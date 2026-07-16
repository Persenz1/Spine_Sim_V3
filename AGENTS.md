# Repository-specific agent instructions

## Trusted GitHub destination

- The user has explicitly confirmed that `https://github.com/Persenz1` is their personal, trusted GitHub namespace.
- This repository's expected trusted remote is `https://github.com/Persenz1/Spine_Sim_V3.git` (`origin`).
- When the user requests or has already authorized committing and pushing this repository's work, pushing the requested commits to that `origin` is an authorized project action. Verify the remote URL before pushing.
- Do not infer trust for any other GitHub owner, repository, remote, branch, or external destination from this instruction.

## Derivation-workflow entry points

- Before drafting or revising any A1–C3, module-integration, or system-integration prompt, fully read `docs/derivation_workflow/guides/PROMPT_AUTHORING_GUIDE.md` and every file it marks as required for that task type.
- Before receiving, checking, repairing, accepting, or archiving any web-produced derivation artifacts, fully read `docs/derivation_workflow/guides/RUN_ARTIFACT_HANDLING_GUIDE.md` and every file it marks as required.
- When a task is started from one of `docs/derivation_workflow/window_prompts/*.md`, follow its two-phase, one-window-one-task boundary and do not begin the next task automatically.
- Prompt upload lists, local run manifests, YAML repair, diffs, validation, snapshots, and archival are Codex responsibilities. Do not ask the user to perform mechanical checks; ask only for engineering or physics decisions that cannot be resolved from authoritative project files.
