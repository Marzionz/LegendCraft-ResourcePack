# Tooling in this repo

Scripts that ship with the pack, what they do, and how to test them. The pack's
own layout and asset conventions are in `README.md` (kept out of the published
tree, alongside `mobs-src/` and `tools/`).

| script | what it does | tests |
|---|---|---|
| `build.ps1` | zips `src/` into `dist/LegendCraft-Pack-<version>.zip` and prints the SHA1 Paper needs for `setResourcePack` | none |
| `deploy-rigs.ps1` | stages named `.bbmodel` rigs — mobs, or props under `-Prop` — from the authoring tree into a BetterModel-shaped folder, and writes the verification list the owner works through at the box | `tests/run-deploy-rigs-tests.ps1` |
| `tools/generate_hud.py` | writes the HUD art and the BetterHud YAML under `hud/` | `tools/test_generate_hud.py`, plus the CI drift gate |
| `tools/deploy-hud.ps1` | the whole HUD loop against mc-dev: regenerate, copy, restart, merge, publish, repoint, restart | none — it drives a live server |
| `tools/merge_dev_pack.py` | merges the plugin build zips with the newest built base pack into `dist/LegendCraft-Pack-dev.zip` | `tools/test_pack_manifest.py` |
| `tools/publish-pack.ps1` | uploads a pack to the rolling `dev` pre-release, or promotes a tested dev pack to an immutable `v<version>` | `tests/run-pack-pin-tests.ps1` |
| `tools/check-pack-pin.ps1` | the production pre-start guard: refuses a dev pin, an absent pin, or a sha1 that is not the bytes at the pinned URL | `tests/run-pack-pin-tests.ps1` |
| `tools/check_generator_drift.py` | the committed `hud/` tree equals generator output; images compared by decoded pixels, everything else byte for byte | CI gate |
| `tools/check_hud_placeholders.py` | every `papi:legendcraft_*` the HUD reads names a case in `LegendCraft-Classes`' expansion source | `tools/test_hud_placeholders.py` |
| `tools/check_hud_yaml.py` | the BetterHud files parse and hold the generator's invariants, and every `pattern:` in the tree obeys the text parser's slash rule | `tools/test_hud_yaml.py` |
| `tools/check_pack_manifest.py` | a merged pack still carries what its inputs put in, and its `pack.mcmeta` declares the format range the client needs before it applies any of it (`--manifest-only` audits `src/pack.mcmeta` alone, which is what CI can reach) | `tools/test_pack_manifest.py` |

## `deploy-rigs.ps1`

```
powershell -NoProfile -File deploy-rigs.ps1 [-Prop] -Rig <name>[,<name>...] [-SourceRoot <dir>] [-StageDir <dir>] [-Json]
powershell -NoProfile -File deploy-rigs.ps1 -Preflight [-Prop] [-StageDir <dir>]
```

Durable, re-runnable tooling (ENGINEERING_STANDARDS §20), not a one-shot: every
run fully replaces its own stage, so running it again is always safe.

Each named rig is located as `<name>.bbmodel` anywhere under `-SourceRoot`
(default `./mobs-src`), checked, and copied to `<StageDir>/models/<name>.bbmodel`
(default stage `./dist/rigs` for mobs, `./dist/props` under `-Prop`).
`<StageDir>/VERIFY.md` is written beside — never inside — `models/`, so the
folder that gets copied onto a server holds nothing but rigs. `-Json` swaps the
human report for a machine-readable result.

### Mobs and props

A mob is authored facing +Z and carries an origin-anchored 180° yaw on its
`root` bone to meet Minecraft's −Z. A **prop** — a banner planted in the ground,
a ring laid on the floor, a glyph worn by a player — has no front, so it carries
an **identity root** by design and is refused by that check. `-Prop` swaps that
one assertion for its identity counterpart and changes nothing else: same id
agreement, same embedded-texture rules, same geometry rule, same all-or-nothing,
same `STAGE-READY` manifest.

The mode is **declared, never inferred from the file**. Inferring it would delete
the assertion rather than swap it: a mob rig whose yaw was lost in authoring
would stage silently as a "prop", which is exactly what the facing check exists
to catch. Because each mode demands what the other forbids, a rig named in the
wrong run is refused — and the refusal names the switch that would have staged it.

The two kinds stage into **separate default directories**, so a prop run cannot
silently replace a mob stage and each kind gets a `STAGE-READY` of its own. Both
are copied into the same `plugins/BetterModel/models`, so the mode does not
change whether a stage is safe to copy: `STAGE-READY` records which mode wrote
it, and the preflight **reports** that without gating on it. A prop's runbook
carries no facing checklist — a check nobody can perform trains the reader to
skip items — and says why in its place.

Rig names are arguments, not a built-in list: this repo is published, and the
authoring tree it reads from deliberately is not.

**It stages; it never deploys.** The copy into `plugins/BetterModel/models` is a
person's step on a shared box, taken under the deploy lock, and the generated
`VERIFY.md` is the runbook for it — lock, preflight, copy, restart, pack merge,
restart, `baseline`, the per-rig checks, `verify`, `release`. A destination
inside a `plugins/BetterModel` folder, anywhere under a directory holding
`server.properties`, or reached through a junction or symlink at any level, is
refused before anything is read, written or deleted. Reparse points are refused
rather than resolved: a link's visible path says nothing about where writes land,
and refusing costs one unusual layout where following could cost a live server
its models folder.

Every path the script takes from a caller reaches the filesystem through
`-LiteralPath` or a .NET API. `Test-Path -Path` treats square brackets as a
wildcard, so a directory legally named `[handoff]` reads as absent and a guard
inspecting it waves the destination through — a caller's path is data, never a
pattern.

The stage's drive root must also be a **plain local volume**. `subst R: <a live
plugin folder>` produces a destination that spells no plugin segments, carries no
reparse attribute and has no visible parent, and both `DriveInfo` and
`Win32_LogicalDisk` report it as an ordinary fixed disk; `QueryDosDevice` is what
tells them apart. The device target must match `\Device\HarddiskVolume<N>`
**exactly** — a letter can be mapped at a volume *plus a path*, which begins with
a real volume and is not one. A SUBST, a network drive, a volume subdirectory, or
a root whose nature cannot be established is refused rather than resolved — the
alias can be re-pointed after the check either way.

A rig that fails any check is reported by name and **nothing is staged** — not
that rig, not the ones that passed, and not what a previous run left behind. A
folder this script has rejected must never be one somebody can still copy.

Two files make that promise checkable. `STAGE-READY` is written **last**, once
every rig and `VERIFY.md` are in place, and lists `<sha1>  <path>` for every file
in the stage — each `models/<rig>.bbmodel` **and** `VERIFY.md` itself, because
the runbook carries the lock discipline and the per-rig checks (facing among
them, for mobs), and a stage that lost it is not one to copy from. `STAGE-INVALID` is written **first**,
before any cleanup or promotion, and is removed only as the final act of a run
that has verified its own output — so a stage stops being deployable the moment
it stops being whole, including when a file cannot be deleted at all.

Deletion can fail when another process holds a handle; when it does, the run
names the surviving path rather than exiting quietly. That is also why presence
of `STAGE-READY` is **not** the copy precondition — a refusal can leave one
behind. Readiness is decided by running:

```
powershell -NoProfile -File deploy-rigs.ps1 -Preflight -StageDir <dir>
```

Exit 0 means `STAGE-INVALID` is absent, `STAGE-READY` is present, and every path
it lists matches on disk, hash for hash — with `models/` read **one level deep**,
so a rig moved into a subfolder is missing rather than found, and any
subdirectory or link in there is itself a refusal. The stage directory,
`models/`, `STAGE-READY` and `VERIFY.md` must each be a real file or directory,
and **no ancestor of the stage may be a reparse point either** — both sides walk
the same path through one shared helper, so the preflight cannot bless a folder
staging would refuse. If any of them is a link, the thing being checked is not
provably the thing a copy would read, and it can be re-pointed in between. It
writes nothing, so it is safe to point anywhere. The generated runbook makes it
step 2, before the copy.

### Testing

```
powershell -NoProfile -File tests\run-deploy-rigs-tests.ps1
```

73 assertions against a synthetic authoring tree built in temp; no real rig is
read. `-KeepFixture` leaves that tree on disk to look at, `-StagerPath` points
the suite at a different copy of the script. Run it whenever `deploy-rigs.ps1`
changes. The `tests/RED-*.txt` files are the recorded red runs the suite's own
header explains.

Three arms create a temporary drive alias — two to prove the guards see through
one, and one to prove the letter picker refuses an occupied name. They take a
letter only when nothing claims it — `Test-Path` false **and** `QueryDosDevice`
empty, because a mapping to an unavailable target answers False while still
existing.

All three go through one lifetime helper rather than repeating the pattern: the
create call runs **inside** the `try`, the cleanup obligation comes from that
call's own result and from nothing else, and the target check and the arm's body
run after it where `finally` still covers them. Removal uses
`DDD_EXACT_MATCH_ON_REMOVE` where the API offers it, and the result plus the
drive's restored state are both checked. Four assertions hold that — one per
creating arm, plus one that throws the instant an alias is live and requires the
drive to come back anyway. A fixture that mutates the machine it runs on is a
defect of the gate, and the crash path is where that happens.

## Adding a script to `tools/`

`.gitignore` keeps `tools/` unpublished and re-includes the gated pipeline file by file, so a
new script there is untracked until it earns a negation line. That fails closed rather than
quietly: `ci.yml` names every gate script it runs, so one missing from the tree stops the run.
Add the negation in the same change that adds the script.
