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
| `prompt-me` | Turn a rough request into a confirmed task brief — clarify consequential gaps, assess scope and session fit, then recommend where to execute or provide a reusable prompt. [[has-dependencies]](#dependencies) |
| `zoom-out` | Explain a complex or abstract subject through its purpose, boundaries, components, and a concrete example — epitome, why it matters, what the explanation includes, a map of the parts, then one component shown in an example and placed back on the map. |

## Dependencies

| Skill | Dependencies |
| --- | --- |
| `prompt-me` | Uses `grilling` and `writing-for-agents` from [`mattpocock/skills`](https://github.com/mattpocock/skills), with bundled fallbacks when unavailable: `npx skills@latest add mattpocock/skills --skill grilling --skill writing-for-agents` |
