# Missing dependencies

When a dependency is unavailable, warn that `prompt-me` works best with the full `grilling` and `writing-for-agents` skills. Name the missing skill, say that its bundled fallback will be used, and offer this install command before continuing:

```bash
npx skills@latest add mattpocock/skills --skill grilling --skill writing-for-agents
```
