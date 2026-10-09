# skills

Personal agent skills, installed with the [`skills`](https://github.com/vercel-labs/skills) CLI.

## Install

```bash
# interactive: choose skills, scope (project/global) and method (symlink/copy)
npx skills@latest add azarakovskiy/skills

# global, no prompts, into ~/.agents/skills (read by every universal agent)
npx skills@latest add azarakovskiy/skills -g --agent universal -y

# list available skills without installing
npx skills@latest add azarakovskiy/skills --list
```

Update installed skills later with `npx skills@latest update`.

## Skills

| Skill | Purpose |
| --- | --- |
| `decompose-ticket` | Split a ticket too big for one implementation pass into a walking skeleton, one subtask per seam or entry point with frozen contracts, and an integration task — the ticket marked orchestrated, subtasks in dependency order, parallel where the owned regions are disjoint. |
| `meta-prompt` | Turn a rough request into a shared, execution-ready task — explore missing context, resolve consequential decisions, check that the work fits one smart zone, confirm the brief, then execute it or write a reusable prompt. |
| `zoom-out` | Explain a complex or abstract subject through its purpose, boundaries, components, and a concrete example — epitome, why it matters, what the explanation includes, a map of the parts, then one component shown in an example and placed back on the map. |

`meta-prompt` requires `grilling` from `mattpocock/skills`: `npx skills@latest add mattpocock/skills --skill grilling`

## Layout

One directory per skill: `skills/<category>/<name>/SKILL.md`. The installer walks `skills/`
three levels deep, so flat (`skills/<name>/`) and one or two category levels both work.
The installed directory is named after the frontmatter `name`, never the category.

Required frontmatter:

```yaml
---
name: decompose-ticket
description: One line shown when an agent picks the skill.
---
```

No `package.json` or plugin manifest is needed.
