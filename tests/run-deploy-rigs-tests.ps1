#Requires -Version 5.1
<#
.SYNOPSIS
  Contract tests for deploy-rigs.ps1.

.DESCRIPTION
  Builds a synthetic mobs-src tree in a temp directory it owns, runs the stager
  against it with -Json, and asserts on the result. No real rig is read: every
  fixture .bbmodel here is hand-written, so a change to the authoring repo can
  never turn this suite green or red by accident.

  Organised by CONTRACT AREA:

    STG    what a successful stage puts on disk, and where
    FAIL   the eight ways a rig is rejected - each one LOUD and named
    ATOM   all-or-nothing: one bad rig stages none of them
    VER    the verification list handed to the owner for the box window
    IDEM   re-running does not leave a stale rig behind
    JSON   the machine-readable arm the rest of this suite reads
    PROP   -Prop: the identity-root assertion, in place of the mob facing yaw

  RUN IT when deploy-rigs.ps1 changes:

      powershell -NoProfile -File tests\run-deploy-rigs-tests.ps1

  ---------------------------------------------------------------------------
  SECTION 16 - acceptance list, then RED, then code.

  Requirement: MM-P3 in LegendCraft/Plans/in-progress/mythicmobs-backlog.md,
  as scoped by the slice brief - a STAGE-ONLY rig deployment step (the owner
  performs the copy into mc-dev under the deploy lock), whose own contract is:
  a rig that fails conversion fails loudly with its name and is never silently
  skipped, and the output folder shape matches BetterModel 3.3.0 exactly.

  The acceptance criteria, written from that requirement before deploy-rigs.ps1
  existed:

    AC-1   a staged rig lands at <stage>/models/<rig>.bbmodel, byte-identical
           to its source                                              STG-01
    AC-2   <stage>/models/ holds exactly one file per requested rig and
           nothing else - BetterModel 3.3.0 loads .bbmodel flat out of
           plugins/BetterModel/models, so the staged folder IS that folder
                                                                      STG-02
    AC-3   the verification list is written OUTSIDE models/, so copying
           models/ into the plugin folder carries no stowaway          STG-03
    AC-4   a requested rig with no .bbmodel under the source root fails,
           naming that rig                                             FAIL-01
    AC-5   a rig name matching more than one .bbmodel fails, naming the rig
           and every path it matched                                   FAIL-02
    AC-6   a .bbmodel that is not parseable JSON fails, naming that rig
                                                                       FAIL-03
    AC-7   a .bbmodel whose internal `name` differs from its filename stem
           fails, naming both values                                   FAIL-04
    AC-8   a non-empty `model_identifier` that differs from the stem fails
           the same way                                                FAIL-05
    AC-9   a rig without a single origin-anchored top-level `root` bone
           carrying rotation [0,180,0] fails, naming that rig          FAIL-06
    AC-10  a rig with no embedded texture fails, naming that rig       FAIL-07
    AC-11  a rig with no elements fails, naming that rig               FAIL-08
    AC-12  when ANY requested rig fails, NO rig is staged and EVERY failing
           rig is reported - a partial stage must never reach the owner, and
           a skip must never be silent                                 ATOM-01
    AC-13  when every rig passes, exit code is 0 and every rig is reported
           staged                                                      ATOM-02
    AC-14  the verification list carries, per staged rig, its sha1 and its
           animation clip names                                        VER-01
    AC-15  facing reads VERIFIED for bone_colossus and UNPROVEN for every
           other rig - only bone_colossus has been seen facing correctly
           in game, and the 180-degree root yaw is unproven on the rest
                                                                       VER-02
    AC-16  re-staging replaces the stage directory: a rig from a previous
           run does not survive into the next one                      IDEM-01
    AC-17  -Json emits a parseable result carrying staged rigs and failures
                                                                       JSON-01
    AC-18  a comma-joined rig list arriving as ONE argument stages every rig
           in it - `powershell -File script.ps1 -Rig a,b` hands the parameter
           the single string "a,b", which is how the owner will invoke this
                                                                       RIG-01
    AC-19  a destination inside a plugins/BetterModel folder is REFUSED with
           nothing written and nothing deleted - stage-only has to be enforced
           by the script, not promised by its documentation           SAFE-01
    AC-20  a destination under a live server root (an ancestor holding
           server.properties) is refused the same way                 SAFE-02
    AC-21  a validation failure INVALIDATES a previously staged models/ and
           VERIFY.md - a refused run must not leave deployable output behind
                                                                      ATOM-03
    AC-22  a failure during the write phase promotes nothing, leaves no
           partial models/, and invalidates the previous stage        ATOM-04
    AC-23  a missing source root reports one named failure per requested rig
           through the normal result path, not a raw exception         SRC-01
    AC-24  a source root that cannot be enumerated does the same       SRC-02
    AC-25  a texture whose `source` is not a data: URI fails, naming the rig -
           a .bbmodel pointing at a workstation file stages happily and
           renders blank                                              FAIL-09
    AC-26  a texture whose base64 payload does not decode fails the same way
                                                                      FAIL-10
    AC-27  the generated runbook carries acquire, baseline, verify and release
           IN THAT ORDER - without baseline and verify the load, render and
           facing readings cannot be attributed to the deployed build  VER-03
    AC-28  when cleanup after a refusal CANNOT remove a previously staged rig,
           the run says so explicitly, naming the surviving path, and the
           surviving folder is left un-READY. Deleting is best-effort on a
           filesystem; telling the truth about it is not               ATOM-05
    AC-29  a successful stage writes a STAGE-READY marker listing every rig
           with its sha1, and the runbook makes that marker the precondition
           for copying anything                                        VER-04
    AC-30  a data: URI with an EMPTY base64 payload fails, naming the rig -
           zero decoded bytes is not a texture                        FAIL-11
    AC-31  a payload that decodes but is not a PNG fails, naming the rig -
           "it decoded" is not "it is an image"                       FAIL-12
    AC-32  a refusal whose STAGE-READY cannot be deleted leaves a STAGE-INVALID
           tombstone, names the surviving marker rather than claiming it is
           gone, and the surviving marker CANNOT make the stage deployable
                                                                     READY-01
    AC-33  the preflight passes on a complete stage                    PRE-01
    AC-34  the preflight fails when models/ does not match STAGE-READY
           exactly - a rig whose bytes changed, or a file the marker never
           listed                                                      PRE-02
    AC-35  a successful run removes STAGE-INVALID as its final action, and the
           runbook makes the owner RUN the preflight rather than look at a
           marker                                                      PRE-03
    AC-36  an invocation naming no rigs and asking for no preflight refuses
           rather than staging nothing quietly                         RIG-02
    AC-37  the preflight fails when VERIFY.md is missing - the runbook IS part
           of the deliverable, and a stage without it deploys with no lock
           discipline and no facing checklist                           PRE-04
    AC-38  the preflight fails when VERIFY.md's bytes changed - listing it is
           not enough, its hash has to match                            PRE-05
    AC-39  the preflight fails when a listed rig has MOVED into a subdirectory
           of models/ - matching on basename lets a rig that is no longer
           where BetterModel looks pass as present                      PRE-06
    AC-40  the preflight fails when models/ holds a subdirectory at all, empty
           included - the staged folder is flat or it is not this stage  PRE-07
    AC-41  a StageDir that REACHES a live plugins/BetterModel folder through a
           reparse point is refused with nothing written and nothing deleted -
           the destination guard cannot be lexical, because a junction's
           visible path says nothing about where it lands                SAFE-03
    AC-42  the preflight fails when models/ is itself a reparse point - a
           stage that can be retargeted between the check and the copy was
           never the thing that got checked                              PRE-08
    AC-43  the preflight fails when VERIFY.md is not a real leaf file     PRE-09
    AC-44  the preflight fails when any ANCESTOR of the stage is a reparse
           point, even with a perfectly normal stage directory - the two sides
           have to walk the same path, or the preflight validates one folder
           and the copy reads another                                    PRE-10
    AC-45  a destination whose path contains SQUARE BRACKETS is guarded like
           any other: a bracket-named junction into a live plugin folder is
           refused with ZERO create or change events in the target       SAFE-04
    AC-46  the same for a bracket-named live server root                 SAFE-05
    AC-47  a destination on a SUBSTITUTED drive root is refused with zero
           create/change/delete/rename events in the target and the sentinel
           preserved - a drive alias hides the segments, the reparse
           attribute and the server marker all at once                   SAFE-06
    AC-48  the preflight refuses a stage reached through a drive alias, for
           the same reason it refuses a reparse point                    PRE-11
    AC-49  a drive letter mapped to a SUBDIRECTORY of a real volume device
           (\Device\HarddiskVolumeN\some\path) is refused by both the stager
           and the preflight - "starts with a volume" is not "is a volume"
                                                                        SAFE-07

  Three criteria constrain THIS SUITE rather than the stager, because a fixture
  that damages the machine it runs on is a defect of the gate itself:

    AC-50  the free-drive-letter picker skips a letter that already has a DOS
           mapping even when that mapping's target is unavailable, and leaves
           it untouched - Test-Path is False for such a drive while
           QueryDosDevice still reports it                              PICK-01
    AC-51  the SUBST arm removes what it created and leaves the drive exactly
           as it found it                                              CLEAN-01
    AC-52  the raw DefineDosDevice arm does the same, removing with
           DDD_EXACT_MATCH_ON_REMOVE so it can only delete its own mapping,
           and checking the call succeeded                             CLEAN-02
    AC-53  the PICKER arm removes the alias IT created too - it makes its own
           mapping to demonstrate an occupied letter, and that mapping needs
           the same teardown contract as the other two                CLEAN-03
    AC-54  an alias survives no crash: a throw the instant the alias is live
           still removes it and restores the drive. All three arms share one
           lifetime helper, so this exercises the path all of them take
                                                                     CLEAN-04

  ---------------------------------------------------------------------------
  PROP MODE - AC-55..AC-66, added for slice PROP-STAGE.

  Requirement: the PROP-STAGE entry in LegendCraft/Plans/todo/slice-board.md,
  from the finding it enacts (LegendCraft/Plans/agent-findings.md, "deploy-rigs.ps1
  refuses props"). AC-9's origin-anchored 180-degree root yaw turns an authored
  +Z mob to face Minecraft's -Z. A prop - a banner planted in the ground, a ring
  on the floor, a glyph worn by a player - has no front, and every prop rig in the
  authoring tree carries an IDENTITY root by design. So all four hook props are
  refused as a batch with `nothing was staged`, and they reached mc-dev by hand,
  with no STAGE-READY manifest behind them.

  The mode is a DECLARED switch and never inferred from the file. Inferring it
  would delete the assertion: a mob rig whose 180-degree yaw was lost in
  authoring would then stage silently as a "prop", which is the exact defect
  AC-9 exists to catch. The caller states which kind of rig they are staging and
  the file has to agree.

    AC-55  -Prop stages a rig whose single top-level `root` bone is at the
           origin with an IDENTITY rotation [0,0,0]                    PROP-01
    AC-56  -Prop REFUSES a rig carrying the mob 180-degree root yaw, naming the
           rig - the two assertions are mutually exclusive, so a mob named in a
           prop run is caught rather than staged                       PROP-02
    AC-57  WITHOUT -Prop an identity-root prop is still refused, naming it - the
           reported defect, reproduced, and the mob rule unchanged     PROP-03
    AC-58  -Prop refuses a root that is not at the origin even when its rotation
           is identity - the anchor half of the assertion survives the swap
                                                                       PROP-04
    AC-59  a mixed batch under -Prop (one prop, one mob) stages NOTHING and
           names the mob - all-or-nothing holds across the new mode     PROP-05
    AC-60  every rule that is not the facing check still applies in prop mode:
           id agreement, an embedded PNG texture, and geometry         PROP-06
    AC-61  a -Prop stage has the same shape as a mob stage - models/ flat,
           VERIFY.md outside it, STAGE-READY listing both - and its own
           -Preflight passes on it                                     PROP-07
    AC-62  the prop runbook carries NO facing checklist and says why, while the
           mob runbook still carries one - a checklist item nobody can perform
           is worse than no checklist                                  PROP-08
    AC-63  -Prop defaults its stage directory to dist\props, so a prop run
           cannot silently replace the mob stage in dist\rigs - each kind gets
           a STAGE-READY of its own, which is what the finding asked for.
           Its CONTROL is the same run without the switch, which must still
           land in dist\rigs                                  PROP-09, PROP-09b
    AC-64  the JSON result carries `kind` = prop/mob per staged rig, and a prop's
           `facing` reads NOT-APPLICABLE rather than UNPROVEN - UNPROVEN says
           "nobody has checked", and for a prop there is nothing to check
                                                                       PROP-10
    AC-65  STAGE-READY records which mode wrote it, and the preflight reports
           that mode on success - INFORMATION, not a new refusal: both kinds are
           copied into the same plugins/BetterModel/models, so the mode does not
           change whether a stage is safe to copy                      PROP-11
    AC-66  -Preflight -Prop defaults to the prop stage directory, so the switch
           means the same thing on both sides of the tool              PROP-12

  Round 2 added AC-67..AC-70, one per reviewer finding F1 and F2. Both are about
  the same gap: -Prop introduced two operator-facing output branches that tell
  the caller what to do next, and no arm held either of them.

    AC-67  a mob-mode refusal that points the caller at -Prop points at a run
           that actually stages the rig - the hint is asserted, and so is the
           run it recommends                                           PROP-13
    AC-68  the same in the other direction: a -Prop refusal that says to drop
           the switch is followed by a mob-mode run that stages it     PROP-14
    AC-69  a root NEITHER mode would accept - one tilted on pitch or roll - gets
           NO hint from either mode. This is the F1 defect: $wellFormed omitted
           the rot[0]/rot[2] zero-checks that $yawOk requires, so the hint read
           the yaw alone and sent the caller on a run that could not succeed
                                                                       PROP-15
    AC-70  a STAGE-READY carrying no mode directive still preflights DEPLOYABLE
           and says it was written by an older stager - the backward-compatible
           branch the round-1 request claimed PROP-11 covered, when every stage
           PROP-11 builds is written by the new stager                  PROP-16

  PROP-03 is the regression reproduction: it asserts the defect as REPORTED (an
  identity-root prop refused by a mob-mode run) rather than a missing-switch
  error, so its red run is the bug and its green run is the bug still correctly
  refused - the mob rule is not what changed.

  PROP-09 and PROP-12 exercise a DEFAULT, so they cannot pass -StageDir. They
  run a COPY of the stager placed in a temp directory rather than the one in the
  repo: the defaults are relative to the script's own $PSScriptRoot, so the copy
  writes its dist\props into temp. A suite that reached into the repo to prove a
  default would be mutating the tree it is gating - the same rule PICK-01 and
  CLEAN-01..04 hold the drive-alias arms to.

  RED RUN: tests/RED-deploy-rigs-propstage.txt, captured with -Prop not yet a
  parameter. 58 passed, 11 failed, and the first failing assertion is

      FAIL  PROP-01  -Prop stages an identity-root rig the mob facing check
                     would refuse

  All 56 pre-existing arms stayed green across it, so the new fixture props
  moved nothing that was already covered. (56, not 54: the suite stood at 56
  assertions before this slice, which is what TOOLING.md carried and what the
  red run's 58 passed decomposes into - 56 pre-existing plus the two new arms
  that were green first.)

  TWO of the thirteen new arms were GREEN on that run, disclosed here rather
  than left to look like coverage:

  PROP-03 is the regression reproduction, and it reproduces behaviour that was
  already CORRECT - a mob-mode run refusing an identity-root prop is the defect
  as reported, and the fix must not loosen it. So it could only ever be green
  first. Its evidence is a MUTATION instead: make the mode inferred rather than
  declared (accept either root shape in either mode) and it goes red.
  tests/RED-deploy-rigs-propstage-declared.txt, 63 passed 6 failed - PROP-03
  with PROP-02 and PROP-05, and FAIL-06/ATOM-01/ATOM-03 alongside them, which is
  the point: inferring the mode does not add a prop rule, it deletes the mob one.

  PROP-09b is PROP-09's control and asserts the UNCHANGED mob default, so it was
  green by construction too. Mutation: default every run to dist\props.
  tests/RED-deploy-rigs-propstage-defaults.txt, 67 passed 2 failed - PROP-09b
  and PROP-12.

  ROUND 2 RED RUN: tests/RED-deploy-rigs-propstage-round2.txt, captured with
  AC-67..AC-70's four arms in place and the F1 defect still live.

      72 passed, 1 failed  (73 assertions)
      FAIL  PROP-15  a root neither mode accepts gets no hint from either mode

  PROP-15 is the F1 reproduction and the only one that could be red: $wellFormed
  read the yaw alone, so a root tilted on pitch or roll was told to swap the
  switch, and the swap refused it too. PROP-13, PROP-14 and PROP-16 were green
  first and are disclosed as such - 13 and 14 assert behaviour that was already
  correct for a well-formed root, and 16 covers a branch that existed but that
  no arm held (the round-1 request wrongly cited PROP-11 for it). Both carry
  mutation evidence:

    the whole wrong-mode hint removed -> tests/RED-deploy-rigs-propstage-hint.txt,
    71 passed 2 failed: PROP-13 and PROP-14. PROP-15 stays GREEN there, which is
    the right shape - "no hint" is what a tilted root is owed.

    the no-directive preflight line silenced ->
    tests/RED-deploy-rigs-propstage-nodirective.txt, 72 passed 1 failed: PROP-16.

  PROP-15 asserts the absence of a hint on a refusal that DID happen: each of its
  four reasons is required to name the rotation it refused, so a fixture that
  never reached the check cannot pass it by printing nothing.

  AC-7/AC-8 exist because BetterModel's own documentation does not state how a
  model id is derived from the file - the wiki gives the folder
  (plugins/BetterModel/models) and nothing more. Requiring stem, `name` and any
  non-empty `model_identifier` to AGREE makes the question moot: under agreement
  every candidate rule yields the same id.

  RED RUN: tests/RED-deploy-rigs.txt, captured with deploy-rigs.ps1 absent.
  Every assertion in it is red and the FIRST failing assertion is

      FAIL  STG-01  a staged rig is byte-identical to its source

  which is the shape of a suite whose subject does not exist yet. That is the
  honest record here: nothing was green on arrival because there was nothing to
  be green against.

  AC-19..AC-27 were added in review round 2, one per blocking finding. Their red
  run is tests/RED-deploy-rigs-review2.txt: 21 passed, 8 failed, FAIL-09 first.

  Review round 11 is entirely about this suite. Its drive-letter picker asked
  Test-Path alone, so a letter already mapped to an UNAVAILABLE target - Test-Path
  False, QueryDosDevice still reporting it - looked free, and the suite took it.
  In the reviewer's environment that false-failed two arms; on a machine where
  the picker then overwrote a mapping somebody depended on it would be worse than
  a false failure. The raw-alias teardown had the matching flaw: it removed with
  0x1|0x2, no DDD_EXACT_MATCH_ON_REMOVE, ignored the return value, and never
  looked at the drive afterwards, so it could not claim to have removed only its
  own mapping or to have removed it at all.

  A gate suite is allowed to be slow and it is allowed to be strict. It is not
  allowed to mutate the machine it runs on, and "it usually works" is not the
  bar for a fixture that manipulates DOS device names. PICK-01, CLEAN-01 and
  CLEAN-02 hold the suite to the standard the stager is held to.

  Their evidence is a MUTATION, disclosed as such: all three guard the fixture,
  and the fixture is what changed, so there is no pre-fix run of the suite in
  which they existed. tests/RED-deploy-rigs-review11.txt is a copy of this file
  with three cuts - the picker's DOS-target check removed, the SUBST teardown
  removed, and the raw removal aimed at a target this arm never created. All
  three assertions go red, 51 passed 3 failed, and nothing else moves.

  That run also demonstrated the failure it exists to prevent: with the teardown
  cut, it left an R: mapping behind, and CLEAN-01 is what named it.

  Round 12 closed the hole in that same fix. CLEAN-01 and CLEAN-02 covered the
  two aliases the SAFE arms create - and PICK-01 creates a THIRD, to demonstrate
  an occupied letter, which nothing covered. Its removal sat outside a
  try/finally with its result unchecked, and its assertion read values captured
  before cleanup, so cutting that one line left the suite reporting all-green
  while leaking a DOS mapping onto the machine. Three arms create aliases;
  three assertions now hold them, and each arm's alias lives inside a
  try/finally whose removal result is captured and whose post-state is compared
  against what it recorded going in. The rule, since it took two rounds to get
  right: whoever creates the alias owns proving it is gone, and "the other arm's
  cleanup assertion passed" is not that proof.

  Round 13 fixed the third try at this, and stopped writing the rule three
  times. Each arm still created its alias and checked its target OUTSIDE the try,
  and took its cleanup obligation from a QUERY rather than from the create call -
  so a throw in between, or in the visibility check, left a process-global drive
  alias behind with finally never entered or its flag still false. The happy path
  was covered; the exception path try/finally exists for was not.

  Use-DriveAlias is now the one lifetime, and all three arms are call sites:
  create inside the try, obligation taken from the create call's own result and
  nothing else, target and body after it where finally still covers them.
  CLEAN-04 exercises the crash path directly - a body that throws the instant the
  alias is live - and because the arms share the helper, it covers the path all
  of them take. That is the same fix shape as round 7's shared ancestor walk: the
  third time a rule needed enforcing in three places was the point to stop
  enforcing it in three places.

  Review round 10 changed two things. AC-49 covers a drive letter mapped to a
  SUBDIRECTORY of a real volume device - \Device\HarddiskVolume3\fake\plugins\
  BetterModel - which the round-9 guard accepted because it tested a PREFIX.
  "Starts with a volume" is not "is a volume"; the check is anchored now.

  The second change is to this suite, and it matters more. SAFE-06 and PRE-11
  were FALSE GREEN: they asserted a non-zero exit, an intact sentinel and zero
  writes, all of which a raw "Cannot find drive" exception satisfies just as
  well as a working guard - and in the reviewer's environment that is exactly
  what happened, because PowerShell caches its drive list and never saw the new
  mapping. A guard that had been deleted entirely would have passed those arms.

  So every drive-alias arm now (a) proves the mapping is visible to the process
  that runs the stager before asserting anything, failing loudly if it is not,
  and (b) requires the REFUSAL REASON - a per-rig JSON failure naming the alias
  for the stager, the same text on the preflight's own output. The general
  lesson is the one this suite keeps re-learning: an assertion that something
  did not happen must also prove the thing that would have made it happen was
  actually set up. "It refused" is not a finding unless you know it was asked.
  Red run: tests/RED-deploy-rigs-review10.txt.

  AC-47..AC-48 were added in review round 9, and they close the last shape of
  the same hole: `subst R: <fake server>\plugins\BetterModel` gives a
  destination that is not a reparse point, spells no plugin segments, and
  exposes no parent above the mapping - so all three guards saw a clean local
  path and the run deleted the live rig and promoted a stage over it. A drive
  alias hides everything a path-based guard can look at, at once.

  The rule is now: the stage's drive root must be a plain local volume.
  QueryDosDevice answers that directly - a real volume maps to
  \Device\HarddiskVolumeN, a SUBST maps to \??\<path>, a network drive to a
  redirector - and anything that is not a plain volume is refused rather than
  resolved, on BOTH sides. Resolving the alias and re-checking was the other
  option; refusing is chosen because the alias can be re-pointed after the check
  either way, which is the same argument that already refuses reparse points.
  If the check itself cannot run, that is also a refusal: a destination whose
  nature cannot be established is not one to write into.

  BOTH sides deliberately, though only the write guard was blocking. A rule the
  preflight and the writer enforce differently is exactly the round-7 defect,
  and it is cheaper to not build it twice than to have it found twice.
  Red run: tests/RED-deploy-rigs-review9.txt.

  AC-45..AC-46 were added in review round 8, and they change how the SAFE arms
  are judged. `Test-Path -Path` treats square brackets as a WILDCARD, so a legal
  Windows directory literally named `[handoff]` reported as absent - and every
  guard reading it waved the destination through. Worse, the old SAFE arms could
  not have caught it: they asserted that the sentinel SURVIVED, and the run did
  its damage in a temp folder it cleaned up on the way out. A guard that fails
  and then tidies up looks identical to a guard that held.

  So the SAFE arms now watch the target with a FileSystemWatcher and assert
  ZERO create/change events inside it - "nothing was written" rather than
  "nothing is left". SAFE-01 and SAFE-03 were strengthened the same way rather
  than left as the weaker form beside the new ones.

  The fix is -LiteralPath everywhere a caller-supplied path reaches the
  filesystem, and .NET APIs (File.Copy, Directory.Move, Directory.CreateDirectory)
  where the cmdlet has no literal form. The rule going in: a path that came from
  outside this script is DATA, never a pattern.

  THIS SUITE HAD THE SAME BUG, and it is worth knowing about. New-Junction
  confirmed its own work with a non-literal Test-Path, so creating a junction
  named "[handoff]" reported failure - and SAFE-04's first red was the helper
  saying "could not create a junction", not the stager doing anything wrong. The
  else-branch that fails loudly instead of skipping is the only reason that was
  visible at all. tests/RED-deploy-rigs-review8.txt is therefore NOT that first
  capture, which proved nothing: it is the suite with the helper fixed, run
  against a mutant whose Test-PathLiteral is wildcard-aware again. SAFE-04 and
  SAFE-05 go red there, 46 passed 2 failed, which is the claim being made.

  AC-44 was added in review round 7. Round 6 fixed the write path properly - an
  ancestor WALK - and the preflight only shallowly, a leaf check, so the two
  sides no longer agreed on what they were looking at. A normal stage directory
  under a junctioned parent passed the preflight and was refused by staging, and
  an ancestor retargeted between the two would have the preflight validate one
  folder while the copy reads another. Both sides now call the same
  Get-ReparseAncestor. The lesson is the shape of the bug, not the bug: a rule
  enforced in two places is a rule that will disagree with itself, and this one
  did so within a single round of fixing it.
  Red run: tests/RED-deploy-rigs-review7.txt.

  AC-41..AC-43 were added in review round 6, from two blocking findings with one
  root: every path check in here was LEXICAL or one level too shallow, and a
  reparse point makes a path's spelling say nothing about where it lands. A
  junction called something innocuous can land inside a live plugins/BetterModel
  folder, and the guard reading its name would wave it through - the exact
  server touch this slice exists to make impossible. The same hole ran the other
  way in the preflight: it inspected the entries INSIDE models/ without ever
  asking what models/ itself was, so a stage whose models/ was a junction to an
  external folder passed, and could be re-pointed between the check and the copy.
  Both guards now refuse a reparse point outright rather than resolving and
  following it, which is the safer direction for a tool whose whole promise is
  that it never touches a server.

  PRE-09 passed on arrival, disclosed: a VERIFY.md replaced by a junction is a
  directory, so it already failed the -PathType Leaf test and was reported
  missing. It constrains the FIX - adding reparse handling must not start
  accepting a directory there - rather than the old behaviour.

  Round 5's disclosure that the reparse-point branch was "proven only through
  the directory arm" is RETIRED, and the assumption behind it was wrong: a
  junction (`mklink /J`) needs no privileges here, so the branch was testable
  all along. SAFE-03, PRE-08 and PRE-09 create real junctions.
  Red run: tests/RED-deploy-rigs-review6.txt.

  AC-37..AC-40 were added in review round 5, from two blocking findings that
  are both the same omission: the readiness manifest described the rigs and
  nothing else, so the preflight answered a narrower question than the one it
  appears to answer. VERIFY.md - the deploy-lock runbook and the facing
  checklist, which is half the point of MM-P3 - was not in the manifest at all,
  so deleting it left a stage reading DEPLOYABLE. And models/ was enumerated
  RECURSIVELY and keyed by basename, so moving a rig into models/nested/ kept
  its name and hash and passed, while the flat folder BetterModel actually reads
  no longer held it. The manifest now lists root-relative paths - `models/<rig>`
  and `VERIFY.md` - and models/ is enumerated one level deep with anything that
  is not a plain file rejected outright.
  Red run: tests/RED-deploy-rigs-review5.txt.

  AC-32..AC-36 were added in review round 4, from one blocking finding that is
  the previous round's fix taken one step further: round 3 made STAGE-READY the
  thing cleanup removes FIRST, which quietly assumed the marker is always
  deletable. Lock it open and a refusal deletes models/ and VERIFY.md while the
  marker survives, so a stage with no rigs in it reads as ready to copy - and
  the refusal text said the marker was gone without having checked. Readiness
  now fails CLOSED: a STAGE-INVALID tombstone is written before any cleanup or
  promotion and removed only as the last action of a verified success, and
  "deployable" is decided by an executable preflight (READY present, INVALID
  absent, and models/ matching the marker name for name and hash for hash)
  rather than by a file existing. Red run: tests/RED-deploy-rigs-review4.txt -
  34 passed, 4 failed, READY-01 first.

  PRE-02 was VACUOUSLY green in that run and is disclosed as such: with no
  -Preflight switch to bind to, every preflight invocation failed, so "the
  preflight rejects a tampered stage" was true for the wrong reason. What makes
  it real is its pairing with PRE-01 on the finished code - the same command
  exits 0 on an untouched stage and non-zero once a staged rig's bytes change or
  an unlisted file appears. A test that can only ever fail proves nothing; this
  one now has both arms.

  The first attempt at PRE-03 was also green for the wrong reason, and that one
  was the FIXTURE's fault rather than the code's: the stage directory was named
  "stage-preflight", the stager prints the stage path into VERIFY.md, and a
  case-insensitive -match on "-Preflight" found the directory name. It is now
  named stage-readycheck and the assertion is case-sensitive on the command
  form. Worth remembering when asserting that generated text mentions something:
  the generated text also contains the paths you made up.

  AC-28..AC-31 were added in review round 3, one per blocking finding, both of
  them found by REPRODUCTION again. Their red run is
  tests/RED-deploy-rigs-review3.txt. The two defects were the same shape twice:
  a check that reports success on the strength of a call that did not throw.
  Cleanup swallowed its deletion errors and never looked to see whether the
  files were gone, so a locked rig survived a refusal in silence; and
  FromBase64String returning without throwing was read as "this is a texture",
  which an empty payload and four bytes of zero both satisfy.

  ATOM-04's red in that file was reached with a WEAKER injection than the one it
  now carries (a file parked at the temp folder's path), which the fix then made
  harmless by cleaning a stale temp folder before use. Its evidence is therefore
  a mutation, recorded in tests/RED-deploy-rigs-atom04.txt: delete the
  Remove-OwnedStage call from the write-phase catch and ATOM-04 goes red alone,
  28 passed 1 failed. That proves the arm bites the guard it names. It does not
  prove it went red before the guard existed, and nothing here should be read as
  claiming otherwise.

  ONE of the nine, SRC-02, PASSED on arrival and that is disclosed rather than
  smoothed over. A source root that is a file rather than a directory already
  produced one named failure per rig, because enumerating a file yields nothing
  and every rig then reports "not found". SRC-02 exists to constrain the FIX:
  the obvious repair for SRC-01 is to throw early on a bad source root, which
  would take SRC-02's per-rig naming with it. Its non-vacuity is that it fails
  the moment the fix over-narrows, not that it failed before the fix.

  The three that matter most are the ones review found by REPRODUCTION rather
  than by reading -
  ATOM-03 (a refused run left alpha, beta and a stale VERIFY.md deployable) and
  SAFE-01/SAFE-02 (nothing stopped a caller from pointing -StageDir at a live
  plugins/BetterModel folder, which the script would then wipe and rewrite -
  outside the deploy lock, from a script whose whole premise is that it never
  touches a server).

  AC-18 was added after the other seventeen were green, from a defect found
  running the stager for real: `powershell -File deploy-rigs.ps1 -Rig a,b`
  binds ONE string, and the rig list came back as a single unfindable name. Its
  own red run is tests/RED-deploy-rigs-comma.txt - RIG-01 red, the other
  eighteen green, which is what a genuine one-defect regression looks like.

  ATOM-01's "nothing was staged" arm is an absence, and an absence is
  indistinguishable from a fixture that never fired. Its control is STG-01/
  STG-02 on the SAME fixture rigs: they stage when the bad rig is not requested,
  so an empty models/ in ATOM-01 is the guard firing rather than the stager
  failing to run.
#>
[CmdletBinding()]
param(
    [switch]$KeepFixture,
    [string]$StagerPath
)

$ErrorActionPreference = 'Stop'

$Stager = Join-Path (Split-Path $PSScriptRoot -Parent) 'deploy-rigs.ps1'
if ($StagerPath) { $Stager = $StagerPath }

$script:Pass = 0
$script:Fail = 0

function Assert {
    param([string]$Id, [string]$What, [bool]$Condition)
    if ($Condition) { $script:Pass++; Write-Host "  PASS  $Id  $What" }
    else { $script:Fail++; Write-Host "  FAIL  $Id  $What" -ForegroundColor Red }
}

function Write-Utf8 {
    param([string]$Path, [string]$Text)
    $null = New-Item -ItemType Directory -Force (Split-Path $Path -Parent)
    [System.IO.File]::WriteAllText($Path, $Text, (New-Object System.Text.UTF8Encoding($false)))
}

# ---------------------------------------------------------------------------
# The fixture. One hand-written .bbmodel per rule, so a failing assertion names
# exactly one defect.
# ---------------------------------------------------------------------------

function New-Bbmodel {
    param(
        [string]$Name,
        [string]$Identifier = '',
        [object[]]$RootRotation = @(0, 180, 0),
        [object[]]$RootOrigin = @(0, 0, 0),
        [int]$Textures = 1,
        [int]$Elements = 2,
        [string[]]$Animations = @('idle', 'walk'),
        [string]$TextureSource = 'data:image/png;base64,iVBORw0KGgo='
    )
    $model = [ordered]@{
        meta              = [ordered]@{ format_version = '4.10'; model_format = 'free'; box_uv = $false }
        name              = $Name
        model_identifier  = $Identifier
        resolution        = [ordered]@{ width = 32; height = 32 }
        elements          = @(1..$Elements | ForEach-Object { [ordered]@{ name = "cube$_"; from = @(0, 0, 0); to = @(1, 1, 1); uuid = "e$_" } })
        outliner          = @(
            [ordered]@{
                name     = 'root'
                origin   = $RootOrigin
                rotation = $RootRotation
                uuid     = 'root-uuid'
                children = @('e1')
            }
        )
        textures          = @(1..16 | Where-Object { $_ -le $Textures } | ForEach-Object {
                [ordered]@{ name = "tex$_.png"; id = "$($_ - 1)"; source = $TextureSource } })
        animations        = @($Animations | ForEach-Object { [ordered]@{ name = $_; loop = 'loop'; length = 1.0; animators = @{} } })
    }
    if ($Elements -eq 0) { $model.elements = @() }
    if ($Textures -eq 0) { $model.textures = @() }
    ConvertTo-Json $model -Depth 8
}

function New-Fixture {
    param([string]$Root)

    if (Test-Path $Root) { Remove-Item $Root -Recurse -Force }
    $null = New-Item -ItemType Directory -Force $Root

    Write-Utf8 (Join-Path $Root 'mobs\good\alpha.bbmodel') (New-Bbmodel -Name 'alpha' -Animations @('idle', 'walk', 'attack'))
    Write-Utf8 (Join-Path $Root 'mobs\good\beta.bbmodel')  (New-Bbmodel -Name 'beta')
    Write-Utf8 (Join-Path $Root 'mobs\summons\bone_colossus.bbmodel') (New-Bbmodel -Name 'bone_colossus' -Identifier 'bone_colossus')

    # one rejection rule per file
    Write-Utf8 (Join-Path $Root 'mobs\bad\badjson.bbmodel')      '{ "meta": { this is not json'
    Write-Utf8 (Join-Path $Root 'mobs\bad\namemismatch.bbmodel') (New-Bbmodel -Name 'somethingelse')
    Write-Utf8 (Join-Path $Root 'mobs\bad\identmismatch.bbmodel') (New-Bbmodel -Name 'identmismatch' -Identifier 'other_id')
    Write-Utf8 (Join-Path $Root 'mobs\bad\noyaw.bbmodel')        (New-Bbmodel -Name 'noyaw' -RootRotation @(0, 0, 0))
    Write-Utf8 (Join-Path $Root 'mobs\bad\notex.bbmodel')        (New-Bbmodel -Name 'notex' -Textures 0)
    Write-Utf8 (Join-Path $Root 'mobs\bad\noelem.bbmodel')       (New-Bbmodel -Name 'noelem' -Elements 0)

    Write-Utf8 (Join-Path $Root 'mobs\bad\filetex.bbmodel') (New-Bbmodel -Name 'filetex' -TextureSource 'C:\Users\artist\work\filetex.png')
    Write-Utf8 (Join-Path $Root 'mobs\bad\junktex.bbmodel') (New-Bbmodel -Name 'junktex' -TextureSource 'data:image/png;base64,not!valid!base64!')
    Write-Utf8 (Join-Path $Root 'mobs\bad\emptytex.bbmodel') (New-Bbmodel -Name 'emptytex' -TextureSource 'data:image/png;base64,')
    Write-Utf8 (Join-Path $Root 'mobs\bad\nonpngtex.bbmodel') (New-Bbmodel -Name 'nonpngtex' -TextureSource 'data:image/png;base64,AAAA')

    # the same stem in two folders - ambiguous by construction
    Write-Utf8 (Join-Path $Root 'mobs\dupa\dup.bbmodel') (New-Bbmodel -Name 'dup')
    Write-Utf8 (Join-Path $Root 'mobs\dupb\dup.bbmodel') (New-Bbmodel -Name 'dup')

    # Props. Identity root, because a prop has no front - the shape every rig
    # under props/ in the authoring tree actually has. `pring` mirrors fx_ring
    # (one element, one clip); `pbanner` mirrors knight_war_banner.
    Write-Utf8 (Join-Path $Root 'props\pring.bbmodel')   (New-Bbmodel -Name 'pring' -RootRotation @(0, 0, 0) -Elements 1 -Animations @('idle'))
    Write-Utf8 (Join-Path $Root 'props\pbanner.bbmodel') (New-Bbmodel -Name 'pbanner' -RootRotation @(0, 0, 0) -Animations @('plant', 'idle', 'expire'))

    # one prop rejection rule per file, and none of them is about facing
    Write-Utf8 (Join-Path $Root 'props\bad\poffroot.bbmodel')  (New-Bbmodel -Name 'poffroot' -RootRotation @(0, 0, 0) -RootOrigin @(0, 8, 0))
    Write-Utf8 (Join-Path $Root 'props\bad\pnotex.bbmodel')    (New-Bbmodel -Name 'pnotex' -RootRotation @(0, 0, 0) -Textures 0)
    Write-Utf8 (Join-Path $Root 'props\bad\pnoelem.bbmodel')   (New-Bbmodel -Name 'pnoelem' -RootRotation @(0, 0, 0) -Elements 0)
    Write-Utf8 (Join-Path $Root 'props\bad\pidentbad.bbmodel') (New-Bbmodel -Name 'pidentbad' -RootRotation @(0, 0, 0) -Identifier 'other_id')

    # Roots NEITHER mode accepts: the yaw is one mode's, the pitch is nobody's.
    # These are what the wrong-mode HINT has to stay silent about - it reads the
    # yaw, and the yaw alone does not decide whether the other mode would stage
    # the rig.
    Write-Utf8 (Join-Path $Root 'props\bad\ptiltprop.bbmodel') (New-Bbmodel -Name 'ptiltprop' -RootRotation @(10, 0, 0))
    Write-Utf8 (Join-Path $Root 'props\bad\ptiltmob.bbmodel')  (New-Bbmodel -Name 'ptiltmob' -RootRotation @(10, 180, 0))
}

function Invoke-Stager {
    param(
        [string]$Source,
        [string]$Stage,
        [string[]]$Rig,
        [switch]$Prop,
        # PROP-09 proves a DEFAULT, so it must not pass -StageDir at all.
        [switch]$DefaultStage,
        [string]$UseStager
    )
    $script:LastExit = $null
    $out = $null
    $exe = if ($UseStager) { $UseStager } else { $Stager }
    # A HASHTABLE splat, never an array one: splatted array elements are passed
    # positionally, so `-StageDir` would arrive as a value rather than as a
    # parameter name and every arm would fail for the wrong reason.
    $extra = @{}
    if ($Prop) { $extra['Prop'] = $true }
    if (-not $DefaultStage) { $extra['StageDir'] = $Stage }
    try {
        $out = & $exe -SourceRoot $Source -Rig $Rig -Json @extra 2>&1
        $script:LastExit = $LASTEXITCODE
    }
    catch {
        Write-Host "  (stager threw: $($_.Exception.Message.Split([char]10)[0]))"
        $script:LastExit = 1
        return $null
    }
    $text = ($out | Out-String).Trim()
    if (-not $text) { return $null }
    try { return $text | ConvertFrom-Json }
    catch {
        Write-Host "  (stager output is not JSON: $($text.Split([char]10)[0]))"
        return $null
    }
}

# The preflight writes nothing and answers with its exit code, so the tests read
# that rather than parsing a result.
function Invoke-Preflight {
    param([string]$Stage, [switch]$Prop)
    return (Invoke-PreflightDetail -Stage $Stage -Prop:$Prop).exit
}

# The exit code alone cannot tell a refusal apart from a crash, so the arms that
# care read the text too.
function Invoke-PreflightDetail {
    param(
        [string]$Stage,
        [switch]$Prop,
        # PROP-12 proves a DEFAULT, so it must not pass -StageDir at all.
        [switch]$DefaultStage,
        [string]$UseStager
    )
    $text = ''
    $code = 1
    $exe = if ($UseStager) { $UseStager } else { $Stager }
    $extra = @{}
    if ($Prop) { $extra['Prop'] = $true }
    if (-not $DefaultStage) { $extra['StageDir'] = $Stage }
    try {
        $out = & $exe -Preflight @extra *>&1
        $code = $LASTEXITCODE
        $text = ($out | Out-String)
    }
    catch { $text = $_.Exception.Message; $code = 1 }
    return @{ exit = $code; text = $text }
}

# Drive-alias plumbing. A separate namespace from the stager's own, and guarded
# on the type already existing, because the suite and the script share a process.
if (-not ('LcTestNative.Dos' -as [type])) {
    Add-Type -Namespace LcTestNative -Name Dos -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern uint QueryDosDevice(string lpDeviceName, System.Text.StringBuilder lpTargetPath, uint ucchMax);
[DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern bool DefineDosDevice(uint dwFlags, string lpDeviceName, string lpTargetPath);
'@
}
$DDD_RAW_TARGET_PATH        = 0x1
$DDD_REMOVE_DEFINITION      = 0x2
$DDD_EXACT_MATCH_ON_REMOVE  = 0x4   # delete only OUR mapping, never a prefix match

function Get-DosTarget {
    param([string]$Letter)
    $sb = New-Object System.Text.StringBuilder 1024
    if ([LcTestNative.Dos]::QueryDosDevice($Letter, $sb, 1024) -eq 0) { return '' }
    return $sb.ToString()
}

# A letter is free only when NOTHING claims it. Test-Path alone is not enough: a
# drive mapped to an unavailable target answers False while QueryDosDevice still
# reports the mapping, and taking that letter would overwrite somebody's alias.
function Get-FreeDriveLetter {
    foreach ($c in [char[]]'RSTUVWXY') {
        $d = "${c}:"
        if (Test-Path -LiteralPath $d) { continue }
        if (Get-DosTarget $d) { continue }
        return $d
    }
    return $null
}

# A mapping is only evidence if the process that runs the stager can SEE it.
# PowerShell caches its drive list, so a mapping made after startup is invisible
# until the provider is re-enumerated - and a stager that then dies on "Cannot
# find drive" satisfies every "it refused" assertion without the guard running.
function Confirm-DriveVisible {
    param([string]$Letter, [string]$ExpectLike)
    Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue | Out-Null
    $target = Get-DosTarget $Letter
    return ([System.IO.Directory]::Exists("$Letter\") -and
            (Test-Path -LiteralPath "$Letter\") -and
            $target -like $ExpectLike)
}

# ONE alias lifetime, used by every arm that creates a drive alias.
#
# The shape is the whole point and it is why this is a function rather than a
# pattern repeated three times: the create call happens INSIDE the try, the
# cleanup obligation is taken from that call's own result and from nothing else,
# and every fallible thing after it - the target query, the visibility check, the
# arm's body - runs where finally still covers it. Deriving the obligation from a
# query instead means a throw between create and query leaks a process-global
# drive alias, and doing any of it before the try means finally never runs at all.
#
# Returns what the caller needs to assert on; it never throws.
function Use-DriveAlias {
    param(
        [string]$Letter,
        [scriptblock]$Create,          # MUST return $true only if the create call succeeded
        [string]$ExpectedTarget,       # what QueryDosDevice must report before the alias is used
        [scriptblock]$Remove,          # MUST return $true only if the removal call succeeded
        [scriptblock]$Body
    )
    $prior = Get-DosTarget $Letter
    $created = $false
    $removed = $false
    $targetOk = $false
    $threw = $null
    try {
        $created = [bool](& $Create)
        if ($created) {
            $targetOk = ((Get-DosTarget $Letter) -eq $ExpectedTarget)
            if ($targetOk) { & $Body }
        }
    }
    catch { $threw = $_.Exception.Message }
    finally {
        if ($created) { $removed = [bool](& $Remove) }
    }
    return @{
        prior    = $prior
        created  = $created
        removed  = $removed
        targetOk = $targetOk
        threw    = $threw
        restored = ((Get-DosTarget $Letter) -eq $prior)
    }
}

# A directory junction needs no privileges, which is exactly why the guards
# cannot trust a path's spelling.
function New-Junction {
    param([string]$Link, [string]$Target)
    $null = [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($Link))
    cmd /c mklink /J "$Link" "$Target" | Out-Null
    # -LiteralPath, or a link named "[handoff]" reports as absent and this
    # helper claims it could not create the junction it just created. The bug
    # under test caught this suite first.
    return (Test-Path -LiteralPath $Link)
}

# "Nothing is left" and "nothing was written" are different claims, and a run
# that writes into a server and then cleans up satisfies only the first. This
# watches the target for the duration and counts every create/change under it.
function Measure-TargetWrites {
    param([string]$Watch, [scriptblock]$Action)

    Get-EventSubscriber -SourceIdentifier 'lcw-*' -ErrorAction SilentlyContinue | Unregister-Event -Force
    Get-Event -SourceIdentifier 'lcw-*' -ErrorAction SilentlyContinue | Remove-Event

    $fsw = New-Object System.IO.FileSystemWatcher
    $fsw.Path = $Watch
    $fsw.IncludeSubdirectories = $true
    $fsw.NotifyFilter = ([System.IO.NotifyFilters]::FileName -bor
        [System.IO.NotifyFilters]::DirectoryName -bor
        [System.IO.NotifyFilters]::LastWrite)
    $null = Register-ObjectEvent $fsw Created -SourceIdentifier 'lcw-created'
    $null = Register-ObjectEvent $fsw Changed -SourceIdentifier 'lcw-changed'
    $null = Register-ObjectEvent $fsw Deleted -SourceIdentifier 'lcw-deleted'
    $null = Register-ObjectEvent $fsw Renamed -SourceIdentifier 'lcw-renamed'
    $fsw.EnableRaisingEvents = $true
    try { & $Action }
    finally {
        Start-Sleep -Milliseconds 500   # let the watcher drain before we judge it
        $fsw.EnableRaisingEvents = $false
    }
    $count = @(Get-Event -ErrorAction SilentlyContinue | Where-Object { $_.SourceIdentifier -like 'lcw-*' }).Count
    Get-EventSubscriber -SourceIdentifier 'lcw-*' -ErrorAction SilentlyContinue | Unregister-Event -Force
    Get-Event -SourceIdentifier 'lcw-*' -ErrorAction SilentlyContinue | Remove-Event
    $fsw.Dispose()
    return $count
}

function Sha1Of {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return '' }
    (Get-FileHash -Algorithm SHA1 -Path $Path).Hash.ToLower()
}

# `,@()` is deliberate elsewhere; here a plain filter is enough because every
# caller counts rather than indexes.
function FailedRigs {
    param($Result)
    if (-not $Result) { return @() }
    @($Result.failures | ForEach-Object { $_.rig })
}

function StagedRigs {
    param($Result)
    if (-not $Result) { return @() }
    @($Result.staged | ForEach-Object { $_.rig })
}

# ---------------------------------------------------------------------------

$fixtureRoot = Join-Path ([System.IO.Path]::GetTempPath()) 'lc-deploy-rigs-tests'
$sourceRoot = Join-Path $fixtureRoot 'mobs-src'
$stageRoot = Join-Path $fixtureRoot 'stage'

Write-Host ''
Write-Host "deploy-rigs contract tests"
Write-Host "  stager  : $Stager"
Write-Host "  fixture : $fixtureRoot"
Write-Host ''

New-Fixture -Root $sourceRoot

# --- STG: what a good stage puts on disk ----------------------------------
Write-Host 'STG  staged output shape'

$r = Invoke-Stager -Source $sourceRoot -Stage $stageRoot -Rig @('alpha', 'beta', 'bone_colossus')
$modelsDir = Join-Path $stageRoot 'models'

Assert 'STG-01' 'a staged rig is byte-identical to its source' (
    (Sha1Of (Join-Path $modelsDir 'alpha.bbmodel')) -ne '' -and
    (Sha1Of (Join-Path $modelsDir 'alpha.bbmodel')) -eq (Sha1Of (Join-Path $sourceRoot 'mobs\good\alpha.bbmodel')))

$staged = @(Get-ChildItem -Path $modelsDir -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.Name } | Sort-Object)
Assert 'STG-02' 'models/ holds exactly the requested rigs, flat, and nothing else' (
    ($staged -join ',') -eq 'alpha.bbmodel,beta.bbmodel,bone_colossus.bbmodel')

Assert 'STG-03' 'the verification list is written outside models/' (
    (Test-Path (Join-Path $stageRoot 'VERIFY.md')) -and
    -not (Test-Path (Join-Path $modelsDir 'VERIFY.md')))

# --- FAIL: every rejection is loud and names the rig -----------------------
Write-Host ''
Write-Host 'FAIL  rejection rules'

$cases = @(
    @{ Id = 'FAIL-01'; Rig = 'nosuchrig';     What = 'a rig with no .bbmodel fails, naming it' }
    @{ Id = 'FAIL-02'; Rig = 'dup';           What = 'an ambiguous rig name fails, naming it'  }
    @{ Id = 'FAIL-03'; Rig = 'badjson';       What = 'unparseable JSON fails, naming it'       }
    @{ Id = 'FAIL-04'; Rig = 'namemismatch';  What = 'name != filename stem fails, naming it'  }
    @{ Id = 'FAIL-05'; Rig = 'identmismatch'; What = 'model_identifier != stem fails, naming it' }
    @{ Id = 'FAIL-06'; Rig = 'noyaw';         What = 'a missing 180-degree root yaw fails, naming it' }
    @{ Id = 'FAIL-07'; Rig = 'notex';         What = 'no embedded texture fails, naming it'    }
    @{ Id = 'FAIL-08'; Rig = 'noelem';        What = 'no elements fails, naming it'            }
    @{ Id = 'FAIL-09'; Rig = 'filetex';       What = 'a texture source that is not a data: URI fails, naming it' }
    @{ Id = 'FAIL-10'; Rig = 'junktex';       What = 'a texture payload that does not decode fails, naming it'   }
    @{ Id = 'FAIL-11'; Rig = 'emptytex';      What = 'an empty base64 payload fails, naming it'                  }
    @{ Id = 'FAIL-12'; Rig = 'nonpngtex';     What = 'a payload that decodes but is not a PNG fails, naming it'  }
)

foreach ($c in $cases) {
    $stage = Join-Path $fixtureRoot ("stage-" + $c.Id)
    $res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @($c.Rig)
    $named = (FailedRigs $res) -contains $c.Rig
    Assert $c.Id $c.What ($named -and $script:LastExit -ne 0)
}

# FAIL-02 additionally names every path it matched - "ambiguous" is useless
# without saying which two files.
$stage = Join-Path $fixtureRoot 'stage-dup-detail'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('dup')
$reason = ($res.failures | Where-Object { $_.rig -eq 'dup' } | ForEach-Object { $_.reason }) -join ' '
Assert 'FAIL-02b' 'the ambiguous-rig failure names both matching paths' (
    $reason -match 'dupa' -and $reason -match 'dupb')

# FAIL-04 additionally names both values, so the fix is obvious from the report.
$stage = Join-Path $fixtureRoot 'stage-name-detail'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('namemismatch')
$reason = ($res.failures | Where-Object { $_.rig -eq 'namemismatch' } | ForEach-Object { $_.reason }) -join ' '
Assert 'FAIL-04b' 'the name-mismatch failure names both the stem and the internal name' (
    $reason -match 'namemismatch' -and $reason -match 'somethingelse')

# --- ATOM: all-or-nothing -------------------------------------------------
Write-Host ''
Write-Host 'ATOM  all-or-nothing staging'

$stage = Join-Path $fixtureRoot 'stage-atom'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'noyaw', 'notex', 'beta')
$stagedFiles = @(Get-ChildItem -Path (Join-Path $stage 'models') -File -Recurse -ErrorAction SilentlyContinue)
$failed = FailedRigs $res
Assert 'ATOM-01' 'one bad rig stages none of them, and every failing rig is reported' (
    $stagedFiles.Count -eq 0 -and
    $script:LastExit -ne 0 -and
    ($failed -contains 'noyaw') -and ($failed -contains 'notex') -and
    (StagedRigs $res).Count -eq 0)

$stage = Join-Path $fixtureRoot 'stage-atom-ok'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'beta')
Assert 'ATOM-02' 'an all-good run exits 0 and reports every rig staged' (
    $script:LastExit -eq 0 -and
    ((StagedRigs $res) -join ',') -eq 'alpha,beta' -and
    (FailedRigs $res).Count -eq 0)

# A refused run that leaves the PREVIOUS stage on disk is the dangerous shape:
# the owner copies a folder the script has already rejected.
$stage = Join-Path $fixtureRoot 'stage-stale'
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'beta')
$stagedBefore = @(Get-ChildItem -Path (Join-Path $stage 'models') -File -ErrorAction SilentlyContinue).Count
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('noyaw')
$leftOver = @(Get-ChildItem -Path (Join-Path $stage 'models') -File -Recurse -ErrorAction SilentlyContinue)
Assert 'ATOM-03' 'a refused run invalidates the models/ and VERIFY.md a previous run left' (
    $stagedBefore -eq 2 -and
    $script:LastExit -ne 0 -and
    $leftOver.Count -eq 0 -and
    -not (Test-Path (Join-Path $stage 'VERIFY.md')))

# The write phase builds into a sibling temp folder and promotes it only once
# every write has succeeded. An undeletable file inside that folder - a handle
# opened with no sharing, which is what a crashed editor or a virus scanner
# looks like - is a deterministic failure inside the write phase.
$stage = Join-Path $fixtureRoot 'stage-latefail'
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'beta')
$tmp = Join-Path $stage '.deploy-rigs-tmp'
Write-Utf8 (Join-Path $tmp 'blocked.bin') 'held open by another process'
$held = [System.IO.File]::Open((Join-Path $tmp 'blocked.bin'), 'Open', 'Read', 'None')
try {
    $res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha')
}
finally {
    $held.Dispose()
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
$leftOver = @(Get-ChildItem -Path (Join-Path $stage 'models') -File -Recurse -ErrorAction SilentlyContinue)
Assert 'ATOM-04' 'a write-phase failure promotes nothing and invalidates the previous stage' (
    $script:LastExit -ne 0 -and
    $leftOver.Count -eq 0 -and
    -not (Test-Path (Join-Path $stage 'VERIFY.md')))

# Deleting is best-effort on a filesystem - a handle somebody else holds open
# beats us. Reporting is not: a stale rig that survives a refusal has to be
# named, and what survives must not look deployable.
$stage = Join-Path $fixtureRoot 'stage-lockedstale'
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'beta')
$locked = Join-Path $stage 'models\alpha.bbmodel'
$held = [System.IO.File]::Open($locked, 'Open', 'Read', 'None')
try {
    $res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('noyaw')
}
finally { $held.Dispose() }
$reasons = ($res.failures | ForEach-Object { $_.reason }) -join ' | '
Assert 'ATOM-05' 'cleanup that cannot delete a stale rig says so, and leaves the stage un-READY' (
    $script:LastExit -ne 0 -and
    (Test-Path $locked) -and
    -not (Test-Path (Join-Path $stage 'STAGE-READY')) -and
    $reasons -match [regex]::Escape('models') -and
    $reasons -match 'not removed')
Remove-Item (Join-Path $stage 'models') -Recurse -Force -ErrorAction SilentlyContinue

# The marker cannot be trusted to be deletable either. Lock IT open and the
# stage loses its rigs while keeping the thing that says it has them.
$stage = Join-Path $fixtureRoot 'stage-lockedready'
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'beta')
$held = [System.IO.File]::Open((Join-Path $stage 'STAGE-READY'), 'Open', 'Read', 'None')
try {
    $res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('noyaw')
    $preflight = Invoke-Preflight -Stage $stage
}
finally { $held.Dispose() }
$reasons = ($res.failures | ForEach-Object { $_.reason }) -join ' | '
Assert 'READY-01' 'a surviving STAGE-READY is tombstoned, named, and cannot make the stage deployable' (
    $script:LastExit -ne 0 -and
    (Test-Path (Join-Path $stage 'STAGE-INVALID')) -and
    $reasons -match 'STAGE-READY' -and $reasons -match 'not removed' -and
    $preflight -ne 0)
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue

# --- PRE: readiness is decided by running something, not by looking ----------
Write-Host ''
Write-Host 'PRE  the deployability preflight'

# NOT named "stage-preflight": the stage path is printed inside VERIFY.md, and a
# fixture called that made PRE-03 below match its own directory name. Case-
# sensitive matching on the command form is the second guard against the same
# accident.
$stage = Join-Path $fixtureRoot 'stage-readycheck'
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'beta')
Assert 'PRE-01' 'the preflight passes on a complete stage' ((Invoke-Preflight -Stage $stage) -eq 0)

$tampered = Join-Path $fixtureRoot 'stage-tampered'
$null = Invoke-Stager -Source $sourceRoot -Stage $tampered -Rig @('alpha', 'beta')
Add-Content -Path (Join-Path $tampered 'models\alpha.bbmodel') -Value ' '
$changedFails = (Invoke-Preflight -Stage $tampered) -ne 0

$extra = Join-Path $fixtureRoot 'stage-extra'
$null = Invoke-Stager -Source $sourceRoot -Stage $extra -Rig @('alpha')
Copy-Item (Join-Path $extra 'models\alpha.bbmodel') (Join-Path $extra 'models\stowaway.bbmodel')
$extraFails = (Invoke-Preflight -Stage $extra) -ne 0

Assert 'PRE-02' 'the preflight fails on changed bytes and on a file the marker never listed' (
    $changedFails -and $extraFails)

$noVerify = Join-Path $fixtureRoot 'stage-noverify'
$null = Invoke-Stager -Source $sourceRoot -Stage $noVerify -Rig @('alpha', 'beta')
Remove-Item (Join-Path $noVerify 'VERIFY.md') -Force
Assert 'PRE-04' 'the preflight fails when VERIFY.md is missing' ((Invoke-Preflight -Stage $noVerify) -ne 0)

$badVerify = Join-Path $fixtureRoot 'stage-badverify'
$null = Invoke-Stager -Source $sourceRoot -Stage $badVerify -Rig @('alpha', 'beta')
Add-Content -Path (Join-Path $badVerify 'VERIFY.md') -Value 'copy it anyway, skip the lock'
Assert 'PRE-05' 'the preflight fails when VERIFY.md has been changed' ((Invoke-Preflight -Stage $badVerify) -ne 0)

# Basename matching is what makes this dangerous: the rig is still "there" by
# name and hash, and no longer where BetterModel reads.
$moved = Join-Path $fixtureRoot 'stage-moved'
$null = Invoke-Stager -Source $sourceRoot -Stage $moved -Rig @('alpha', 'beta')
$null = New-Item -ItemType Directory -Force (Join-Path $moved 'models\nested')
Move-Item (Join-Path $moved 'models\alpha.bbmodel') (Join-Path $moved 'models\nested\alpha.bbmodel')
Assert 'PRE-06' 'the preflight fails when a listed rig has moved into a subdirectory' (
    (Invoke-Preflight -Stage $moved) -ne 0)

$nested = Join-Path $fixtureRoot 'stage-nested'
$null = Invoke-Stager -Source $sourceRoot -Stage $nested -Rig @('alpha')
$null = New-Item -ItemType Directory -Force (Join-Path $nested 'models\empty')
Assert 'PRE-07' 'the preflight fails on a subdirectory in models/, empty included' (
    (Invoke-Preflight -Stage $nested) -ne 0)

# models/ replaced by a junction to a backing folder outside the stage: every
# entry inside it still matches, and the thing being checked is no longer the
# thing that gets copied.
$linked = Join-Path $fixtureRoot 'stage-linkedmodels'
$null = Invoke-Stager -Source $sourceRoot -Stage $linked -Rig @('alpha', 'beta')
$backing = Join-Path $fixtureRoot 'external-backing'
Move-Item (Join-Path $linked 'models') $backing
if (New-Junction -Link (Join-Path $linked 'models') -Target $backing) {
    Assert 'PRE-08' 'the preflight fails when models/ is itself a reparse point' (
        (Invoke-Preflight -Stage $linked) -ne 0)
}
else {
    Assert 'PRE-08' 'the preflight fails when models/ is itself a reparse point' $false
    Write-Host '  (could not create a junction - this assertion cannot be evaluated here)'
}

$linkedVerify = Join-Path $fixtureRoot 'stage-linkedverify'
$null = Invoke-Stager -Source $sourceRoot -Stage $linkedVerify -Rig @('alpha')
Remove-Item (Join-Path $linkedVerify 'VERIFY.md') -Force
if (New-Junction -Link (Join-Path $linkedVerify 'VERIFY.md') -Target $backing) {
    Assert 'PRE-09' 'the preflight fails when VERIFY.md is not a real leaf file' (
        (Invoke-Preflight -Stage $linkedVerify) -ne 0)
}
else {
    Assert 'PRE-09' 'the preflight fails when VERIFY.md is not a real leaf file' $false
    Write-Host '  (could not create a junction - this assertion cannot be evaluated here)'
}

# The stage leaf is an ordinary directory; its PARENT is the junction. The write
# guard already walked ancestors, so this is the case where the two sides of the
# same rule disagreed.
$parentDir = Join-Path $fixtureRoot 'linked-parent'
$leafStage = Join-Path $parentDir 'stage'
$null = Invoke-Stager -Source $sourceRoot -Stage $leafStage -Rig @('alpha', 'beta')
$parentBacking = Join-Path $fixtureRoot 'linked-parent-backing'
Move-Item $parentDir $parentBacking
if (New-Junction -Link $parentDir -Target $parentBacking) {
    Assert 'PRE-10' 'the preflight fails when an ancestor of the stage is a reparse point' (
        (Invoke-Preflight -Stage $leafStage) -ne 0)
}
else {
    Assert 'PRE-10' 'the preflight fails when an ancestor of the stage is a reparse point' $false
    Write-Host '  (could not create a junction - this assertion cannot be evaluated here)'
}

Assert 'PRE-03' 'a successful run clears STAGE-INVALID, and the runbook runs the preflight' (
    -not (Test-Path (Join-Path $stage 'STAGE-INVALID')) -and
    ([System.IO.File]::ReadAllText((Join-Path $stage 'VERIFY.md')) -cmatch 'deploy-rigs\.ps1 -Preflight'))

$res = Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-norigs') -Rig @('')
Assert 'RIG-02' 'an invocation naming no rigs and asking for no preflight refuses' (
    $script:LastExit -ne 0 -and (FailedRigs $res).Count -gt 0)

# --- SAFE: the stage-only boundary is enforced, not promised -----------------
Write-Host ''
Write-Host 'SAFE  destinations the stager refuses'

$plugin = Join-Path $fixtureRoot 'fakeserver\plugins\BetterModel'
$sentinel = Join-Path $plugin 'models\already_live.bbmodel'
Write-Utf8 $sentinel 'a rig somebody else deployed'
$res = $null
$writes = Measure-TargetWrites -Watch $plugin -Action {
    $script:res = Invoke-Stager -Source $sourceRoot -Stage $plugin -Rig @('alpha')
}
$res = $script:res
$survivors = @(Get-ChildItem -LiteralPath (Join-Path $plugin 'models') -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
Assert 'SAFE-01' 'a plugins/BetterModel destination is refused with nothing written into it at all' (
    $script:LastExit -ne 0 -and
    (FailedRigs $res) -contains 'alpha' -and
    ($survivors -join ',') -eq 'already_live.bbmodel' -and
    $writes -eq 0)

# The dangerous case is the one whose PATH looks fine. This junction is called
# "handoff" and lands in a live plugin folder.
$fakeSrv = Join-Path $fixtureRoot 'junction-server'
Write-Utf8 (Join-Path $fakeSrv 'server.properties') 'resource-pack-sha1=deadbeef'
$fakePlugin = Join-Path $fakeSrv 'plugins\BetterModel'
$fakeSentinel = Join-Path $fakePlugin 'models\already_live.bbmodel'
Write-Utf8 $fakeSentinel 'a rig somebody else deployed'
$alias = Join-Path $fixtureRoot 'handoff'
if (New-Junction -Link $alias -Target $fakePlugin) {
    $writes = Measure-TargetWrites -Watch $fakePlugin -Action {
        $script:res = Invoke-Stager -Source $sourceRoot -Stage $alias -Rig @('alpha')
    }
    $survivors = @(Get-ChildItem -LiteralPath (Join-Path $fakePlugin 'models') -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    Assert 'SAFE-03' 'a StageDir reaching a live plugin folder through a junction is refused, writing nothing at all' (
        $script:LastExit -ne 0 -and
        ($survivors -join ',') -eq 'already_live.bbmodel' -and
        $writes -eq 0)
}
else {
    Assert 'SAFE-03' 'a StageDir reaching a live plugin folder through a junction is refused' $false
    Write-Host '  (could not create a junction - this assertion cannot be evaluated here)'
}

# Square brackets are legal in a Windows path and a WILDCARD to Test-Path -Path.
# A guard that reads the name has to read it literally or it is reading a
# pattern that matches nothing.
$brPlugin = Join-Path $fixtureRoot 'bracket-server\plugins\BetterModel'
Write-Utf8 (Join-Path $fixtureRoot 'bracket-server\server.properties') 'resource-pack-sha1=deadbeef'
Write-Utf8 (Join-Path $brPlugin 'models\already_live.bbmodel') 'a rig somebody else deployed'
$brAlias = Join-Path $fixtureRoot '[handoff]'
if (New-Junction -Link $brAlias -Target $brPlugin) {
    $writes = Measure-TargetWrites -Watch $brPlugin -Action {
        $script:res = Invoke-Stager -Source $sourceRoot -Stage $brAlias -Rig @('alpha')
    }
    $survivors = @(Get-ChildItem -LiteralPath (Join-Path $brPlugin 'models') -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
    Assert 'SAFE-04' 'a BRACKET-named junction into a live plugin folder is refused with zero writes' (
        $script:LastExit -ne 0 -and
        ($survivors -join ',') -eq 'already_live.bbmodel' -and
        $writes -eq 0)
}
else {
    Assert 'SAFE-04' 'a BRACKET-named junction into a live plugin folder is refused with zero writes' $false
    Write-Host '  (could not create a junction - this assertion cannot be evaluated here)'
}

# A substituted drive root spells nothing, carries no reparse attribute, and has
# no parent above the mapping. It is the one alias that hides every input the
# other guards read.
$substPlugin = Join-Path $fixtureRoot 'subst-server\plugins\BetterModel'
Write-Utf8 (Join-Path $fixtureRoot 'subst-server\server.properties') 'resource-pack-sha1=deadbeef'
Write-Utf8 (Join-Path $substPlugin 'models\already_live.bbmodel') 'a rig somebody else deployed'
# Before anything takes a drive letter: prove the picker will not take one that
# is already claimed. A mapping whose target has been deleted is the case that
# fooled it - Test-Path False, mapping still there.
$goneTarget = Join-Path $fixtureRoot 'gone-target'
$null = [System.IO.Directory]::CreateDirectory($goneTarget)
$occupy = Get-FreeDriveLetter
if ($occupy) {
    $script:unavailable = $false
    $script:beforeTarget = ''
    $script:afterTarget = ''
    $script:picked = $null
    $pick = Use-DriveAlias -Letter $occupy `
        -Create { subst $occupy $goneTarget | Out-Null; return ($LASTEXITCODE -eq 0) } `
        -ExpectedTarget ('\??\' + $goneTarget) `
        -Remove { subst $occupy /D | Out-Null; return ($LASTEXITCODE -eq 0) } `
        -Body {
            Remove-Item -LiteralPath $goneTarget -Recurse -Force -ErrorAction SilentlyContinue
            $script:unavailable = -not (Test-Path -LiteralPath "$occupy\")
            $script:beforeTarget = Get-DosTarget $occupy
            $script:picked = Get-FreeDriveLetter
            $script:afterTarget = Get-DosTarget $occupy
        }

    Assert 'PICK-01' 'the picker skips a letter whose mapping is unavailable, and leaves it untouched' (
        $pick.created -and $pick.targetOk -and -not $pick.threw -and
        $script:unavailable -and $script:beforeTarget -and
        $script:picked -and $script:picked -ne $occupy -and
        $script:afterTarget -eq $script:beforeTarget)
    Assert 'CLEAN-03' 'the picker arm removes the alias it created and restores the drive' (
        $pick.created -and $pick.removed -and $pick.restored)
}
else {
    Assert 'PICK-01' 'the picker skips a letter whose mapping is unavailable, and leaves it untouched' $false
    Assert 'CLEAN-03' 'the picker arm removes the alias it created and restores the drive' $false
    Write-Host '  (no free drive letter - these two assertions cannot be evaluated here)'
}

# The crash path is what try/finally exists for, so it gets its own arm rather
# than a claim. Same helper the three real arms use, with a body that throws the
# instant the alias is live.
$faultLetter = Get-FreeDriveLetter
$faultTarget = Join-Path $fixtureRoot 'fault-target'
$null = [System.IO.Directory]::CreateDirectory($faultTarget)
if ($faultLetter) {
    $fault = Use-DriveAlias -Letter $faultLetter `
        -Create { subst $faultLetter $faultTarget | Out-Null; return ($LASTEXITCODE -eq 0) } `
        -ExpectedTarget ('\??\' + $faultTarget) `
        -Remove { subst $faultLetter /D | Out-Null; return ($LASTEXITCODE -eq 0) } `
        -Body { throw 'injected fault immediately after the alias went live' }

    Assert 'CLEAN-04' 'a throw with the alias live still removes it and restores the drive' (
        $fault.created -and $fault.threw -and $fault.removed -and $fault.restored -and
        (Get-DosTarget $faultLetter) -eq $fault.prior)
}
else {
    Assert 'CLEAN-04' 'a throw with the alias live still removes it and restores the drive' $false
    Write-Host '  (no free drive letter - this assertion cannot be evaluated here)'
}

$letter = Get-FreeDriveLetter
if ($letter) {
    $script:visible = $false
    $script:writes = -1
    $script:stageExit = 0
    $script:reason = ''
    $script:pre = @{ exit = 0; text = '' }
    $script:survivors = @()
    $sub = Use-DriveAlias -Letter $letter `
        -Create { subst $letter $substPlugin | Out-Null; return ($LASTEXITCODE -eq 0) } `
        -ExpectedTarget ('\??\' + $substPlugin) `
        -Remove { subst $letter /D | Out-Null; return ($LASTEXITCODE -eq 0) } `
        -Body {
            $script:visible = Confirm-DriveVisible -Letter $letter -ExpectLike '\??\*'
            if ($script:visible) {
                $script:writes = Measure-TargetWrites -Watch $substPlugin -Action {
                    $script:res = Invoke-Stager -Source $sourceRoot -Stage "$letter\" -Rig @('alpha')
                }
                $script:stageExit = $script:LastExit
                $script:reason = ($script:res.failures | ForEach-Object { $_.reason }) -join ' | '
                $script:pre = Invoke-PreflightDetail -Stage "$letter\"
                $script:survivors = @(Get-ChildItem -LiteralPath (Join-Path $substPlugin 'models') -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
            }
        }
    $visible = $sub.created -and $sub.targetOk -and -not $sub.threw -and $script:visible
    $writes = $script:writes; $stageExit = $script:stageExit
    $reason = $script:reason; $pre = $script:pre; $survivors = $script:survivors

    Assert 'CLEAN-01' 'the SUBST arm removes its own mapping, checks the call, and restores the drive' (
        $sub.created -and $sub.removed -and $sub.restored)

    if ($visible) {
        Assert 'SAFE-06' 'a SUBST drive root into a live plugin folder is refused BY THE GUARD, with zero writes' (
            $stageExit -ne 0 -and
            (StagedRigs $script:res).Count -eq 0 -and
            (FailedRigs $script:res) -contains 'alpha' -and
            $reason -match 'SUBST' -and
            ($survivors -join ',') -eq 'already_live.bbmodel' -and
            $writes -eq 0)
        Assert 'PRE-11' 'the preflight refuses a drive-aliased stage, saying so' (
            $pre.exit -ne 0 -and $pre.text -match 'SUBST')
    }
    else {
        Assert 'SAFE-06' 'a SUBST drive root into a live plugin folder is refused BY THE GUARD, with zero writes' $false
        Assert 'PRE-11' 'the preflight refuses a drive-aliased stage, saying so' $false
        Write-Host "  ($letter was mapped but is not visible to this process - the arms cannot run, so they FAIL rather than pass for the wrong reason)"
    }
}
else {
    Assert 'CLEAN-01' 'the SUBST arm removes its own mapping, checks the call, and restores the drive' $false
    Assert 'SAFE-06' 'a SUBST drive root into a live plugin folder is refused BY THE GUARD, with zero writes' $false
    Assert 'PRE-11' 'the preflight refuses a drive-aliased stage, saying so' $false
    Write-Host '  (no free drive letter - these three assertions cannot be evaluated here)'
}

# A drive letter can also be mapped straight at a volume device PLUS a path. The
# target then legitimately begins with a real volume, and only an anchored check
# tells "is a volume" from "starts with one".
$rawPlugin = Join-Path $fixtureRoot 'raw-server\plugins\BetterModel'
Write-Utf8 (Join-Path $fixtureRoot 'raw-server\server.properties') 'resource-pack-sha1=deadbeef'
Write-Utf8 (Join-Path $rawPlugin 'models\already_live.bbmodel') 'a rig somebody else deployed'
$letter = Get-FreeDriveLetter
$volume = Get-DosTarget ([System.IO.Path]::GetPathRoot($rawPlugin).TrimEnd('\'))
if ($letter -and $volume -like '\Device\*') {
    $rawTarget = $volume + $rawPlugin.Substring(2)      # drop "C:", keep the rest
    $script:visible = $false
    $script:writes = -1
    $script:stageExit = 0
    $script:reason = ''
    $script:pre = @{ exit = 0; text = '' }
    $script:survivors = @()
    # EXACT_MATCH_ON_REMOVE: delete this exact mapping or nothing. Without it the
    # call can remove a mapping this arm did not create.
    $raw = Use-DriveAlias -Letter $letter `
        -Create { return [LcTestNative.Dos]::DefineDosDevice($DDD_RAW_TARGET_PATH, $letter, $rawTarget) } `
        -ExpectedTarget $rawTarget `
        -Remove {
            return [LcTestNative.Dos]::DefineDosDevice(
                ($DDD_REMOVE_DEFINITION -bor $DDD_RAW_TARGET_PATH -bor $DDD_EXACT_MATCH_ON_REMOVE),
                $letter, $rawTarget)
        } `
        -Body {
            $script:visible = Confirm-DriveVisible -Letter $letter -ExpectLike '\Device\*'
            if ($script:visible) {
                $script:writes = Measure-TargetWrites -Watch $rawPlugin -Action {
                    $script:res = Invoke-Stager -Source $sourceRoot -Stage "$letter\" -Rig @('alpha')
                }
                $script:stageExit = $script:LastExit
                $script:reason = ($script:res.failures | ForEach-Object { $_.reason }) -join ' | '
                $script:pre = Invoke-PreflightDetail -Stage "$letter\"
                $script:survivors = @(Get-ChildItem -LiteralPath (Join-Path $rawPlugin 'models') -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
            }
        }
    $visible = $raw.created -and $raw.targetOk -and -not $raw.threw -and $script:visible
    $writes = $script:writes; $stageExit = $script:stageExit
    $reason = $script:reason; $pre = $script:pre; $survivors = $script:survivors

    Assert 'CLEAN-02' 'the raw-alias arm removes exactly its own mapping, checks the call, and restores the drive' (
        $raw.created -and $raw.removed -and $raw.restored)

    if ($visible) {
        Assert 'SAFE-07' 'a drive mapped to a SUBDIRECTORY of a volume device is refused by stager and preflight, with zero writes' (
            $stageExit -ne 0 -and
            (FailedRigs $script:res) -contains 'alpha' -and
            $reason -match 'not a plain local volume' -and
            $pre.exit -ne 0 -and $pre.text -match 'not a plain local volume' -and
            ($survivors -join ',') -eq 'already_live.bbmodel' -and
            $writes -eq 0)
    }
    else {
        Assert 'SAFE-07' 'a drive mapped to a SUBDIRECTORY of a volume device is refused by stager and preflight, with zero writes' $false
        Write-Host '  (the raw device mapping could not be made visible - this assertion cannot be evaluated here)'
    }
}
else {
    Assert 'CLEAN-02' 'the raw-alias arm removes exactly its own mapping, checks the call, and restores the drive' $false
    Assert 'SAFE-07' 'a drive mapped to a SUBDIRECTORY of a volume device is refused by stager and preflight, with zero writes' $false
    Write-Host '  (no free drive letter or no volume device name - these two assertions cannot be evaluated here)'
}

$brSrv = Join-Path $fixtureRoot '[server]'
Write-Utf8 (Join-Path $brSrv 'server.properties') 'resource-pack-sha1=deadbeef'
$writes = Measure-TargetWrites -Watch $brSrv -Action {
    $script:res = Invoke-Stager -Source $sourceRoot -Stage (Join-Path $brSrv 'rigs') -Rig @('alpha')
}
Assert 'SAFE-05' 'a BRACKET-named live server root is refused with zero writes under it' (
    $script:LastExit -ne 0 -and $writes -eq 0)

$srv = Join-Path $fixtureRoot 'liveserver'
Write-Utf8 (Join-Path $srv 'server.properties') 'resource-pack-sha1=deadbeef'
$res = Invoke-Stager -Source $sourceRoot -Stage (Join-Path $srv 'rigs') -Rig @('alpha')
Assert 'SAFE-02' 'a destination under a live server root is refused' (
    $script:LastExit -ne 0 -and
    (FailedRigs $res) -contains 'alpha' -and
    -not (Test-Path (Join-Path $srv 'rigs\models')))

# --- SRC: the source root's own failures come back as named rigs -------------
Write-Host ''
Write-Host 'SRC  source-root failures'

$res = Invoke-Stager -Source (Join-Path $fixtureRoot 'no-such-source') -Stage (Join-Path $fixtureRoot 'stage-nosrc') -Rig @('alpha', 'beta')
$failed = FailedRigs $res
Assert 'SRC-01' 'a missing source root names every requested rig through the normal result' (
    $script:LastExit -ne 0 -and
    ($failed -contains 'alpha') -and ($failed -contains 'beta'))

$notADir = Join-Path $fixtureRoot 'source-is-a-file'
Write-Utf8 $notADir 'this is a file, not a tree'
$res = Invoke-Stager -Source $notADir -Stage (Join-Path $fixtureRoot 'stage-badsrc') -Rig @('alpha', 'beta')
$failed = FailedRigs $res
Assert 'SRC-02' 'a source root that cannot be enumerated names every requested rig' (
    $script:LastExit -ne 0 -and
    ($failed -contains 'alpha') -and ($failed -contains 'beta'))

# --- VER: the owner's verification list ------------------------------------
Write-Host ''
Write-Host 'VER  the verification list'

$stage = Join-Path $fixtureRoot 'stage-verify'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'bone_colossus')
$verify = ''
if (Test-Path (Join-Path $stage 'VERIFY.md')) {
    $verify = [System.IO.File]::ReadAllText((Join-Path $stage 'VERIFY.md'))
}
$alphaSha = Sha1Of (Join-Path $stage 'models\alpha.bbmodel')
Assert 'VER-01' 'the list carries each rig sha1 and its animation clip names' (
    $verify -match [regex]::Escape($alphaSha) -and
    $verify -match 'attack' -and $verify -match 'walk')

$alphaFacing = ($res.staged | Where-Object { $_.rig -eq 'alpha' } | ForEach-Object { $_.facing })
$colossusFacing = ($res.staged | Where-Object { $_.rig -eq 'bone_colossus' } | ForEach-Object { $_.facing })
Assert 'VER-02' 'facing is VERIFIED for bone_colossus and UNPROVEN for every other rig' (
    $colossusFacing -eq 'VERIFIED' -and $alphaFacing -eq 'UNPROVEN' -and
    $verify -match 'UNPROVEN')

# Without baseline and verify around the readings, nothing the owner sees at the
# box can be attributed to the build they deployed.
$iAcquire = $verify.IndexOf('lc-deploy-lock.ps1 acquire')
$iBaseline = $verify.IndexOf('lc-deploy-lock.ps1 baseline')
$iVerify = $verify.IndexOf('lc-deploy-lock.ps1 verify')
$iRelease = $verify.IndexOf('lc-deploy-lock.ps1 release')
Assert 'VER-03' 'the runbook carries acquire, baseline, verify and release in that order' (
    $iAcquire -ge 0 -and $iBaseline -gt $iAcquire -and
    $iVerify -gt $iBaseline -and $iRelease -gt $iVerify)

$readyPath = Join-Path $stage 'STAGE-READY'
$ready = ''
if (Test-Path $readyPath) { $ready = [System.IO.File]::ReadAllText($readyPath) }
Assert 'VER-04' 'a complete stage is marked STAGE-READY, listing every rig and sha1, and the runbook requires it' (
    $ready -match 'alpha\.bbmodel' -and
    $ready -match 'bone_colossus\.bbmodel' -and
    $ready -match [regex]::Escape($alphaSha) -and
    $verify -match 'STAGE-READY')

# --- IDEM: a stale rig does not survive -------------------------------------
Write-Host ''
Write-Host 'IDEM  re-staging'

$stage = Join-Path $fixtureRoot 'stage-idem'
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'beta')
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha')
$after = @(Get-ChildItem -Path (Join-Path $stage 'models') -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name } | Sort-Object)
Assert 'IDEM-01' 'a rig from the previous run does not survive the next one' (
    ($after -join ',') -eq 'alpha.bbmodel')

# --- JSON ------------------------------------------------------------------
Write-Host ''
Write-Host 'JSON  machine-readable result'

$stage = Join-Path $fixtureRoot 'stage-json'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha', 'noyaw')
Assert 'JSON-01' '-Json emits a parseable result carrying staged rigs and failures' (
    $null -ne $res -and
    $null -ne $res.PSObject.Properties['staged'] -and
    $null -ne $res.PSObject.Properties['failures'] -and
    $null -ne $res.PSObject.Properties['stageDir'])

# --- RIG: how the owner actually passes the list ---------------------------
Write-Host ''
Write-Host 'RIG  rig-list parsing'

$stage = Join-Path $fixtureRoot 'stage-comma'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha,beta')
Assert 'RIG-01' 'a comma-joined rig list arriving as one argument stages every rig in it' (
    $script:LastExit -eq 0 -and ((StagedRigs $res) -join ',') -eq 'alpha,beta')

# --- PROP: the identity-root assertion --------------------------------------
#
# The mode is DECLARED, never inferred: -Prop demands an identity root and its
# absence demands the 180-degree yaw, so each arm below has the other mode as
# its own control. A rig that stages under both would mean neither assertion
# ran.
Write-Host ''
Write-Host 'PROP  prop mode'

$stage = Join-Path $fixtureRoot 'stage-prop'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('pring', 'pbanner') -Prop
Assert 'PROP-01' '-Prop stages an identity-root rig the mob facing check would refuse' (
    $script:LastExit -eq 0 -and ((StagedRigs $res) -join ',') -eq 'pring,pbanner')

$stage = Join-Path $fixtureRoot 'stage-prop-mob'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha') -Prop
Assert 'PROP-02' '-Prop refuses a rig carrying the mob 180-degree root yaw, naming it' (
    $script:LastExit -ne 0 -and ((FailedRigs $res) -join ',') -eq 'alpha' -and
    -not (Test-Path (Join-Path $stage 'models')))

# The defect as REPORTED. Not a missing-switch error: a mob-mode run must still
# refuse a prop, and must still say so with the rotation it found.
$stage = Join-Path $fixtureRoot 'stage-prop-nomode'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('pring')
$pringReason = @($res.failures | Where-Object { $_.rig -eq 'pring' } | ForEach-Object { $_.reason })
Assert 'PROP-03' 'without -Prop an identity-root prop is still refused, naming it and its rotation' (
    $script:LastExit -ne 0 -and ((FailedRigs $res) -join ',') -eq 'pring' -and
    ($pringReason -join ' ') -match '0, 0, 0')

$stage = Join-Path $fixtureRoot 'stage-prop-offroot'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('poffroot') -Prop
Assert 'PROP-04' '-Prop refuses an identity rotation whose root is off the origin' (
    $script:LastExit -ne 0 -and ((FailedRigs $res) -join ',') -eq 'poffroot')

$stage = Join-Path $fixtureRoot 'stage-prop-mixed'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('pring', 'alpha') -Prop
Assert 'PROP-05' 'a mixed prop/mob batch under -Prop stages nothing and names the mob' (
    $script:LastExit -ne 0 -and ((FailedRigs $res) -join ',') -eq 'alpha' -and
    -not (Test-Path (Join-Path $stage 'models\pring.bbmodel')))

$stage = Join-Path $fixtureRoot 'stage-prop-rules'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('pnotex', 'pnoelem', 'pidentbad') -Prop
Assert 'PROP-06' 'prop mode still applies id agreement, embedded texture and geometry' (
    $script:LastExit -ne 0 -and
    (((FailedRigs $res) | Sort-Object) -join ',') -eq 'pidentbad,pnoelem,pnotex')

$stage = Join-Path $fixtureRoot 'stage-prop-shape'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('pring', 'pbanner') -Prop
$propModels = @(Get-ChildItem -Path (Join-Path $stage 'models') -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object { $_.Name } | Sort-Object)
$propReady = ''
if (Test-Path (Join-Path $stage 'STAGE-READY')) { $propReady = [System.IO.File]::ReadAllText((Join-Path $stage 'STAGE-READY')) }
Assert 'PROP-07' 'a prop stage has the mob stage shape, and its own preflight passes on it' (
    ($propModels -join ',') -eq 'pbanner.bbmodel,pring.bbmodel' -and
    (Test-Path (Join-Path $stage 'VERIFY.md')) -and
    -not (Test-Path (Join-Path $stage 'models\VERIFY.md')) -and
    $propReady -match 'pring\.bbmodel' -and $propReady -match 'pbanner\.bbmodel' -and
    (Invoke-Preflight -Stage $stage -Prop) -eq 0)

$propVerify = ''
if (Test-Path (Join-Path $stage 'VERIFY.md')) { $propVerify = [System.IO.File]::ReadAllText((Join-Path $stage 'VERIFY.md')) }
$mobVerify = [System.IO.File]::ReadAllText((Join-Path $fixtureRoot 'stage-verify\VERIFY.md'))
Assert 'PROP-08' 'the prop runbook drops the facing checklist and says why; the mob one keeps it' (
    $propVerify -notmatch 'front points forward' -and
    $propVerify -match 'has no front' -and
    $mobVerify -match 'front points forward')

$propStaged = @($res.staged | Where-Object { $_.rig -eq 'pring' })
$mobRes = Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-prop-kind') -Rig @('alpha')
$mobStaged = @($mobRes.staged | Where-Object { $_.rig -eq 'alpha' })
Assert 'PROP-10' 'the result marks kind per rig, and a prop facing reads NOT-APPLICABLE' (
    $propStaged.Count -eq 1 -and $propStaged[0].kind -eq 'prop' -and
    $propStaged[0].facing -eq 'NOT-APPLICABLE' -and
    $mobStaged.Count -eq 1 -and $mobStaged[0].kind -eq 'mob' -and
    $mobStaged[0].facing -eq 'UNPROVEN')

$propPre = Invoke-PreflightDetail -Stage $stage -Prop
$mobPre = Invoke-PreflightDetail -Stage (Join-Path $fixtureRoot 'stage-prop-kind')
Assert 'PROP-11' 'STAGE-READY records the mode and the preflight reports it, without changing its verdict' (
    $propReady -match '#!mode prop' -and
    $propPre.exit -eq 0 -and $propPre.text -match 'PROP stage' -and
    $mobPre.exit -eq 0 -and $mobPre.text -match 'MOB stage')

# PROP-09/PROP-12 prove DEFAULTS, so they pass no -StageDir. A copy of the
# stager in temp makes its $PSScriptRoot-relative defaults land in temp - the
# suite never writes into the repo it gates.
$scriptCopyDir = Join-Path $fixtureRoot 'stager-copy'
$null = New-Item -ItemType Directory -Force $scriptCopyDir
$scriptCopy = Join-Path $scriptCopyDir 'deploy-rigs.ps1'
Copy-Item -LiteralPath $Stager -Destination $scriptCopy -Force

$null = Invoke-Stager -Source $sourceRoot -Rig @('pring') -Prop -DefaultStage -UseStager $scriptCopy
$defaultPropRig = Join-Path $scriptCopyDir 'dist\props\models\pring.bbmodel'
$defaultMobDir = Join-Path $scriptCopyDir 'dist\rigs'
Assert 'PROP-09' '-Prop defaults its stage to dist\props, leaving the mob stage in dist\rigs untouched' (
    $script:LastExit -eq 0 -and (Test-Path $defaultPropRig) -and -not (Test-Path $defaultMobDir))

# The control is the same preflight WITHOUT -Prop: dist\rigs does not exist yet,
# so a switch that did nothing would fail here rather than pass by luck.
$preDefaultProp = Invoke-PreflightDetail -Prop -DefaultStage -UseStager $scriptCopy
$preDefaultMob = Invoke-PreflightDetail -DefaultStage -UseStager $scriptCopy
Assert 'PROP-12' '-Preflight -Prop defaults to the prop stage, and without it to the mob stage' (
    $preDefaultProp.exit -eq 0 -and $preDefaultMob.exit -ne 0)

$null = Invoke-Stager -Source $sourceRoot -Rig @('alpha') -DefaultStage -UseStager $scriptCopy
Assert 'PROP-09b' 'the mob default is unchanged: no -Prop still stages into dist\rigs' (
    $script:LastExit -eq 0 -and (Test-Path (Join-Path $scriptCopyDir 'dist\rigs\models\alpha.bbmodel')))

# The refusal HINT is the caller's only channel for a wrong-switch failure, so
# each arm below asserts the hint AND runs what it recommends. A hint nobody
# follows through on is how F1 shipped: it read the yaw alone, so a tilted root
# was told to swap the switch and the swap refused it too.
function ReasonFor {
    param($Result, [string]$Rig)
    if (-not $Result) { return '' }
    (@($Result.failures | Where-Object { $_.rig -eq $Rig } | ForEach-Object { $_.reason }) -join ' ')
}

$stage = Join-Path $fixtureRoot 'stage-hint-prop'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('pring')
$hintProp = ReasonFor $res 'pring'
$null = Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-hint-prop-followed') -Rig @('pring') -Prop
Assert 'PROP-13' 'a mob-mode refusal that points at -Prop points at a run that really stages the rig' (
    $hintProp -match 'pass -Prop to stage it' -and $script:LastExit -eq 0)

$stage = Join-Path $fixtureRoot 'stage-hint-mob'
$res = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha') -Prop
$hintMob = ReasonFor $res 'alpha'
$null = Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-hint-mob-followed') -Rig @('alpha')
Assert 'PROP-14' 'a -Prop refusal that says to drop the switch is followed by a mob run that stages it' (
    $hintMob -match 'drop -Prop to stage it' -and $script:LastExit -eq 0)

# F1, as reported. Both rigs are refused by BOTH modes, so neither refusal may
# recommend the other one.
$tiltPropMob = ReasonFor (Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-tilt-1') -Rig @('ptiltprop')) 'ptiltprop'
$tiltPropProp = ReasonFor (Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-tilt-2') -Rig @('ptiltprop') -Prop) 'ptiltprop'
$tiltMobMob = ReasonFor (Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-tilt-3') -Rig @('ptiltmob')) 'ptiltmob'
$tiltMobProp = ReasonFor (Invoke-Stager -Source $sourceRoot -Stage (Join-Path $fixtureRoot 'stage-tilt-4') -Rig @('ptiltmob') -Prop) 'ptiltmob'
# Each reason is required to name the rotation it refused, so "no hint" is a
# hint that is absent from a refusal that DID happen - not a refusal that never
# ran, which reads the same in a -notmatch.
Assert 'PROP-15' 'a root neither mode accepts gets no hint from either mode, and is still refused by name' (
    $tiltPropMob -match '10, 0, 0' -and $tiltPropMob -notmatch '-Prop to stage it' -and
    $tiltPropProp -match '10, 0, 0' -and $tiltPropProp -notmatch '-Prop to stage it' -and
    $tiltMobMob -match '10, 180, 0' -and $tiltMobMob -notmatch '-Prop to stage it' -and
    $tiltMobProp -match '10, 180, 0' -and $tiltMobProp -notmatch '-Prop to stage it')

# The backward-compatibility branch: a marker written before the directive
# existed. Stripping the comment changes no hash, so the stage is still whole -
# which is the point, because the mode is information and the hashes decide.
$stage = Join-Path $fixtureRoot 'stage-nodirective'
$null = Invoke-Stager -Source $sourceRoot -Stage $stage -Rig @('alpha')
$readyPath = Join-Path $stage 'STAGE-READY'
$stripped = (@([System.IO.File]::ReadAllLines($readyPath) | Where-Object { -not $_.Trim().StartsWith('#!mode') }) -join "`r`n") + "`r`n"
[System.IO.File]::WriteAllText($readyPath, $stripped, (New-Object System.Text.UTF8Encoding($false)))
$noDirective = Invoke-PreflightDetail -Stage $stage
Assert 'PROP-16' 'a STAGE-READY with no mode directive is still deployable, and says an older stager wrote it' (
    $stripped -notmatch '#!mode' -and
    $noDirective.exit -eq 0 -and $noDirective.text -match 'older stager')

# ---------------------------------------------------------------------------

if (-not $KeepFixture) { Remove-Item $fixtureRoot -Recurse -Force -ErrorAction SilentlyContinue }

Write-Host ''
Write-Host "  $($script:Pass) passed, $($script:Fail) failed  ($($script:Pass + $script:Fail) assertions)"
Write-Host ''
if ($script:Fail -gt 0) { exit 1 }
exit 0
