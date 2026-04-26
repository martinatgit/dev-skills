#!/usr/bin/env python3
"""Generate v3 operational specialist reasoning agent prompts from taxonomy JSON.

Reads the reasoning taxonomy and produces one markdown file per specialist family
in the v3 operational format. Each file contains decision rules, diagnostic
checklists, and pitfall warnings derived from the taxonomy's mode metadata.

Skips the two meta-reasoning categories (meta_reasoning_expanded, meta_reasoning)
since those belong to the orchestrator, not specialist agents.
"""
import json
import os
import re
import sys

# Resolve paths relative to the repository root (two levels up from this script's
# directory: agents/ -> reason-through/ -> skills/ -> .claude/ -> repo root).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

# Try the canonical path first, fall back to the archive location.
TAXONOMY_CANDIDATES = [
    os.path.join(REPO_ROOT, "doc", "research-insights", "reasoning", "reasoning_taxonomy.json"),
    os.path.join(REPO_ROOT, "tmp", "archive", "research", "reasoning", "reasoning_taxonomy.json"),
]
OUTPUT_DIR = os.path.join(REPO_ROOT, ".claude", "skills", "reason-through", "agents", "families")

META_IDS = {"meta_reasoning_expanded", "meta_reasoning"}


def _find_taxonomy():
    """Locate the taxonomy JSON, trying canonical then fallback paths."""
    for path in TAXONOMY_CANDIDATES:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(
        f"Taxonomy JSON not found at any of: {TAXONOMY_CANDIDATES}"
    )


def _strip_use_this_when(text: str) -> str:
    """Strip leading 'Use this when' (case-insensitive) from diagnostic_description."""
    return re.sub(r"^[Uu]se this when\s+", "", text).strip()


def _lowercase_first(text: str) -> str:
    """Lowercase the first character of a string, preserving the rest."""
    if not text:
        return text
    return text[0].lower() + text[1:]


def build_applicability_section(cat: dict) -> str:
    """Build the ## Applicability test section for a category."""
    family_name = cat["name"]
    trigger = cat["diagnostic_trigger"]

    lines = []
    lines.append("## Applicability test\n")
    lines.append("**Apply when** the task involves:")
    lines.append(f"- {trigger}")
    lines.append(
        f"- The core question would be answered differently by applying "
        f"{family_name} than by general reasoning alone"
    )
    lines.append(
        f"- Specific structural elements of {family_name} "
        f"(listed in modes below) are present in the task"
    )
    lines.append("")
    lines.append("**Do NOT apply when:**")
    lines.append(
        f"- The task merely mentions a keyword related to {family_name} "
        f"but the core question is in another domain"
    )
    lines.append(
        "- Your reasoning would duplicate what a more directly relevant "
        "family already covers"
    )
    lines.append(
        "- Applying your modes would not change the answer or surface "
        "a novel insight"
    )
    lines.append("")
    lines.append(
        "**Material relevance test:** This family adds value only if the task "
        "contains structural elements that map to at least one of your reasoning "
        "modes' decision rules below. Surface-level keyword matches do not count "
        "— check whether the mode's diagnostic checklist would find real evidence "
        "in the task."
    )
    return "\n".join(lines)


def build_mode_section(mode: dict) -> str:
    """Build one ### Mode section with decision rule, checklist, and pitfalls."""
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

    lines = []
    lines.append(f"### {name}")

    # Primary question
    lines.append(f"**Primary question:** {primary_q}")

    # Decision rule
    lines.append(
        f"**Decision rule:** USE when {condition}. "
        f"SKIP when the task does not contain identifiable {first_concept} "
        f"that this mode would analyse, or when another mode already covers "
        f"this ground. This mode changes the outcome when {best_fit_lower}."
    )

    # Diagnostic checklist (3-5 items)
    lines.append("**Diagnostic checklist:**")
    lines.append(f"- Is this the core question: {primary_q_bare}?")
    lines.append(f"- Does the task match: {best_fit}?")
    for concept in concepts[:3]:
        lines.append(f"- Can you identify a specific '{concept}' in the task?")

    # Pitfalls
    lines.append("**Common pitfalls:**")
    # Always include mainRisk as the first pitfall
    lines.append(
        f"- {main_risk}: detect by checking whether your inference is grounded "
        f"in task evidence rather than plausible narrative. Mitigate by naming "
        f"the specific observation that supports your conclusion."
    )
    # Contextual extra pitfalls based on mainRisk keywords
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

    # Concepts and relationships
    concepts_str = ", ".join(concepts) if concepts else "(none)"
    relationships_str = "; ".join(relationships) if relationships else "(none)"
    lines.append(f"**Concepts:** {concepts_str}")
    lines.append(f"**Relationships:** {relationships_str}")

    return "\n".join(lines)


def generate_specialist_file(cat: dict) -> str:
    """Generate the full markdown content for one specialist agent family."""
    agent_id = cat["id"]
    family_name = cat["name"]
    description = cat["description"]
    modes = cat.get("reasoning_modes", [])
    n_modes = len(modes)

    parts = []

    # Header
    parts.append(f"# Specialist Agent: {family_name}\n")
    parts.append(f"You are a specialist reasoning agent for the **{family_name}** family.\n")

    # Identity
    parts.append("## Your identity\n")
    parts.append(f"- **Agent ID:** `{agent_id}`")
    parts.append(f"- **Reasoning family:** {family_name}")
    parts.append(f"- **Family description:** {description}\n")

    # Applicability
    parts.append(build_applicability_section(cat))
    parts.append("")

    # Mode selection guide
    parts.append("## Mode selection guide\n")
    parts.append(
        f"You have access to {n_modes} reasoning modes. For each, a **decision "
        f"rule** tells you when to USE or SKIP it. Apply ONLY modes whose "
        f"decision rule is satisfied — unused modes should not appear in your "
        f"output.\n"
    )

    for mode in modes:
        parts.append(build_mode_section(mode))
        parts.append("")

    # Task section
    parts.append(f"## Task\n")
    parts.append(
        f"Analyze the following user task through the lens of {family_name}.\n"
    )
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


def main():
    taxonomy_path = _find_taxonomy()
    print(f"Reading taxonomy from: {taxonomy_path}")

    with open(taxonomy_path, "r") as f:
        data = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    generated = []
    for cat in data["categories"]:
        if cat["id"] in META_IDS:
            continue
        content = generate_specialist_file(cat)
        filepath = os.path.join(OUTPUT_DIR, f"{cat['id']}.md")
        with open(filepath, "w") as f:
            f.write(content)
        generated.append((cat["id"], cat["name"], len(cat["reasoning_modes"])))

    print(f"\nGenerated {len(generated)} specialist agent prompts (v3 operational format):")
    for agent_id, name, mode_count in generated:
        print(f"  {agent_id}.md — {name} ({mode_count} modes)")


if __name__ == "__main__":
    main()
