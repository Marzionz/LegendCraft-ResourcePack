# LegendCraft-ResourcePack — repo contract

Resource-pack build + deploy tooling for the LegendCraft mc-dev box. Reviews of this repo
grade against `C:\Repositories\Standards\ENGINEERING_STANDARDS.md` first; the rule below is
this repo's own layer on top, born from a merged finding.

## Contract rules

1. **Every operator-facing "what to do next" line a script emits is either held by a test
   arm or listed as deliberately uncovered.** A script that instructs a human (a runbook
   line, a preflight verdict, a next-step hint) is making a claim about the world; an
   asserted-but-never-exercised instruction is exactly where a wrong step costs the shared
   box. (Origin: PROP-STAGE, `d33dd26` PR #2 — the prop runbook shipped as asserted text,
   standing WARN at confidence 65 until walked at the box.)

## Gate mechanics

- Executable tooling here is §19-gated (Claude gate per owner ruling: no sol for dev
  tooling; every gated merge takes a row in the hub's `Plans/todo/review-audit-queue.md`).
  Pack content/assets are the content track and commit direct.
- Deploys to mc-dev follow the deploy lock + stop-before-swap rules in
  `C:\Repositories\Standards\MINECRAFT_STANDARDS.md`; the pack sha1 gets pinned per
  `project_mcdev_model_deploy`.
