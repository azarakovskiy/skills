# Write the execution prompt

Apply [prompt-quality.md](prompt-quality.md) to turn the confirmed brief into the minimum **standalone** prompt: it makes sense without this conversation and runs AFK, so every open choice is the executor's to make. Keep the user's precise wording; leave an already adequate prompt unchanged.

- Write one prompt per part of a split. Name what a part needs from earlier parts and where to find it.
- Keep the brief's model nudge out of the prompts. It tells the user which model to start the session on; the executor cannot pick its own model.

Revalidate each prompt against the confirmed brief and every line of prompt-quality.md: every settled decision carried, nothing invented, no question left for a human.

Send one labeled, copyable block per prompt:

````
**<part name>**
```markdown
<the prompt>
```
````
