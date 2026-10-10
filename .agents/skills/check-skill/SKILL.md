---
name: check-skill
description: Gate every public skill package change with a fast current-only behavioral eval; also run directly for one exact skill.
metadata:
  internal: true
---

# Check Skill

Run automatically after final changes to a package under `skills/`, or as `check-skill <exact skill name>`. This is the edit-loop gate; `promote-skill` owns final release. Keep the repository unchanged.

## 1. Select

Automatic use: select every public skill package changed by the parent task. Direct use: require one exact skill name. For each selection, match the sole public `SKILL.md` frontmatter name and its `evals/<name>.json`; return `BLOCKED` on a missing or duplicate match.

**Done when:** every selected package has one exact skill name and evaluation record, or `BLOCKED` names the unresolved selection.

## 2. Lock the suite

Read `cases` from the evaluation record's committed `HEAD` version and use them verbatim. Return `BLOCKED` when the record is missing or invalid, the committed suite is empty, or working `cases` differ from `HEAD`. Ignore `comparison`; promotion owns recorded scores.

**Done when:** each selected skill has one nonempty committed suite identical to its working `cases`, or `BLOCKED` names the suite defect.

## 3. Run current behavior

Snapshot the final package's complete recursive regular-file set. Choose one available local agent/model pair and run every committed case in parallel, each in a fresh context containing only that package and the case prompt. Start at `SKILL.md` and resolve relative references only inside the snapshot. Return `BLOCKED` when the environment or snapshot is unavailable.

Judge each output against every criterion. `PASS` requires observable satisfaction of every criterion; otherwise mark `FAIL` and cite the missing or contradicted behavior.

**Done when:** every case has one fresh output and a criterion-complete verdict, or `BLOCKED` names the unavailable prerequisite.

## 4. Report

Report every case as `PASS` or `FAIL`, with concise evidence for failures, then one overall result. Overall `PASS` requires every case to pass; `FAIL` or `BLOCKED` prevents parent-task completion. Return the gate result without human confirmation; promotion owns human-confirmed scoring and recording.

**Done when:** every committed case appears once, the overall result follows its case verdicts, and the repository remains unchanged.
