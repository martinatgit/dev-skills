# Analysis checklists

Detailed prompts and rubrics for `analyze-design-simplicity`. Each section maps to a
phase or output item in `SKILL.md`. Read the section you need when you reach it.

## Contents

- [Mental-model questions](#mental-model-questions) — phase 2
- [What "simpler" means](#what-simpler-means) — phase 3
- [Component and function inventory](#component-and-function-inventory) — phase 4
- [Conflict detection](#conflict-detection) — phase 4
- [Narrative style](#narrative-style) — phase 5 / output item 4

---

## Mental-model questions

Answer these for yourself to build a precise picture of the design. They are thinking
prompts, not report sections — the answers feed your mental model and your judgment.

**Scope and adjacency**
- What is the scope boundary of the software, and what is adjacent to it?
- What is in scope to be modified? What may be used but not modified? What is
  explicitly out of scope?

**Software components as anthropomorphised stakeholders**
- Identify motivations and concerns
- Examples (tone and style only, not content)
  > As the authorisation module I want to make sure that only users with explicit permissions are accessing protected assets. 
  > As a software component, I don't want to hammer the database or network unnecessarily to keep up performance. 
  > As a parallel executing function, I must be certain that my assumptions hold or are verifiable throughout my execution, i.e. nothing should change underneath me (e.g. avoid time-of-check-time-of-use-race). 
  > As a user, I want to get the information I asked for. I want to be able to specify my query as narrowly as possible. 
  > As a maintainer, I want to be confident that a change will not have undesired side effects.

**Hierarchy and ownership**
- Who owns what? Who drives what? Who instantiates what?
- Which variables and references live at which scope: local, file, component, module,
  process, project?

**Iteration**
- Is there an iteration or loop? If so, what is being iterated over?
- Is the collection data-driven (determined at runtime) or design-driven (fixed before
  compile)?
- If design-driven, has the collection been factored out so the design extends without
  edits in many places?

**Locality and abstraction**
- Are the things that belong together located together?
- Can the special cases be abstracted over?
- Can the implementation be simplified — dropping a variable, function, or class —
  without increasing the mix of concerns or hurting composability?
- Are units loosely coupled and are composable or are they tightly coupled? 
- Are units single concern or multi concern? 

**Data flow**
- What is the life cycle of data? Where is it generated (sourced), processed, stored, deleted? 
- Is there a single source of truth?
- Is derived or computed data cached? How is staleness avoided? 
- Where is data aggregated and managed? 
- What meta data is managed? (e.g. version, date, who modified it, encoding, validation, checksum, etc.)
- Is data properly typed? 
- Are there several formats, encodings, conventions competing for similar data contents? 
- Are data structures mutable or immutable? 
- What state management strategy is applied? 
- Are there special/magic values? 
- How are exceptions and errors communicated and resolved? 
- What mechanisms keep data clean, prevent staleness, fix latent or compounding errors? 
- Consolidate view to have a mental model of the data architecture (from local scoped in memory to long term scaled persistence in databases)

**Parallelisation**
- What parallelisation principles are applied? (e.g. single-threaded singleton with no parallelisation, 
cooperative-yields, threads, multiple-independent processes, multi-computer networking, etc.)
- What synchronisation methods are applied? (mutex, semaphores, message-queues, etc. )
- Is there one-to-one or one-to-many communication?

**Error and failure handling**
Identify what is the general approach to error handling and recovery:
- What error handling is applied and is it consistent (e.g. exceptions, special return values, etc.)?
- Are errors handled locally where possible? What is the error escalation principle? 
- In case of failure, what is the next lower solid base to stand on for recovery?

**The right way to think about the problem**
Identify the framing that best fits. Examples (not a closed list):
- producer/consumer, publisher/subscriber
- asynchronous vs. synchronous execution
- event-based: fire-and-forget vs. wait-for-completion
- class / container / aggregator
- queue / sequence of execution
- numerical algorithm
- relationships: caller/callee, owner/dependent, controller/worker
- extension / plugin
- abstraction / generalization
- a named software pattern (command, visitor, factory, inversion of control,
  dependency injection, …)
- a parameterizable template

---

## What "simpler" means

Simplicity is a technical claim. When you judge the design (phase 3) and when you list
fallacies (output item 9), use these measures. Each is a "prefer A over B" rule;
deviations should be justified.

- **Simple over complicated** — a widely understood construct beats one that takes
  time to learn.
- **Fail as early as possible** — compile-time failure beats runtime failure.
- **Deep vs shallow modules** — deep modules are preferable as they abstract complexity and provide clean interfaces that lend themselves naturally to testing. 
- **Formal enforcement over lax enforcement** — encode constraints, fixed points, and
  assumptions so the compiler or type system enforces them, rather than relying on
  convention.
- **Generality over many special cases** — aim for as few, as broadly applicable rules
  as possible. Every rule should earn its keep and reduce confusion.
- **Explicit over implicit** — stated intent beats hidden assumption.
- **Consolidation and locality over distribution** — related concerns belong together
  in the codebase.
- **Easy to explain** — the implementation strategy should be easy to understand,
  explain, and remember.
- **Pit of success** — the design should naturally force the right thing and
  discourage misuse, confusion, complexity, and hidden error sources.
- **Understandability and maintainability over obscure optimisation.**
- **Extendability over narrow local interpretation.**
- **Configurability and parameterization over hardcoded values.**
- **Isolate necessary complexity behind stable interfaces** — when complexity can't be
  removed, contain it so the rest of the system doesn't have to know about it.

### Design smells to watch for

The rubric above says what to prefer. These are the recurring symptoms that say a
design is drifting the wrong way — treat each as a lead to investigate, not a verdict:

- A component has too many reasons to change.
- A simple concept requires reading many files to understand.
- Adding a new case requires edits in multiple unrelated places.
- Ownership of state or control is unclear.
- Data flows backward through hidden channels.
- Error handling is inconsistent across similar paths.
- State changes are implicit or happen as a side effect of something else.
- Special cases keep multiplying.
- Correctness relies on undocumented sequencing or call order.
- Runtime checks compensate for constraints that a type, schema, or interface could
  enforce instead.
- Naming hides the real responsibility.
- Valid inputs exist for which the behavior is undefined.
- A long-running operation depends on assumptions that can change underneath it.
- The design is optimised for first implementation rather than for maintenance.

---

## Component and function inventory

In phase 4, work through these for every relevant unit. Be concrete and name things.

### For every class / component / module

- What does it encapsulate or abstract?
- What is its scope?
- What does it establish?
- What does it extend? By what is it extended?
- Who allocates it? Who uses it?
- Is there a single instance or multiple?
- What is aggregated vs. merely referenced? Do all references remain valid, or can
  they go out of scope?

### For every function

- **Inputs** — which are mandatory, which optional.
- **Overloads.**
- **Fixed points and constraints.**
- **Calling semantics** — fire-and-forget, async, or sync.
- **Error handling.**
- **Output expectations.**
- **Side effects.** Avoid them where possible. Acceptable side effects modify
  *external* state deliberately — emitting a log/monitoring message, writing to a
  database. Avoid mutating inputs or state allocated outside the function (files,
  globals). Prefer immutable data structures (copy-and-modify) wherever practical.
- **Consistency.** Does it behave consistently with the rest of the project (e.g.
  calling convention)? Check the documented conventions. If none exists, propose one
  in `doc/conventions.md` and ask the user to confirm.
- **Length.** If a function exceeds ~100 lines, list what each section is trying to do
  and propose refactoring it into composable helpers.

---

## Conflict detection

Still in phase 4, and feeding output item 12. Be a devil's advocate. Assume Murphy's
law — what can go wrong, will. Look for:

- **Mutual contradictions** — two parts of the design that cannot both hold.
- **Undefined behavior** — valid input for which it is unclear what should happen.
- **Things that don't make sense** — instructions you've been given that don't add up.
- **Perverse incentives** — does the design reward unintended behavior by engineers,
  maintainers, admins, product owners, or users?
- **Misinterpretation risk** — places where a reasonable reader could draw the wrong
  conclusion.
- **Exploits and races** — security holes, time-of-check/time-of-use races, ordering
  assumptions that may not hold under concurrency or failure.

Reason each item through rather than just listing it: what triggers it, what breaks,
and how bad it is.

---

## Narrative style

The narrative (output item 4) introduces concepts and develops them so a reader builds
the same mental model you have. Rules:

- Use short sentences.
- Keep it logically consistent and representative of the actual design.
- Focus on the essence.
- Communicate a mental model.
- Reference key components and functions, ideally with precise links.
- Introduce the challenges faced.
- Make it easily understandable.

### Example (tone and style only — not content)

> The authorization module is instantiated by the application main as a singleton
> (via the NestJS DI container). It encapsulates three service classes:
> `PermissionService`, `RoleService`, and `AdminService`. The `PermissionService`
> exposes interfaces to manage access rights. Each user carries a list of explicit
> permissions (see `user.schema.ts`). Each feature module registers its document
> types and actions with the authorization module. A user is granted access via
> `permissionService.grantAccess(docType, action)`, and permissions are persisted with
> the user. Whenever the user calls a REST endpoint, the `AuthGuard` checks
> permissions using `permissionService.hasAccess(docType, action)`; the same function
> can confirm access before a background step in a long-running job.
>
> A race condition is possible: the check passes inside a long-running job, but the
> permission is revoked shortly after. Writing results then fails, the error is thrown
> and caught by the job orchestrator, which rolls back incomplete results and reports
> the job as failed. A second challenge is the timing of granting permissions to a
> newly created document. The rule is to grant access immediately on creation, even
> before the document is fully populated, and to fire the `onDelete` event (caught by
> the `PermissionService`) so orphaned permissions are cleaned up.
