---
name: decompose-ticket
description: Decompose a ticket too big for one implementation pass into a walking skeleton, one subtask per seam, and an integration task; tickets that fit pass through untouched.
---

# Decompose Ticket

Input: one ticket that states its outcome. Output: either "implement as-is", or specs for a walking skeleton, one subtask per seam, and an integration task — the agent running this skill turns them into tickets.

## Process

### 1. Outcome and seams

Write the ticket's outcome in one line: what proves the ticket done. For a feature, the user-visible behaviour; for a refactor, the preserved behaviour plus the changed structure. A ticket with no outcome is not ready — report it back.

Attribute every file and module the ticket touches to exactly one **seam**: a design decision hidden behind an interface, so its behaviour can be substituted without editing in place. Name each seam for the decision it hides ("how job state is persisted"), not for a runtime layer: layers recur in every ticket, secrets do not.

**Done when:** the outcome line exists, and every touched file sits under exactly one seam.

### 2. Pass through or split

**Pass through** when the ticket has one seam and one verifiable outcome — no subtasks; implement it as one unit.

**Split** when any of these holds:

- more than one seam;
- no single outcome proves the ticket: two results must both land, neither sufficient alone;
- holding its seams at once means holding internals you cannot stub past — **thrashing**: re-reading files a piece already covered, every interface dragged back in.

**Done when:** the verdict is written down, with the trigger that fired for a split.

### 3. Walking skeleton

First subtask: the **walking skeleton** — the thinnest end-to-end path through every seam, each **stubbed**: canned returns for new behaviour, the old code still answering for a refactor. Nothing is verified yet; the skeleton proves the wiring — request in, response out, through every seam.

It freezes each seam's **contract**: inputs, outputs, errors, how the seam is reached. From here the contracts are frozen: a subtask that cannot satisfy its contract has found a bad cut — stop and report it.

**Done when:** the end-to-end check passes against the stubs, and every seam has a written contract.

### 4. One subtask per seam

Each subtask thickens one seam: its stub becomes real logic behind the frozen contract. It reads only its seam's files and that contract — the working set stays small.

Each subtask is:

- **Independent:** implementable without another seam's internals; the frozen contract is its entire interface.
- **Valuable:** the end-to-end check passes with this seam alone thickened.
- **Small:** one implementation pass.

**Done when:** every seam has exactly one subtask spec carrying its contract and its verification.

### 5. Integration

Map-Reduce: each subtask lands its own seam; the integration task combines them into the feature and re-runs the skeleton's end-to-end check. Blocked by every seam, verified by the ticket's check.

**Done when:** every seam is thickened, no stub remains (refactor: no delegation to the old code), and the check passes alongside the ticket's original acceptance criteria.

### 6. Recurse or stop

A subtask that still fails step 2 is its own ticket: re-enter at step 1 on that seam.

**Stop and report** when no substitutable boundary exists inside the offending area — a refused split is legitimate; invented micro-cuts are not.

**Done when:** every subtask passes step 2, or the refused seam is reported as blocked.

## Subtask specs

One spec per subtask:

- **Owns:** the files and modules it may edit — one seam's surface.
- **Contract:** what it must satisfy; the skeleton's spec lists a contract for every seam.
- **Verification:** the check that proves it — a seam subtask names its own check plus the skeleton's end-to-end check.
- **Blocked by:** the skeleton, or a seam whose contract it consumes.
