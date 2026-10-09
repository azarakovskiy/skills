---
name: promote-skill
description: Update the README listing and dependency notes for one skill in this repo.
disable-model-invocation: true
---

Promote one skill in this repo. Input is the path to its `SKILL.md`. The result is updated repository documentation for that skill.

## 1. Read

Read that `SKILL.md`: frontmatter `name`, `description`, and `dependencies`. Each dependency entry has `name` and `repo`. When `dependencies.md` sits beside that skill, read the install command in it. Read the Skills table in `README.md`.

**Done when:** this skill's name, description, and dependency entries are known, and the Skills table has been read. When `dependencies.md` exists, its install command is known too.

## 2. Listing

When the `SKILL.md` is under `skills/` and that `name` has no row, add one row. The Skill cell is the frontmatter `name` in backticks. The Purpose cell is one imperative sentence with an em dash, in the same shape as the Purpose cells already in the table, and it states what the skill does. An existing row and its Purpose cell stay. When the `SKILL.md` is outside `skills/`, leave the table as it is.

**Done when:** a skill under `skills/` has exactly one row for its frontmatter `name`, and a skill outside `skills/` has left the table unchanged.

## 3. Dependencies

A dependency is an entry in this skill's frontmatter `dependencies` whose `name` matches no frontmatter `name` in this repo. The external skill stays in its own repo.

Document each one in `README.md`, immediately under the Skills table, one line:

`<skill>` requires `<dependency>` from `<repo>`: `<the install command from dependencies.md>`

A line already present for this skill stays. When this skill's `dependencies` is missing or empty, it gains no line. When a skill-tool call in this skill names a skill that `dependencies` does not list, carry that gap into the report.

**Done when:** each of this skill's external dependencies has its line under the Skills table. A skill with none has gained no line.

## 4. Report

Reply with two outcomes for this skill.

- **Listing:** the row added, the existing row left in place, or the table left unchanged because the `SKILL.md` sits outside `skills/`.
- **Dependencies:** each of this skill's lines under the Skills table, and whether that line was added or already present. When this skill has no external dependencies, say it gained no line. Name any gap carried from step 3.

**Done when:** the reply states both outcomes.
