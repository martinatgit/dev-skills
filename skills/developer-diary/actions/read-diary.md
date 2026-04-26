

# Read relevant information from the developer diary
Use this procedure when reading information from the developer-diary. 


## Structure of the developer-diary
The developer diary is organised in a hierarchical tree. Each tree node is stored in a markdown file. The root node has a high-level of abstraction while details are deeper in tree as appropriate. The root node is stored in `doc/developer-diary/developer-diary.md`. The tree structure is intentional to selectively and exclusively select the content that is relevant for a task at hand. Only read relevant nodes. Avoid polluting your context and attention with irrelevant nodes. 

## 1. Clarify the task you are preparing for

Before reading any diary nodes, create a short task understanding for yourself:
- explicitly mentioned node indices 
- one-sentence task summary,
- 3 to 8 keywords,
- relevant component names, requirement IDs, feature names, file names, or design concerns.

This task understanding is your relevance filter for selecting diary nodes.


## 2. Start at the root

The root node is always:
`doc/developer-diary/developer-diary.md`
Always read the root first.

Then read the file `doc/developer-diary/feature-routing.md`

Create an in-memory list named `selected_nodes`. Add the root node to it first.

Each entry in `selected_nodes` should track:
- Index
- Title
- File name
- Why it is relevant

Add relevant references from the feature-routing.md table to the in-memory list. 

## 3. Traverse selectively

At each node:

1. Read the current node fully. Pay special attention to these high-value sections:
   - **Notes and commentary** (especially Decision journal, Session context, Uncertainties) — contains the context that enables continuation
   - **Problems encountered** — reveals what the previous engineer struggled with and how they resolved it
   - **Special instructions for next reader** — urgent handoff items
   - **Design decisions made** — the reasoning behind choices (look for alternatives considered)
2. Find the `Child nodes` table.
3. Evaluate each child using only:
   - the child index,
   - file name,
   - description,
   - and the current task understanding.
4. Select only the children that are meaningfully relevant based on topic closeness to the task understanding.

Selection rule:
- Prefer a narrow path from the root to the most relevant leaf.
- Select multiple branches only when the task truly spans multiple architectural concerns.
- Avoid speculative reading.

**Staleness check:** After reading each node, compare its `Last updated` date with its children. If a parent node's `Last updated` is older than a child that records completed work in `Progress made`, the parent's `Outstanding items` and `Next steps` sections may be stale — they could list items the child has already completed. Flag this in the `Known risks or ambiguities` section of the output. Also check: if `Outstanding items` contains items marked as completed (`[x]`), the node needs a cleanup update.

**Special instructions expiry:** After reading a node's `Special instructions for next reader`, check if the instructions reference work that appears completed in `Progress made` or a child node. If so, note it as stale in `Known risks or ambiguities`. Stale special instructions mislead new engineers into thinking urgent action is needed when the work is already done.

For each selected child:
- add it to `selected_nodes`,
- open the child file,
- repeat the same process.

Stop when there are no more relevant unexplored children.


## 4. Read related nodes only when necessary

Use the `Relevant related diary nodes` table only when one of these is true:
- the current task explicitly spans the linked concern,
- the current node says the linked node is required context,
- or the main branch leaves an obvious gap that blocks understanding.

Do not fan out across related nodes casually.


## 5. Produce an aggregated task context

After reading the selected nodes, produce an internal working summary with this structure:

```md
### Aggregated context
A concise but comprehensive summary of the relevant engineering context (including design goals, requirements, implementation details, etc.)

### Previous engineer's mental model
Reconstruct the thinking of the engineer(s) who wrote the diary entries:
- What were they confident about vs. uncertain about? (Check "Notes and commentary > Uncertainties and risks")
- What decisions did they make and why? (Check "Notes and commentary > Decision journal" and "Design decisions made")
- What did they struggle with? (Check "Problems encountered" — sparse entries here signal missing context)
- What were they about to do next? (Check "Special instructions for next reader" and "Next steps")
- What did they reference during their work? (Check "Notes and commentary > Session context" for specs, files, and tests)

### Areas needing extra care
Flag anything where the previous engineer expressed uncertainty, took shortcuts, or noted fragility.
These are areas where you should proceed carefully, verify assumptions, and potentially re-examine decisions.

### Known risks or ambiguities
A bullet list of unresolved questions, conflicting notes, stale references, or places where the diary may be incomplete.

### What is ready
A summary of the items that are ready and working

### Open issues
A list of next steps and action items that are pending execution
```

## 6. Escalate if inconsistency discovered

If you encounter a concrete inconsistency that blocks normal reading, such as:
- missing referenced files,
- malformed tables that prevent routing,
- broken indexes,
- or obvious stale references that make the tree misleading,

then switch to `review` mode only for the affected scope.











