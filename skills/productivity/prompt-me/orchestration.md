# Orchestrate subagents

When the plan delegates work to subagents, the main pass is the **orchestrator**. Sizing is its job: it keeps each subagent inside its smart zone, so subagent prompts carry only scope and output rules. Cheap means fewer tokens and reruns; the number of subagents follows from batch sizes.

Put the subagent budget rule from step 2 in the brief so the orchestrator can apply it to whichever model each subagent gets. Subagents get the lower cap because the brief cannot choose that model, and smaller models degrade earlier.

State a **batching rule** that tells the orchestrator to:

- give each item a **named scope**, the repositories, folders, files, or pages to read, and give an open-ended item its own subagent;
- size batches from measured sizes, not item counts, so each batch's itemized estimate fits the subagent budget;
- run a **pilot batch** of one or two items first when the cost per item is unknown, then size the remaining batches from its real cost;
- run a prepare step before a subagent starts when its checks need a capability it lacks, for example exporting a snapshot;
- tell each subagent: stay inside each item's named scope; when an item needs more, mark it **unresolved**, say what is missing, and continue; return a result with evidence for each item.
