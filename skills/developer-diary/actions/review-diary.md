
# Review and maintain the developer diary

The following are a list of quality concerns to look for and repair to maintain a high quality developer diary.

## Identify and resolve duplication and ambiguities
Make sure there is no significant duplication or ambiguity within the diary tree. You verify this as follows: 
 - Collect all leave nodes of the tree, i.e. all nodes that have no child nodes, in a list. Do this with a breadth-first search, start from the root `doc/developer-diary/developer-diary.md` and iterate over children until all leave nodes are found. 
 - For each item in the list memorise its index and synthesise a short description and bullet point list of key words of topics that are representative of the node. This mimics formulating a search while reading the developer hierarchy. Then search for that information and validate that you find the node from which the information have been created (same index). If a different node is found add cross references to both nodes and describe how they are related. 

## Listed diary-entry files must exist
 - Make sure that all referenced `diary-entry.md` files exist. Their correct relative path (starting from `doc`) directory should exist in the sections "Child nodes" and "Relevant related diary nodes". If a file is missing, remove the entry from the reference list.



  
## Parent-child content deduplication

For each parent node that has children, compare the parent's `Progress made` and `Outstanding items` sections against its children:

- **Flag as duplication:** Items in the parent that belong entirely to one child (not a cross-cutting summary). Example: if the parent lists "PropagatorEngine implemented with fixpoint loop" and child R.1.10 covers Layer 4.5 Deep Solvers exclusively, that item belongs in the child, not the parent. The parent should say "Layer 4.5 Deep Solvers implemented (see R.1.10)" instead.

- **Acceptable summarization:** Items in the parent that aggregate across multiple children. Example: "Layers 0, 2, 2.5, 3, 4, 4.5 implemented with 451 tests" is a valid cross-cutting summary even though each layer has its own child node.

- **Rule of thumb:** If you can point to exactly one child that owns the detail, the detail should be in the child and the parent should reference it. If the detail spans 2+ children, it belongs in the parent as a summary.

Report duplication instances for the user to resolve. Do not auto-fix — the user decides whether to move content to children or keep it as intentional summary.

## Feature routing regeneration

Regenerate `doc/developer-diary/feature-routing.md` from the full tree:

1. Traverse all nodes (breadth-first from root)
2. For each node, extract identifiable features (packages, modules, components, functions, API surfaces)
3. Produce the feature-routing table with columns: Feature name, Index, Description
4. Include implementation status where known (e.g., "implemented, 26 tests" or "specified, not implemented")
5. Sort by Index (R.1.1 before R.1.2, etc.)

This ensures feature-routing is comprehensive and consistent with the actual tree, rather than incrementally patched during updates.

## Content quality audit

For each leaf node (nodes with no children), check for these quality problems:

- **Empty "Notes and commentary":** Flag as a quality gap. This is the most important section — it should contain decision journal, session context, and uncertainties at minimum.
- **"No problems encountered" or empty "Problems encountered":** Flag as suspicious unless the node describes trivially simple work. Most non-trivial implementation involves some debugging.
- **Design decisions without reasoning:** Check that each decision in "Design decisions made" includes at least one alternative considered and a rationale. Bare statements like "Chose X" without "over Y because Z" are quality gaps.
- **Progress entries without context:** "Implemented X" without why or how is a quality gap. Look for entries that would require reading all source files to understand.
- **Empty or bare "Next steps":** Items like "implement Y" without priority, dependencies, or complexity context reduce the value for the next engineer.

Report quality gaps to the user. Do not auto-fix content quality — the engineer who did the work has the context to write rich entries. Flag which nodes need enrichment.

## Peers information must be consistent 
 - Make sure that peers information are mutual and consistent across peers


## Node references must be rendered in markdown list
 - Make sure the that the format of the reference list is valid markdown 
  - Child nodes to be rendered as a markdown list
  ```md
  | Index | File name | Description | 
  | --- | --- | --- | 
  ```

  
## Schema validity  
Each diary-entry.md file (including the developer-diary.md root node) follow precisely the same markdown format described below. Template of a diary node with the required section headings: 
```md
## Index

## Last updated

## Title

## Relevant context

## Design decisions made

## Peers

## Progress made

## Outstanding items

## Problems encountered

## What works well

## Next steps

## Child nodes
 | Index | File name | Description | 
 | --- | --- | --- | 
 

## Relevant related diary nodes
 | Index | File name | Description | 
 | --- | --- | --- | 
 

## Notes and commentary

## Special instructions for next reader

```

### Content in following sections must be present
- At least the following section must have content: 
   - Index
   - Title
   - Relevant context
  
Other sections may be empty when truly not applicable, but the heading must still be present.


### Node content specification
Explanation to diary-entry.md sections: 
 - "Index": A unique identifier of the node (e.g. `R.2.6.3`, which encodes the path from root to current node. "R" is the root node. In this case, start at root, take its second child, from there take the sixth child, and current node is is third child)
 - "Last updated": The date (YYYY-MM-DD) when this node was last modified. Used for staleness detection during read operations. Must be updated on every edit.
 - "Title": A short matching title for the current node
 - "Relevant Context": An introduction and overview at a level of abstraction that is appropriate for the node. As leave node the description, reference to requirements, pseudo code examples, documentation, etc must be sufficiently comprehensive to document current status and enable software developers to take the next step, i.e. executing their task. The nodes only introduce the content that is relevant to their context only. The assumption is that the reader has read and understood the nodes on the direct path from the root node to the current node. 
 - "Design decisions made":  Important design decisions made that other software developers need to be aware of. 
 - "Peers": Information describing what separate this node from peers on the same level. It contains information what is within scope of the current node and what is out of scope but should be covered in peer nodes. The reader can use this information to verify to have selected the correct node or to go back up to the parent node and select a better matching peer node.
 - "Progress made": A summary of the progress made so far.
 - "Outstanding items": A list of items that need to be done to complete a software component, feature or other artefact that the node describes. 
 - "Problems encountered": A list of reminders of problems (including resolutions if present) encountered while designing and implementing the software. 
 - "What works well": A summary of what works and is stable (e.g. proven in use).   
 - "Next steps": The direct next steps that this node needs to be executed. When software engineers go home in the evening, or otherwise clock off, they document next steps here. This list is the set of tasks that are still incomplete and need to be picked up immediately.

 - "Child nodes": 
   A markdown table listing all child nodes. When a node becomes too large, identifiable sub-nodes are documented separately,
   The format of the markdown table is as follows:  
   ```md
    | Index | File name | Description | 
    | --- | --- | --- | 
   ```md

 - "Notes and commentary": General notes and commentary by the software developers to remind themselves or others. 


 - "Relevant related diary nodes"
  A markdown table listing relevant other nodes from the diary including a description of that relationship. 
  The format of the markdown table is as follows:  
   ```md
    | Index | File name | Description | 
    | --- | --- | --- | 
   ```md

 - "Special instructions for next reader": Ephemeral storage of notes and instructions that the reader needs to react on directly and the remove from the node. 

## Diary entry Node file size limit
A node has a size limit. If the content of the node is estimated to be above 4000 tokens, the content should be split into child nodes and only the aggregation and routing should be higher level understanding should be retained on this node. The split should maintain independence and orthogonality between nodes. Avoid duplications and ambiguities. There should always be a clear position in the developer-diary node hierarchy. Identify the single source of truth and when necessary list other related nodes in the "Relevant related diary nodes" section. 

Enforce the size limit by splitting longer content across children. Estimate whether the updated node exceeds the 4000-token guideline.

If yes:
- split the node into child concerns:
    - identify the topics and concerns that are orthogonal and mutually independent that can be split into individual child nodes of the diary(apply software engineering expertise to modularise, decouple and identify separable boundaries (e.g. module, component, class, function, artefact, etc))
    - mentally plan how many children to produce, give each child topic an identifiable type and scope, and what content aggregates and summarises over all children to keep in current node
    - plan minimally necessary cross references between the children (peers)
    - review and verify your plan, adjust if needed
    - create the child_X subdirectories for each planned child (where X is the is ID of the child node)
    - create in each child directory a `diary-entry.md` file with the content of the `resources/diary-entry.md.tpl` and set the correct ID and title content
    -  then for each planned child do the following:
      - populate the content of the child_X/diary-entry.md file with the planned child contents,
      - review that the content is accurate and minimises overlap to other peer children and cross links 
- modify the parent as a concise summary and router, only leave content in the parent that is common across all child diary-entries. 
- Make sure all child nodes are properly referenced with id and matching short description in parent node. 
