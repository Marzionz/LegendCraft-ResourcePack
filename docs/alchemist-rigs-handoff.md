# Alchemist rig batch — draft review handoff

The Alchemist source assets and renders are in the private
[LegendCraft-Models draft PR #3](https://github.com/Marzionz/LegendCraft-Models/pull/3),
on `alchemist-rigs`. The owner chose a private Models PR plus this public handoff.
Model sources, textures, renders and detailed design contracts stay private.

Start at the private [review index](https://github.com/Marzionz/LegendCraft-Models/blob/alchemist-rigs/props/alc_review.md).
It links all nine model contracts, 31 clip GIFs and sheets, concept comparisons,
distance views and interactive previews.

The source branch starts at Models `d3a50b5`; this handoff branch starts at freshly
fetched ResourcePack `d56ded2`. Both shared checkouts were left unchanged.

## Validation

The saved-model verifier and existing ResourcePack gate table passed. The checks
did not merge or publish a dev pack and did not contact mc-dev.

The [private validation report](https://github.com/Marzionz/LegendCraft-Models/blob/alchemist-rigs/tools/alchemist_validation.md)
records the counts, environment retries and runtime limits.

## Review state

**Draft only. Owner visual approval and in-game verification are outstanding.**
The private contracts record departures from the approved concepts and integration
decisions still owed. No plugin or balance change is included.

This handoff does not register, stage, merge, deploy or publish the rigs. The normal
review gates for authoring tooling still apply before any later merge.
