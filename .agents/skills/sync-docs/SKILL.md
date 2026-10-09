---
name: sync-docs
description: Synchronize README listing and dependency notes for one named skill under `skills/`, or every skill there.
disable-model-invocation: true
metadata:
  internal: true
---

# Sync Docs

Synchronize repository documentation for installable skills. Input is optional: a supplied input is an exact frontmatter skill `name`, not a path; omitted input selects every `SKILL.md` beneath `skills/`.

## 1. Select

Find every file named `SKILL.md` beneath `skills/` and read its frontmatter `name` before editing `README.md`.

- With input, select the one file whose `name` exactly matches it. No match is an unknown name: stop, name the input and the searched `skills/` tree, and leave `README.md` unchanged. More than one match is ambiguous: stop, name the input and every matching path, and leave `README.md` unchanged.
- Without input, select every file found.

Files outside `skills/`, including repository-local utilities under `.agents/skills/`, are never candidates.

**Done when:** input has resolved to exactly one selected file, or omitted input has selected every `SKILL.md` beneath `skills/`. An unknown or ambiguous input has instead produced the concrete failure report and stopped before any `README.md` edit.

## 2. Read

For every selected skill, read its frontmatter `name`, `description`, and `dependencies`. Each dependency entry has `name` and `repo`. When `dependencies.md` sits beside a selected skill, read its install command. Inspect its skill-tool calls for names missing from `dependencies`.

Read the Skills table in `README.md` and the frontmatter `name` of every `SKILL.md` in the repository; the latter set distinguishes repository skills from external dependencies.

**Done when:** every selected skill's fields and skill-tool calls are known, all repository skill names and the Skills table are known, and every available adjacent install command needed below is known.

## 3. Listing

For each selected skill whose `name` has no row in the Skills table, add one. The Skill cell is the frontmatter `name` in backticks. The Purpose cell is one imperative sentence with an em dash, in the same shape as the Purpose cells already in the table, and states what the skill does. Leave an existing row and its Purpose cell unchanged.

**Done when:** every selected skill has exactly one row for its frontmatter `name`, and no unselected skill's row changed.

## 4. Dependencies

An external dependency is an entry in a selected skill's frontmatter `dependencies` whose `name` matches no frontmatter `name` in the repository. The external skill stays in its own repository.

Document each external dependency immediately under the Skills table, one line:

`<skill>` requires `<dependency>` from `<repo>`: `<the install command from dependencies.md>`

Leave a line already present for that skill unchanged. A skill with missing or empty `dependencies` gains no line. Carry into that skill's report any skill-tool call naming a skill absent from its `dependencies`.

**Done when:** every selected skill's external dependencies have their lines under the Skills table, each selected skill with none has gained no line, and every undeclared skill-tool call has been recorded for reporting.

## 5. Report

Give one compact outcome per selected skill:

- **Listing:** the row added or the existing row left in place.
- **Dependencies:** every dependency line and whether it was added or already present; when there are none, say the skill gained no line; name every undeclared skill-tool call.

Use the frontmatter `name` to identify each outcome, adding its repository-relative path only when names repeat. Do not repeat the workflow or unchanged table content.

**Done when:** a named run reports exactly its one selected skill; a no-input run reports every selected `SKILL.md` exactly once, with the number of outcomes matching the files selected in step 1. In both branches, every listing and dependency result from steps 3 and 4 is represented.
