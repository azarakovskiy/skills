# Write the execution prompt

Turn the confirmed brief into the minimum **standalone** prompt under [prompt-quality.md](prompt-quality.md): understandable without this conversation, runnable AFK, every open choice the executor's. Keep the user's precise wording; leave an adequate prompt unchanged.

- For splits, write one prompt per part, naming required outputs of earlier parts and where to find them.
- Omit the brief's model nudges from prompts: they guide the user, not the executor, which cannot choose its model.

Revalidate every prompt against the confirmed brief and every line of prompt-quality.md: all settled decisions carried, nothing invented, no question left for a human.

Send one labeled, copyable block per prompt:

````
**<part name>**
```markdown
<the prompt>
```
````
