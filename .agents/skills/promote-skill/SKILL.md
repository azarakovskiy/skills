---
name: promote-skill
description: Evaluate and promote one exact skill with a human-confirmed comparison.
disable-model-invocation: true
metadata:
  internal: true
---

# Promote Skill

Invoke as `promote-skill <exact skill name>`. This is the final release workflow. Work locally with repository tools, clean local agents, and the Python standard library. Keep model outputs in the conversation only; write no raw output, commit, or push.

## 1. Select

Require one skill name. Read the frontmatter of every `skills/**/SKILL.md` and select the sole exact `name` match; `.agents/skills/` is outside the search. Stop on a missing or duplicate match and list the paths searched or matched. Set its evaluation record to `evals/<name>.json`.

**Done when:** exactly one installable skill path and its one evaluation path are named, or selection has stopped with a concrete missing/duplicate report and no file changed.

## 2. Lock the suite

Read the evaluation record and the `cases` value from its committed `HEAD` version. Use those committed prompts and criteria verbatim. If the working `cases` differ, show the exact proposed changes and request explicit approval. Approval invalidates historical results: retain the approved cases, set `comparison` to `null`, and stop so the suite can be committed before evaluation. Never fold a case change into a promotion run.

**Done when:** the run has a nonempty, committed, unchanged case suite whose root `skill` equals the selected name; or an approved suite change has cleared `comparison` and the run has stopped before evaluation.

## 3. Establish the comparison

Discover the pull request base ref from available environment and repository/PR tools. Ask the human for the base ref only when those sources cannot identify it, then require that ref to resolve locally. At that ref, locate the skill with the same exact frontmatter name. Read the package-hash implementation in `scripts/evals.py`, then materialize its complete recursive regular-file set from that ref as an isolated base arm, preserving relative paths and excluding the symlinks or special files that the hash excludes. Snapshot the same complete file set from the selected working directory as an isolated current arm. Resolve each arm's relative references only within its own snapshot: a base file must never fall through to a current companion file. No base match means an initial baseline with no base arm; stop on multiple base matches.

Choose one locally available `{agent, model}` pair, announce it, and use that exact pair for every candidate run and scoring run in this evaluation.

**Done when:** a resolvable base ref, either one complete isolated base package or an initial-baseline decision, one complete isolated current package, and one explicit local agent/model pair are recorded for the run; each package exactly matches the reporter's hashable file set and every relative reference is bound to its own arm.

## 4. Hash the inputs

Using Python's standard library, calculate:

- `suite_hash` as `sha256:` plus the lowercase SHA-256 of `json.dumps(cases, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()`;
- each `skill_hash`, retaining that JSON field name, by applying the deterministic package-hash algorithm in `scripts/evals.py` to the arm's complete isolated skill directory.

Use the current directory snapshot for `current`; use `base: null` when there is no base arm. The directories hashed here must be the exact snapshots evaluated in the next step.

**Done when:** the immutable suite and every available complete arm package have their required hashes, and each package hash identifies the exact directory snapshot—including companion files—that will run.

## 5. Evaluate blind

For every case, run each available arm in a fresh local agent context with the recorded agent/model, supplying only that arm's complete isolated directory and the case prompt. Start at its `SKILL.md` and resolve every relative reference from that same arm, so a base run can read only base companion files. Give neither arm information about the other. Randomly label the two outputs A/B before a fresh scoring agent sees them; give the scorer only the prompt, criteria, and labeled outputs. Have it assign each output an integer score from 0 through 100 against the criteria and a concise, evidence-based rationale. Reveal the mapping only after both scores are fixed. For an initial baseline, score the current arm alone and keep the case's base score `null`.

Compute each aggregate as the nearest-integer equal-weight mean: `(sum(scores) + len(scores)//2)//len(scores)`. Retain raw outputs only long enough for human review.

**Done when:** every suite id has the required provisional score or scores and a nonempty rationale, every run used only its own complete package, the blinded mapping has been revealed, both aggregates (or the current aggregate alone) have been computed, and no raw output has been written to disk.

## 6. Confirm with the human

Show the human, per case, the prompt, criteria, relevant output evidence, revealed arm mapping, provisional scores, and rationale; then show hashes, environment, aggregates, and `base → current (delta)` when a base exists. Explicitly warn when the delta is negative and continue. Ask the human to confirm or correct the scores and rationales, and identify the confirmer when their identity is not already unambiguous. Wait for an explicit response before recording anything.

Apply every correction and recompute aggregates with the same formula.

**Done when:** the human has explicitly confirmed the final per-case scores and rationales, the confirmer is identified, corrected aggregates are shown, and any regression warning has been acknowledged without blocking progress.

## 7. Record

Replace only `comparison` in `evals/<name>.json` with:

- `suite_hash` and `environment: {agent, model}`;
- `base: null`, or `{skill_hash, score}` for the evaluated base;
- `current: {skill_hash, score}`;
- `cases`, in suite order, each exactly `{id, base, current, rationale}` with `base: null` exactly when the comparison base is null;
- nonempty `confirmed_by` and current `confirmed_at` strings.

Keep integer scores in `0..100`, exact suite-id coverage, and aggregate scores equal to the confirmed case means. Preserve root `skill` and `cases`. Store no prompts, criteria copies, raw outputs, or secrets inside `comparison`.

**Done when:** the evaluation file contains exactly the confirmed compact comparison for the hashed inputs and stable suite, with no raw model output persisted.

## 8. Synchronize documentation

Read and follow `../sync-docs/SKILL.md` with the selected exact skill name as its input. It is the single source of truth for documentation synchronization; do not improvise another process.

**Done when:** every completion criterion in that skill's named-skill path is satisfied and its report names exactly the selected skill.

## 9. Validate and report

From the repository root, run `python3 scripts/evals.py --base <resolved-base-ref>`. Fix structural or consistency errors in the record and rerun. Report warnings, including stale/missing comparisons or regressions, without treating them as blockers.

**Done when:** the reporter exits successfully, its Markdown base/current score report has been shown (and appended to `GITHUB_STEP_SUMMARY` when configured), and the workspace remains uncommitted and unpushed.
