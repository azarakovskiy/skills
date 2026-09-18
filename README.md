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
| `hello-world` | Throwaway check that installation works end to end. |

## Layout

One directory per skill: `skills/<category>/<name>/SKILL.md`. The installer walks `skills/`
three levels deep, so flat (`skills/<name>/`) and one or two category levels both work.
The installed directory is named after the frontmatter `name`, never the category.

Required frontmatter:

```yaml
---
name: hello-world
description: One line shown when an agent picks the skill.
---
```

No `package.json` or plugin manifest is needed.
