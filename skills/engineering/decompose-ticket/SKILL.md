---
name: decompose-ticket
description: Split a ticket too big for one implementation pass into a walking skeleton, one subtask per seam or entry point, and an integration task — a Subtasks section an orchestrator dispatches in dependency order. Tickets that fit pass through untouched.
disable-model-invocation: true
---

# Decompose Ticket

Input: one ticket that states its outcome. Output: either "implement as-is", or the same ticket extended with a `## Subtasks` section: a walking skeleton, one subtask per seam or entry point, an integration task, and the dispatch rules an orchestrator runs them by. The ticket is the plan — subtasks live in it, not in new tickets.

## Process

### 1. Outcome, seams, and entry points

Write the ticket's outcome in one line: what proves the ticket done. For a feature, the user-visible behaviour; for a refactor, the preserved behaviour plus the changed structure. A ticket with no outcome is not ready — report it back.

Attribute every file and module the ticket touches to exactly one **seam**: a design decision hidden behind an interface, so its behaviour can be substituted without editing in place. Name each seam for the decision it hides ("how job state is persisted"), not for a runtime layer: layers recur in every ticket, secrets do not.

Attribute every **entry point** — a thing a verifier runs: a command, a flag, a route — to the seam it enters.

**Done when:** the outcome line exists, every touched file sits under exactly one seam, and every entry point is listed under its seam.

### 2. Pass through or split

**Pass through** when the ticket has one seam and one entry point — one check proves the ticket done: implement it as one unit, with no Subtasks section.

**Split** when any of these holds:

- more than one seam;
- **more than one entry point**: the seam's surface is several things a verifier runs — a second command, a second flag, a second route — each with its own check;
- holding its seams at once means holding internals you cannot stub past — **thrashing**: re-reading files a piece already covered, every interface dragged back in.

**Done when:** the verdict is written down, with the trigger that fired for a split, and carried into the section's `**Split because:**` line.

### 3. Walking skeleton

First subtask: the **walking skeleton** — the thinnest end-to-end path through every seam, each **stubbed**: canned returns for new behaviour, the old code still answering for a refactor. Nothing is verified yet; the skeleton proves the wiring — request in, response out, through every seam.

It freezes each seam's **contract** — one per entry point where a seam carries several: inputs, outputs, errors, how the entry point is reached. **One stub per entry point**, so entry points fill independently. It owns the value types the entry points share — every subtask reads them, none rewrites them. From here the contracts are frozen: a subtask that cannot satisfy its contract has found a bad cut — stop and report it.

**Done when:** the end-to-end check passes against the stubs, every stub has a written contract, and the shared value types are landed.

### 4. One subtask per seam or entry point

Each subtask thickens one seam — or one entry point of one seam: its stub becomes real logic behind the frozen contract. It reads only its own entry point, that contract, and the value types the entry points share — the working set stays small, and it never edits another entry point's code. Give it a **blocked-by edge** to the skeleton, and to any subtask whose contract it consumes.

Two subtasks with no edge between them never want the same region. Where one file must carry two entry points, each subtask's **Owns** names the regions it may edit — disjoint regions, so the merges are textual and clean; where a region serves no entry point, the skeleton owns it.

Each subtask is:

- **Independent:** implementable without another seam's internals; the frozen contract is its entire interface.
- **Valuable:** the end-to-end check passes with this entry point alone thickened.
- **Small:** one implementation pass, proven by one check; two checks, two subtasks.

**Done when:** every stub has exactly one subtask spec carrying its contract and its verification, and any two subtasks with no edge between them claim no file or region in common — the property that lets the **frontier** (subtasks whose blockers have landed) run in parallel.

### 5. Integration

Map-Reduce: each subtask lands its own seam or entry point; the integration task combines them, sweeps up what no entry point owns, and re-runs the skeleton's end-to-end check. Work the skeleton alone unblocks — install, docs — is its own subtask, free to run beside the rest. The integration task blocks on every subtask; its check is the ticket's original acceptance criteria alongside the end-to-end check.

**Done when:** every subtask is landed, no stub remains (refactor: no delegation to the old code), and the check passes alongside the ticket's original acceptance criteria.

### 6. Recurse or stop

A subtask that still fails step 2 decomposes further in place: re-enter at step 1 on that seam or entry point and nest its skeleton, subtasks, and integration under it — `03.1`, `03.2`, and so on.

**Stop and report** when no substitutable boundary exists inside the offending area — a refused split is legitimate; invented micro-cuts are not.

**Done when:** every subtask passes step 2, or the refused seam is reported as blocked.

## Writing the Subtasks section

Append to the ticket, below its own text, numbering subtasks in dependency order — the skeleton first, integration last. Keep the field names verbatim; an orchestrator reads them.

<subtasks-section-template>

## Subtasks

**Split because:** <the trigger that fired — more than one seam, more than one entry point, or thrashing>.
**Workspace:** before the first dispatch, create a worktree on branch `feature/<slug>` — the feature workspace. Every subtask lands there: a subtask running beside another gets a worktree of its own, branched off the feature branch tip, merged back on landing.
**Dispatch:** one subagent per frontier subtask, implemented with the implement skill; a subtask lands only with its check green, before its dependents dispatch.
**Pass to the subagent:** these rules, its spec below, the workspace path and branch, the claims of the lanes it runs beside on any shared file, pointers to what already landed that its spec consumes (paths, entry points, signatures — pointers, not diffs), and the end-to-end check. Waves, merges, and gates stay with the orchestrator.
**Report up:** status, files landed, the check's command and its output — diffs stay in the worktree. A subtask that cannot satisfy its contract, or that merges outside its declared regions, stops and reports instead of amending it.

### 01 — <title>

**Owns:** the files it may edit, and the regions inside any file it shares — one seam, or one entry point inside it; nothing else.
**Contract:** the frozen contract of its entry point, from the skeleton's spec.
**Verification:** the check that proves it — its own check plus the skeleton's end-to-end check; the integration spec names the ticket's acceptance criteria.
**Blocked by:** the skeleton, or a subtask whose contract it consumes.

</subtasks-section-template>

That section is the orchestrator's whole state: the plan it dispatches from, one bounded report per lane, and each check's output. Code-level review already runs inside every lane, and the acceptance walk belongs to the integration subtask.
