---
name: address-review
description: Work through the open review comments on your own PR — label each on its merit, decide with you what to do, then fix, defer to a follow-up ticket, or reply, with nothing reaching the PR or the tracker before you approve it.
disable-model-invocation: true
---

The user wrote the PR and runs this skill on it after a review. Work out the code host from the PR link and the tracker from the ticket the PR links; reach both through whatever access this session has.

## 1. Read the PR

Read the PR description, the ticket it links, the list of changed files, and the comments. The ticket sets the **scope**: what this PR set out to deliver. Without a linked ticket, the PR description sets it. Stay **shallow**: open code only where a comment needs it.

The **open comments** are:

- every unresolved review thread, except one whose latest message is the user's: it waits on the reviewer;
- every comment outside a thread that asks for a change or an answer.

**Done when:** you can state the scope in one line and you hold the list of open comments.

## 2. Triage

For each open comment:

1. Read it with the rest of its thread.
2. Label it; see **Labels**.
3. Investigate, shallowly, what resolving it takes: where the change lands and roughly how big it is, or the answer when a sentence or two settles it. A fix, a design, a sketch or a longer answer waits until the user decides, even when the reviewer asks for it.
4. Recommend one action and how it fits the scope: **fix** it in this PR when the change belongs to the scope, **defer** it to a follow-up ticket when it reaches past the scope, **disagree** when it does not hold up on its merit, or **answer** it.

Present all open comments in one message, most severe first:

```markdown
**Scope:** <ticket>: <one line>
**Skipped:** <comments left out and why, or "none">

### <n>. <label> · <file:line, or "PR comment"> · <reviewer>
Reviewer's label: <theirs; this line only when it differs from yours>
**Asks:** <what the comment asks>
**Why:** <why the reviewer asks it>
**Takes:** <where the change lands and roughly how big it is, or the short answer>
**Recommend:** <fix | defer | disagree | answer>, because <how it fits the scope>
```

**Done when:** every open comment appears with every field filled, and the message ends by asking the user to decide each one.

## 3. Decide

Answer the user's questions, dig deeper where they ask, and revise a recommendation when they bring a fact you missed. A disagreement reply needs a reason: ask the user for it, or propose one for them to confirm.

**Done when:** every open comment has the user's decision.

## 4. Act

Every write to the PR or the tracker waits until the user approves its exact content: the diff and commit message of a push, the text of a ticket or a reply, the threads to resolve. A decision such as "fix it" or "go ahead" approves the action, not the content. When the user edits a text, show the new version and wait for approval again.

Work in two rounds, so each reply can point to a real commit or ticket:

1. **Changes:** make each agreed fix yourself and show the diff. Draft a follow-up ticket for each deferred comment, in the tracker that holds the PR's ticket: what to do, why the reviewer asked, and a link to the comment. After approval, push the fixes and create the tickets.
2. **Replies:** draft a reply to each decided comment (see **Replies**) and list the threads to resolve. After approval, post the replies and resolve those threads.

| Decision | Reply | Thread |
| --- | --- | --- |
| fix | goes out after the push; says what changed and names the commit | resolve |
| defer | links the follow-up ticket | resolve |
| disagree | gives the user's reason | leave open |
| answer | answers the question | resolve |

**Done when:** every approved push, ticket, reply and resolve is done, and the user has a list of what happened to each comment.

## Labels

- **nit**: a small, valid polish item (typo, naming, formatting). It never holds the merge.
- **personal preference**: the reviewer's taste. The code works either way, and no repo rule settles it.
- **should change**: a real gain, such as clarity, easier upkeep or a missing test. The PR works without it.
- **must change**: a defect this PR must fix before merge, such as wrong behavior, a security hole or a broken convention.
- **blocker**: holds the merge and needs more than a local fix, such as a wrong approach or an open design or product decision.
- **question**: the reviewer asks something, and an answer settles it.

Label each comment on its merit, whatever the reviewer called it ("nit:", "blocking"). When their label differs from yours, show it next to yours. When no label fits, say so and propose a new label for that kind of comment, for the user to add to this list.

## Replies

A reply goes out under the user's name to a reviewer who knows the code and their own comment. Write it as the user, in ASD-STE100 Simplified Technical English.

- Open with the outcome: the change, the follow-up ticket, the disagreement, or the answer.
- Add only what could change the reviewer's mind or lets them act: usually one fact they lack, and the commit or ticket link.
- Leave out what the reviewer already has: their comment restated, the diagnosis, proof that the fix works.
- State only facts from the PR, the investigation or the user.

Before you show a draft, rewrite every AI tell in it:

- a "not X but Y" contrast, or a defense against an objection nobody raised;
- a closing line that repeats the point;
- chat filler: greetings, praise ("Great catch!", "You're absolutely right"), sign-offs ("Hope this helps");
- a dash joining two clauses;
- inflated words such as crucial, robust, seamless, leverage, enhance;
- bold labels or headings.
