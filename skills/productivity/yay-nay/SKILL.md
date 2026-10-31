---
name: yay-nay
description: Say concisely whether the last reply needs human attention or we're all set.
disable-model-invocation: true
---

# Yay or nay

Read the last reply, the work it reports, and the request it answers. Find every **attention item**: something the user must act on, decide, or know before relying on the result. Typical items:

- a question, choice, or approval the reply leaves to the user
- a blocker, error, or warning
- a check that failed, was skipped, or was not run
- asked-for work the reply does not report as done
- a stated risk, assumption, or unverified claim
- a manual step: a command, a credential, a setting, a review

When unsure, count it.

Answer with the verdict alone.

No items:

> Yay, we're all set. Nothing to look at, there are no issues.

Items (most blocking first, one short sentence each):

> Nay, not quite done yet. These need your attention:
>
> - <item>: <the user's next action>
