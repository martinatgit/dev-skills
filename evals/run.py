#!/usr/bin/env python3
"""
Minimal eval runner skeleton.

Extend this to shell out to each target agent and compare outputs against
fixtures. This stub validates repo structure and prints a summary so that
`python3 evals/run.py` is always a safe first check.

Usage:
    python3 evals/run.py [--skill <skill-name>]
"""

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"


def check_frontmatter(skill_md: Path) -> list[str]:
    """Return a list of problems with a SKILL.md's frontmatter."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return [f"{skill_md}: missing opening --- frontmatter delimiter"]

    end = text.find("\n---\n", 4)
    if end == -1:
        return [f"{skill_md}: missing closing --- frontmatter delimiter"]

    frontmatter = text[4:end]
    problems: list[str] = []

    if not re.search(r"^name:\s*\S", frontmatter, re.MULTILINE):
        problems.append(f"{skill_md}: frontmatter missing 'name'")
    if not re.search(r"^description:\s*\S", frontmatter, re.MULTILINE):
        problems.append(f"{skill_md}: frontmatter missing 'description'")

    allowed = {"name", "description"}
    for line in frontmatter.splitlines():
        m = re.match(r"^([a-zA-Z_][\w-]*):", line)
        if m and m.group(1) not in allowed:
            problems.append(
                f"{skill_md}: frontmatter contains non-spec key '{m.group(1)}' "
                f"(spec allows only: {', '.join(sorted(allowed))})"
            )
    return problems


def check_marketplace() -> list[str]:
    if not MARKETPLACE.exists():
        return [f"{MARKETPLACE}: missing"]
    try:
        json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{MARKETPLACE}: invalid JSON ({e})"]
    return []


def _readme_registered_skills() -> set[str]:
    """Skill names linked from the README skills table."""
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        return set()
    text = readme.read_text(encoding="utf-8")
    return set(re.findall(r"\]\(skills/([^/)]+)/SKILL\.md\)", text))


def _marketplace_registered_skills() -> set[str]:
    """Skill names listed in every plugins[].skills array."""
    if not MARKETPLACE.exists():
        return set()
    try:
        data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()  # check_marketplace() reports the parse error separately.
    names: set[str] = set()
    for plugin in data.get("plugins", []):
        for entry in plugin.get("skills", []):
            names.add(Path(entry).name)
    return names


def check_registration() -> list[str]:
    """Every skills/<name>/ must appear in BOTH the README table and marketplace.

    Without this, `/plugin install` (marketplace) and `npx skills add` (whole
    tree) ship different skill sets. There is deliberately no exemption list:
    an unregistered skill is always a bug, never a decision.
    """
    on_disk = {p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md")}
    problems: list[str] = []

    for name in sorted(on_disk - _marketplace_registered_skills()):
        problems.append(
            f"skills/{name}: not listed in {MARKETPLACE.relative_to(REPO_ROOT)} "
            f"(plugins[].skills) — /plugin install will not ship it"
        )
    for name in sorted(on_disk - _readme_registered_skills()):
        problems.append(
            f"skills/{name}: not linked from the README skills table"
        )
    for name in sorted(_marketplace_registered_skills() - on_disk):
        problems.append(
            f"{MARKETPLACE.relative_to(REPO_ROOT)}: lists './skills/{name}' "
            f"but no such skill directory exists"
        )
    return problems


def check_no_placeholders() -> list[str]:
    """Reject {{...}} placeholders in user-facing surfaces only.

    The rule's intent is that contributors must not ship unfilled template
    placeholders inside SKILL.md or `references/`. Runtime artefacts
    (`agents/`, `actions/`, `resources/`, `scripts/`) are filled by the
    skill at runtime and legitimately contain placeholder markers; the
    repo-root `template/` is also exempt.
    """
    problems: list[str] = []
    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        targets = [skill_md]
        ref_dir = skill_md.parent / "references"
        if ref_dir.is_dir():
            targets.extend(p for p in ref_dir.rglob("*.md") if p.is_file())
        for path in targets:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            if "{{" in text and "}}" in text:
                problems.append(
                    f"{path}: contains unfilled placeholder {{{{...}}}}"
                )
    return problems


def check_python_scripts() -> list[str]:
    """Compile every *.py under skills/<name>/scripts/ to catch syntax errors."""
    import py_compile
    problems: list[str] = []
    for skill_dir in sorted(SKILLS_DIR.glob("*/scripts")):
        for py_file in sorted(skill_dir.glob("*.py")):
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                problems.append(f"{py_file}: {e.msg.strip()}")
    return problems


# Scripts stamped identically into every skill that ships them. Drift here is
# always a bug: these files carry cross-skill invariants (project-root
# detection, shared-conventions parsing) that must not vary per skill.
STAMPED_SCRIPTS = (
    "read_shared_conventions.py",
    "find_project_root.py",
)


def check_stamped_script_drift() -> list[str]:
    """Byte-compare each skill's stamped scripts against the canonical template.

    Comparison is newline-insensitive: `.gitattributes` pins these files to LF,
    but a checkout with core.autocrlf=true will materialise CRLF locally and
    that is not drift.
    """
    problems: list[str] = []
    for filename in STAMPED_SCRIPTS:
        template = REPO_ROOT / "template" / "scripts" / filename
        if not template.exists():
            continue  # Template absent; refresher hasn't been introduced.
        canonical = template.read_bytes().replace(b"\r\n", b"\n")
        for copy in sorted(SKILLS_DIR.glob("*/scripts/" + filename)):
            if copy.read_bytes().replace(b"\r\n", b"\n") != canonical:
                problems.append(
                    "%s: differs from canonical template at %s "
                    "(run: python3 scripts/refresh-shared-reader.py)"
                    % (copy.relative_to(REPO_ROOT),
                       template.relative_to(REPO_ROOT))
                )
    return problems


def check_agent_skill_pairing() -> list[str]:
    """Each agents/<name>-agent.md must pair with a skill.

    Naming rule: agent name '<name>-agent' implies a skill 'skills/<name>/'.
    """
    problems: list[str] = []
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.is_dir():
        return problems
    for md in sorted(agents_dir.glob("*-agent.md")):
        stem = md.stem  # e.g. 'improve-prompt-agent'
        if not stem.endswith("-agent"):
            continue
        skill_name = stem[:-len("-agent")]
        skill_dir = SKILLS_DIR / skill_name
        if not skill_dir.is_dir():
            problems.append(
                f"{md}: paired skill 'skills/{skill_name}/' not found"
            )
    return problems


def _load_generator():
    """Import scripts/generate-codex-agents.py as a module.

    The filename has a hyphen, so it cannot be imported with a normal
    `import` statement; load it from its file path instead. This makes
    check_agent_format_parity() assert the actual contract — "the .toml is
    what the generator would produce from the .md" — rather than reimplementing
    (and inevitably drifting from) the generator's parsing logic.
    """
    import importlib.util

    gen_path = REPO_ROOT / "scripts" / "generate-codex-agents.py"
    spec = importlib.util.spec_from_file_location("generate_codex_agents", gen_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def check_agent_format_parity() -> list[str]:
    """Each agents/<name>.md must have a .toml sibling that is byte-identical
    (newline-normalised) to what scripts/generate-codex-agents.py would
    produce from that .md right now.

    This is deliberately stronger than comparing individual fields: a
    hand-edited or stale .toml fails even if the fields anyone thought to
    check (like 'name') still happen to match. Regenerating in memory and
    diffing catches every generator bug that changes output (chomped
    description indicators, dropped list items, a leaked Claude model tier)
    without needing a bespoke assertion per bug.
    """
    problems: list[str] = []
    agents_dir = REPO_ROOT / "agents"
    if not agents_dir.is_dir():
        return problems

    try:
        generator = _load_generator()
    except Exception as e:
        return [f"cannot load scripts/generate-codex-agents.py: {e}"]

    import tomllib

    for md in sorted(agents_dir.glob("*.md")):
        if md.name == "README.md":
            continue
        toml_path = md.with_suffix(".toml")
        if not toml_path.exists():
            problems.append(f"{md}: missing TOML sibling at {toml_path.name}")
            continue

        md_text = md.read_text(encoding="utf-8")
        try:
            fm, body = generator.parse_frontmatter(md_text)
            expected_toml = generator.emit_toml(fm, body)
        except ValueError as e:
            problems.append(f"{md}: cannot parse frontmatter ({e})")
            continue

        try:
            with open(toml_path, "rb") as f:
                tomllib.load(f)
        except Exception as e:
            problems.append(f"{toml_path}: cannot parse TOML ({e})")
            continue

        actual_toml = toml_path.read_text(encoding="utf-8")
        if expected_toml.replace("\r\n", "\n") != actual_toml.replace("\r\n", "\n"):
            problems.append(
                f"{toml_path.name}: does not match the output of "
                f"scripts/generate-codex-agents.py for {md.name} — "
                f"regenerate with: python3 scripts/generate-codex-agents.py"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", help="Check one skill only (by folder name)")
    args = parser.parse_args()

    all_problems: list[str] = []

    if args.skill:
        skill_md = SKILLS_DIR / args.skill / "SKILL.md"
        if not skill_md.exists():
            print(f"error: no such skill: {args.skill}", file=sys.stderr)
            return 2
        targets = [skill_md]
    else:
        targets = sorted(SKILLS_DIR.glob("*/SKILL.md"))
        all_problems.extend(check_marketplace())
        all_problems.extend(check_registration())
        all_problems.extend(check_no_placeholders())
        all_problems.extend(check_python_scripts())
        all_problems.extend(check_stamped_script_drift())
        all_problems.extend(check_agent_skill_pairing())
        all_problems.extend(check_agent_format_parity())

    for skill_md in targets:
        all_problems.extend(check_frontmatter(skill_md))

    if all_problems:
        print(f"FAIL — {len(all_problems)} problem(s):")
        for p in all_problems:
            print(f"  - {p}")
        return 1

    print(f"OK — checked {len(targets)} skill(s).")
    print()
    print("This runner only validates structure. For real evals:")
    print("  1. Add test prompts under evals/fixtures/<skill-name>/prompts.json")
    print("  2. Extend run.py to invoke each target agent and compare outputs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
