# Skill authoring

Before editing a skill or its companion files, read and follow the `writing-for-agents` skill.

# Skill checks

`.githooks/pre-commit` runs `scripts/evals.py`, which checks the skills a commit touches against master; `python3 scripts/evals.py --help` says when it runs models, what blocks, and how to run it by hand.

Each case in `evals/<skill>.json` has an `id`, a `prompt` and the `expectations` the judge grades, plus two review notes for the user that the judge never sees: `tests`, the behavior the case targets, and `traps`, what the prompt leaves out, gets wrong or plants on purpose (`[]` for none).

- **Enable** on a new clone: `git config core.hooksPath .githooks`.
- **Approve a block:** the user reads the report and runs `git commit --no-verify`. An agent that hits a block shows the user the report and waits; it adds `--no-verify` only after the user explicitly says yes in chat.

# README

For each new skill, add a row to the README Skills table, and list each external dependency (a frontmatter `dependencies` entry from another repository) under `## Dependencies` with its install command. The structure checks fail when the Skills table and `skills/` disagree.
