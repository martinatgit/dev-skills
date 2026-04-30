#!/usr/bin/env python3
"""Generate operational specialist reasoning agent prompts from taxonomy JSON.

Dev-time tool. Run from anywhere; writes prompts into ../agents/families/
relative to this script. Stdlib only.

Reads the reasoning taxonomy and produces one markdown file per specialist
family. Skips meta-reasoning categories (those belong to the orchestrator).

Usage:
    python3 scripts/_generate_specialists.py [--taxonomy <path>]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = SKILL_DIR / "agents" / "families"

META_IDS = {"meta_reasoning_expanded", "meta_reasoning"}


def _strip_use_this_when(text: str) -> str:
    return re.sub(r"^[Uu]se this when\s+", "", text).strip()


def _lowercase_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def build_applicability_section(cat: dict) -> str:
    family_name = cat["name"]
    trigger = cat["diagnostic_trigger"]
    lines = [
        "## Applicability test\n",
        "**Apply when** the task involves:",
        f"- {trigger}",
        f"- The core question would be answered differently by applying "
        f"{family_name} than by general reasoning alone",
        f"- Specific structural elements of {family_name} "
        f"(listed in modes below) are present in the task",
        "",
        "**Do NOT apply when:**",
        f"- The task merely mentions a keyword related to {family_name} "
        f"but the core question is in another domain",
        "- Your reasoning would duplicate what a more directly relevant "
        "family already covers",
        "- Applying your modes would not change the answer or surface "
        "a novel insight",
        "",
        "**Material relevance test:** This family adds value only if the task "
        "contains structural elements that map to at least one of your reasoning "
        "modes' decision rules below. Surface-level keyword matches do not count "
        "— check whether the mode's diagnostic checklist would find real evidence "
        "in the task.",
    ]
    return "\n".join(lines)


def build_mode_section(mode: dict) -> str:
    name = mode["name"]
    primary_q = mode.get("primaryQuestion", "")
    best_fit = mode.get("bestFit", "")
    main_risk = mode.get("mainRisk", "")
    diag_desc = mode.get("diagnostic_description", "")
    concepts = mode.get("semantic_concepts", [])
    relationships = mode.get("semantic_relationships", [])

    condition = _strip_use_this_when(diag_desc).rstrip(".")
    first_concept = concepts[0] if concepts else "element"
    best_fit_lower = _lowercase_first(best_fit).rstrip(".")
    primary_q_bare = primary_q.rstrip("?")

    lines = [f"### {name}",
             f"**Primary question:** {primary_q}",
             f"**Decision rule:** USE when {condition}. "
             f"SKIP when the task does not contain identifiable {first_concept} "
             f"that this mode would analyse, or when another mode already covers "
             f"this ground. This mode changes the outcome when {best_fit_lower}.",
             "**Diagnostic checklist:**",
             f"- Is this the core question: {primary_q_bare}?",
             f"- Does the task match: {best_fit}?"]
    for concept in concepts[:3]:
        lines.append(f"- Can you identify a specific '{concept}' in the task?")

    lines.append("**Common pitfalls:**")
    lines.append(
        f"- {main_risk}: detect by checking whether your inference is grounded "
        f"in task evidence rather than plausible narrative. Mitigate by naming "
        f"the specific observation that supports your conclusion."
    )
    risk_lower = main_risk.lower()
    if "correlation" in risk_lower or "confus" in risk_lower:
        lines.append(
            "- Confusing correlation with causation: detect by asking whether "
            "an alternative causal path could produce the same evidence. "
            "Mitigate by listing at least one competing explanation."
        )
    if "anchor" in risk_lower or "first" in risk_lower or "prematur" in risk_lower:
        lines.append(
            "- Premature closure: detect by checking whether you stopped "
            "searching after the first plausible answer. Mitigate by generating "
            "at least one alternative before committing."
        )
    if "overfit" in risk_lower or "noise" in risk_lower:
        lines.append(
            "- Overfitting to noise: detect by asking whether the pattern "
            "holds outside the immediate data. Mitigate by testing the "
            "conclusion against a second, independent observation."
        )
    if "rigid" in risk_lower or "brittle" in risk_lower:
        lines.append(
            "- Rigidity under changing conditions: detect by asking whether "
            "a small change in assumptions would invalidate the conclusion. "
            "Mitigate by stress-testing the key assumption."
        )

    concepts_str = ", ".join(concepts) if concepts else "(none)"
    relationships_str = "; ".join(relationships) if relationships else "(none)"
    lines.append(f"**Concepts:** {concepts_str}")
    lines.append(f"**Relationships:** {relationships_str}")
    return "\n".join(lines)


def generate_specialist_file(cat: dict) -> str:
    agent_id = cat["id"]
    family_name = cat["name"]
    description = cat["description"]
    modes = cat.get("reasoning_modes", [])
    n_modes = len(modes)

    parts = [f"# Specialist Agent: {family_name}\n",
             f"You are a specialist reasoning agent for the **{family_name}** family.\n",
             "## Your identity\n",
             f"- **Agent ID:** `{agent_id}`",
             f"- **Reasoning family:** {family_name}",
             f"- **Family description:** {description}\n",
             build_applicability_section(cat),
             "",
             "## Mode selection guide\n",
             f"You have access to {n_modes} reasoning modes. For each, a **decision "
             f"rule** tells you when to USE or SKIP it. Apply ONLY modes whose "
             f"decision rule is satisfied — unused modes should not appear in your "
             f"output.\n"]
    for mode in modes:
        parts.append(build_mode_section(mode))
        parts.append("")
    parts.append("## Task\n")
    parts.append(f"Analyze the following user task through the lens of {family_name}.\n")
    parts.append(
        "Follow the **operating procedure** in the specialist-base contract:\n"
        "1. Determine applicability using the criteria above\n"
        "2. Extract situation structure\n"
        "3. Select relevant modes using the decision rules above\n"
        "4. Build evidence-based inferences using the reasoning template\n"
        "5. Separate observations, interpretations, and uncertainty\n"
        "6. Produce action-relevant conclusions\n"
        "7. Construct the semantic model\n"
    )
    parts.append("Return ONLY valid JSON conforming to the output schema.")
    return "\n".join(parts) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--taxonomy", required=False,
                   help="Path to reasoning_taxonomy.json. "
                        "Defaults to REASON_THROUGH_TAXONOMY env var.")
    args = p.parse_args()

    tax_path = args.taxonomy or os.environ.get("REASON_THROUGH_TAXONOMY")
    if not tax_path:
        print("error: provide --taxonomy <path> or set REASON_THROUGH_TAXONOMY",
              file=sys.stderr)
        return 2
    tax_path = Path(tax_path).expanduser()
    if not tax_path.is_file():
        print(f"error: taxonomy file not found: {tax_path}", file=sys.stderr)
        return 2

    print(f"Reading taxonomy from: {tax_path}")
    with tax_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[tuple[str, str, int]] = []
    for cat in data["categories"]:
        if cat["id"] in META_IDS:
            continue
        content = generate_specialist_file(cat)
        filepath = OUTPUT_DIR / f"{cat['id']}.md"
        filepath.write_text(content, encoding="utf-8")
        generated.append((cat["id"], cat["name"], len(cat["reasoning_modes"])))

    print(f"\nGenerated {len(generated)} specialist agent prompts:")
    for agent_id, name, mode_count in generated:
        print(f"  {agent_id}.md — {name} ({mode_count} modes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
