---
name: address-review
description: Triage your PR's open review comments, decide together, then fix, defer or reply with exact-content approval before PR or tracker writes.
disable-model-invocation: true
---

The user authored the reviewed PR. Infer the code host from the PR link and the tracker from its linked ticket; use available session access.

## 1. Read the PR

Read the PR description, linked ticket, changed-file list and comments. The ticket sets **scope** (what this PR set out to deliver); without one, use the PR description. Stay **shallow**: open code only where a comment needs it.

**Open comments** comprise:

- **Review threads:** every unresolved thread, even if it asks for nothing, unless its latest message is the user's (waiting on the reviewer);
- **Outside threads:** only comments that ask for a change or an answer.

**Done when:** scope fits one line and the open-comment list is complete.

## 2. Triage

For every open comment:

1. Read it with its full thread.
2. Label it on merit using **Labels**, regardless of the reviewer's label. If none fits, say so and propose a label for that kind of comment for the user to add to the list.
3. Investigate **shallowly**: where the change lands and its rough size, or a one- or two-sentence answer. Fixes, designs, sketches and longer answers wait for the user's decision, even if the reviewer requests them.
4. Recommend one action and its scope fit: **fix** in this PR if in scope, **defer** if beyond scope, **disagree** if it fails on merit, or **answer**.

### Labels

- **nit**: valid minor polish (typo, naming, formatting); never blocks merge.
- **personal preference**: the reviewer's taste; either version works and no repo rule settles it.
- **should change**: a real gain (clarity, easier upkeep, a missing test); the PR works without it.
- **must change**: a defect to fix before merge (wrong behavior, security hole, broken convention).
- **blocker**: blocks merge and needs more than a local fix (wrong approach, open design or product decision).
- **question**: an answer settles the reviewer's question.

Present all open comments in one message, most severe first:

```markdown
**Scope:** <ticket>: <one line>
**Skipped:** <comments left out and why, or "none">

### <n>. <label> · <file:line, or "PR comment"> · <reviewer>
Reviewer's label: <theirs; this line only when it differs from yours>
**Asks:** <what the comment asks>
**Why:** <why the reviewer asks it>
**Takes:** <where the change lands and roughly how big it is, or the short answer>
**Recommend:** <fix | defer to a follow-up ticket | disagree | answer>, because <how it fits the scope>
```

**Done when:** every open comment appears with every field filled, and the message ends by asking the user to decide each one.

## 3. Decide

Answer the user's questions, dig deeper where asked, and revise recommendations for facts you missed. For disagreement, ask the user for a reason or propose one for confirmation.

**Done when:** every open comment has the user's decision.

## 4. Act

Before **any PR or tracker write**, get the user's approval of its **exact content**: the diff and commit message for a push, ticket or reply text, and threads to resolve. "Fix it" or "go ahead" approves the action, not content. If the user edits text, show the revision and wait for approval again.

Work in two rounds so replies can point to real commits or tickets:

1. **Changes:** implement each agreed fix yourself and show its diff. For each deferral, draft a follow-up ticket in the PR ticket's tracker: what to do, why the reviewer asked, and the comment link. After approval, push fixes and create tickets.
2. **Replies:** draft one reply per decided comment (see **Replies**) and list threads to resolve. After approval, post replies and resolve those threads.

| Decision | Reply | Thread |
| --- | --- | --- |
| fix | after push, says what changed and names the commit | resolve |
| defer | links the follow-up ticket | resolve |
| disagree | gives the user's reason | leave open |
| answer | answers the question | resolve |

### Replies

Write as the user, under their name, in ASD-STE100 Simplified Technical English. The reviewer knows the code and their comment.

- Open with the outcome: change, follow-up ticket, disagreement or answer.
- Add only what could change the reviewer's mind or let them act: usually one fact they lack and the commit or ticket link.
- Omit what they already have: their comment restated, the diagnosis, proof the fix works.
- Use only facts from the PR, investigation or user.

Before showing a draft, rewrite every AI tell:

- "not X but Y" contrasts or defenses against unraised objections;
- closing lines that repeat the point;
- chat filler: greetings, praise ("Great catch!", "You're absolutely right"), sign-offs ("Hope this helps");
- dashes joining clauses;
- inflated words (crucial, robust, seamless, leverage, enhance);
- bold labels or headings.

**Done when:** every approved push, ticket, reply and resolution is complete, and the user has an outcome list for every comment.
