# Repository-specific agent instructions

## Trusted GitHub destination

- The user has explicitly confirmed that `https://github.com/Persenz1` is their personal, trusted GitHub namespace.
- This repository's expected trusted remote is `https://github.com/Persenz1/Spine_Sim_V3.git` (`origin`).
- When the user requests or has already authorized committing and pushing this repository's work, pushing the requested commits to that `origin` is an authorized project action. Verify the remote URL before pushing.
- Do not infer trust for any other GitHub owner, repository, remote, branch, or external destination from this instruction.

## Current theory handoff

- Start current theory, paper, solver, and parameter tasks at `theory/README.md`; do not traverse `archive/` by default.
- The accepted 1.0 system/modules remain the formal authority. `theory/paper/MECHANISM_DERIVATION_FORMAL.md` is a proposed, closure-corrected derivation and must not be silently treated as accepted.
- A/B/C low-level authority remains in `theory/modules/`. The standalone files in `theory/interfaces/` are exact public-contract mirrors embedded in the A/B modules and are retained as implementation/audit entry points.
- Final A3/B3/C3 rolling contexts are historical only and live under `archive/web_pro_derivation_2026-07-17/derivation/modules/*/history/`; do not treat them as current peers of the integrated modules.
- `theory/evidence_reassessment/` contains working copies for future paper-to-evidence reverse review. The archive retains the complete source copies, including ZIPs, evidence cards, extraction audits, figures, and the generated engineering-context view. Evidence working copies are non-normative and must not silently modify accepted theory.
- Before solver implementation or parameter work, fully read `theory/review/DERIVATION_VERIFICATION_2026-07-17.md`, `theory/implementation/BOOTSTRAP_CALIBRATION_AND_PARAMETER_POLICY.md`, and `theory/implementation/DEV_BOOTSTRAP_PROFILE.yaml`.
- Where the review marks a P0 issue, use the explicitly closed M0 branch or return unavailable until a versioned amendment is accepted; do not implement an ambiguous formula.
- Nonzero `+X`, `45°`, and rocking C-layer execution remains blocked by `B_TO_C 1.0.0`. Do not bypass that contract boundary with projections, rotated legacy wrenches, or empirical capability domains.

## Derivation-workflow entry points

- Before drafting or revising any archived A1–C3, module-integration, or system-integration prompt, fully read `archive/web_pro_derivation_2026-07-17/docs/derivation_workflow/guides/PROMPT_AUTHORING_GUIDE.md` and every file it marks as required for that task type.
- Before receiving, checking, repairing, accepting, or archiving any web-produced derivation artifacts, fully read `archive/web_pro_derivation_2026-07-17/docs/derivation_workflow/guides/RUN_ARTIFACT_HANDLING_GUIDE.md` and every file it marks as required.
- When a task is started from one of `archive/web_pro_derivation_2026-07-17/docs/derivation_workflow/window_prompts/*.md`, follow its two-phase, one-window-one-task boundary and do not begin the next task automatically.
- Prompt upload lists, local run manifests, YAML repair, diffs, validation, snapshots, and archival are Codex responsibilities. Do not ask the user to perform mechanical checks; ask only for engineering or physics decisions that cannot be resolved from authoritative project files.

## Simulator-development entry points

- Start simulator planning and implementation tasks at `docs/simulator_development/README.md` and follow `docs/simulator_development/REQUIREMENTS_DISCUSSION_WORKFLOW.md`.
- Each simulator module uses a requirements-discussion window followed by a separate implementation window. A requirements window must not start coding, and an implementation prompt must be generated from the frozen module requirements rather than from a generic template.
- Respect the M00→M07 dependency and frozen-requirements gates in `docs/simulator_development/SIMULATOR_MODULE_PLAN.md`. M08 C diagnostics are deferred and do not block the first A/B release.
- The plotting module is a read-only consumer of versioned result data. It must not import or invoke simulator internals, mutate canonical results, or rerun simulations. Missing raw data must be proposed through a versioned `PLOT_DATA_GAP_REQUEST` and implemented by the owning source module in a separate task.
- First-release results remain `DEV_PRIOR / synthetic_surface / no_damage / not_certifiable`. Do not request absent experimental data or silently promote development priors into measured material parameters.
