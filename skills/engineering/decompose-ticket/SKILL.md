---
name: decompose-ticket
description: Decompose oversized tickets in place; pass through tickets that fit.
disable-model-invocation: true
---

# Decompose Ticket

Input: one ticket stating its outcome. Return "implement as-is" or mark and extend that same ticket using the format below. Subtasks live in it, not in new tickets.

## Process

### 1. Outcome, seams, and entry points

Write a one-line outcome proving completion: user-visible behaviour for a feature; preserved behaviour plus changed structure for a refactor. Missing outcome: report the ticket not ready.

Map every touched file and module to exactly one **seam**: a design decision hidden behind an interface, its behaviour substitutable without in-place edits. Name the hidden decision ("how job state is persisted"), not a runtime layer.

Map every **entry point** — something a verifier runs: command, flag, route — to the seam it enters.

**Done when:** the outcome line exists, every touched file/module belongs to exactly one seam, and every entry point is listed under its seam.

### 2. Pass through or split

**Pass through** only when one seam and one entry point need one completion check: return "implement as-is", with no marker or Subtasks section.

**Split** if any holds:

- more than one seam;
- more than one entry point, each with its own check;
- **thrashing:** holding the seams requires internals you cannot stub past — re-reading covered files, dragging every interface back in.

**Done when:** the verdict is written, with a split's trigger in `**Split because:**`.

### 3. Walking skeleton

First subtask: the **walking skeleton**, the thinnest end-to-end wiring through every seam — request in, response out. Stub every seam: canned returns for new behaviour, old code still answering for a refactor. Nothing is verified yet.

Freeze each seam's **contract**, one per entry point where it has several: inputs, outputs, errors, how to reach it. **One stub per entry point** lets them fill independently. The skeleton owns shared value types; subtasks read, never rewrite them. If a subtask cannot satisfy its contract, stop and report a bad cut.

**Done when:** the end-to-end check passes against stubs, every stub has a written contract, and shared value types have landed.

### 4. One subtask per seam or entry point

Each subtask thickens one seam or one of its entry points: replace its stub with real logic behind the frozen contract. Read only its entry point, contract and shared value types; edit no other entry point's code. Add **blocked-by edges** to the skeleton and every subtask whose contract it consumes.

In a file carrying multiple entry points, each subtask's **Owns** names disjoint editable regions, allowing clean textual merges. Regions serving no entry point belong to the skeleton.

Each subtask is:

- **Independent:** needs no other seam's internals; the frozen contract is its entire interface.
- **Valuable:** the end-to-end check passes with only this entry point thickened.
- **Small:** one implementation pass, one check; two checks require two subtasks.

**Done when:** every stub has exactly one subtask spec with contract and verification; subtasks with no edge between them claim disjoint files or regions. The **frontier** (subtasks whose blockers have landed) can then run in parallel.

### 5. Integration

Integration combines the seams/entry points, sweeps up work none owns, and reruns the skeleton's end-to-end check alongside the ticket's original acceptance criteria. It blocks on every subtask. Work the skeleton alone unblocks (install, docs) gets its own subtask, free to run beside the rest.

**Done when:** every subtask has landed, no stub remains (refactor: no old-code delegation), and the end-to-end check and original acceptance criteria pass.

### 6. Recurse or stop

For a subtask that fails step 2, re-enter step 1 on its seam or entry point. Nest its skeleton, subtasks and integration in place: `03.1`, `03.2`, and so on.

**Stop and report** if no substitutable boundary exists inside the offending area: refuse the split rather than invent micro-cuts.

**Done when:** every subtask passes step 2, or its refused seam is reported as blocked.

## Writing the Subtasks section

Append below the ticket's text. Number in dependency order: skeleton first, integration last. Keep field names verbatim and every path relative to the executor's checkout.

<subtasks-section-template>

## Subtasks

**Split because:** <the trigger that fired>; <N entry points across M seams>, one implementation pass each.
**Waves:** <frontier per wave from `Blocked by` edges — W1 01; W2 02, 03; …>.

### 01 — <title>

**Owns:** editable workspace-relative files and regions in shared files — one seam or entry point only.
**Contract:** the entry point's frozen contract from the skeleton's spec.
**Verification:** its own check plus the skeleton's end-to-end check; integration names the ticket's original acceptance criteria.
**Blocked by:** the skeleton and any subtask whose contract it consumes.

</subtasks-section-template>

Mark the ticket's own head beside its status and blockers:

**Orchestrated:** <N> subtasks in <N> waves — not one implementation pass.

Code-level review runs inside every lane; the acceptance walk belongs to integration.
