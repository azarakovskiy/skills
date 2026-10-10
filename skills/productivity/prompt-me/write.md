# Write the execution prompt

Apply [prompt-quality.md](prompt-quality.md) to write the confirmed brief as the minimum **standalone** prompt: it must make sense without this conversation. Keep precise user wording; leave an already adequate prompt unchanged.

- Carry forward settled decisions and necessary user-provided facts. Use resolvable pointers for discoverable facts and require lookup or verification before relying on unknowns.
- Add an example only when the output pattern would otherwise be ambiguous.
- Separate instructions, context, and input with a heading or a tag only when they could be confused.
- Write one prompt per agreed pass. Name prerequisite outputs and where to find them so later passes can resume without the earlier conversation.
- Carry the applicable **Models** category, effort, and concise task-grounded reason into each prompt, leaving specific model selection to the user. Keep switching advisory; preserve every **Required** capability and its task-grounded reason separately.

Revalidate the finished prompt against the confirmed brief: preserve every requirement and settled decision, remove contradictions or invented requirements, and keep remaining unknowns explicit.

Send a labeled copyable block for each pass, then the session verdict:

````
```markdown
<the prompt>
```
Run this prompt <in a new session | here>.
Reason: <one sentence>
````
