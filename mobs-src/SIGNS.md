# Knight Horn Blast sign ledger

## HORN-BLAST-01 / HORN-BLAST-02 — 2026-09-25

Paired single-key, step-held throwaway clips were loaded and rendered through
Blockbench MCP on the copied horn geometry, then inspected side by side.
Evidence: [paired captures](props/knight_horn_blast_sign_probes.png).
Format 4.10 Generic Model imported into the connected Blockbench editor.
Root and yaw parent unrotated for the probe; horn pivot `(0,22,-9)`.
Witness `bell_strap_tab` world AABB centre:

| ID | Channel | Negative probe | Positive probe | Observed result |
|---|---|---|---|---|
| HORN-BLAST-01 | horn rotation X, +/-35 degrees | Y=24.188258, Z=-15.524878 | Y=16.617049, Z=-13.287929 | Negative X lifts the outward bell; positive lowers it |
| HORN-BLAST-02 | horn position Y, +/-5 units | Y=15.050000 | Y=25.050000 | Positive Y lifts the horn |

Cube rest rotation was preserved on import: the source mouth-lip cube remains
`[-22.5,0,0]`. Animation X is inverted by the 4.10 import path; rest yaw parents
rotate the horn frame radially. All four horn children share the probed local frame.
The authored nonzero animation components are X rotation (0 to -22) and Y position
(0 to +2); they trace to the two rows above. No animated yaw, roll, X/Z translation,
or 180-degree mob-root assumptions are used. Scale-stage keys require no sign probe.

Probe clips exist only in scratch, never in the final rig. The live 31-tick check
confirms all four raised world transforms remain fixed throughout hold and fade.
