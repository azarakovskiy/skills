# Write the execution prompt

The user confirmed the brief and wants a reusable prompt. Write that brief as the minimum prompt. Keep the user's wording where it is precise. Leave a prompt that already meets this bar unchanged.

- Point at sources of truth, and tell the executor to inspect discoverable facts.
- For missing evidence, require an explicit unknown or a blocking question.
- Add an example only when the output pattern would otherwise be ambiguous.
- Separate instructions, context, and input with a heading or a tag only when they could be confused.
- Write one prompt per agreed zone.

Send one copyable block, then the session verdict:

````
```markdown
<the prompt>
```
Run this prompt <in a new session | here>.
Reason: <one sentence>
````
