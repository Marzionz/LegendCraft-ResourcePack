# Knight war horn

Static held-item art for the Knight's War Cry. The client uses a `GOAT_HORN` with its `item_model` component set to `legendcraft:classes/knight_horn`; vanilla's `TOOT_HORN` use pose moves the arm. This asset contains no bones, animation clips, or `.mcmeta`.

The item key the plugin sets is `legendcraft:classes/knight_horn` via `ModelRegistry.modelKey(CLASSES, "knight_horn")`.

## Shape and source

`knight_horn.bbmodel` is a Blockbench **Java Block/Item** project with one embedded 64×64 texture. Its 84 cubes form five successive curved body sections, a hollow stepped bell, a bored silver mouthpiece ferrule, silver bell band, one thin gold inlay ring, and a leather loop with a silver keeper. The azure chevron is painted once on the bell's outer side.

The mouthpiece is narrow and the bell is broad: a bovine war horn, distinct from the vanilla goat horn silhouette. The construction uses cross-sections made from rectangular cubes; all element rotations are about x at 0°, 22.5°, or 45°. Several cubes make each stepped cross-section. There are no meshes or multi-axis element rotations.

`(8,8,8)` sits at the centre of the mouthpiece opening. The bell points along model **−z** and curves toward **+y**. Rotated geometry bounds are `[5.360, 7.053, -2.830]` to `[10.640, 14.615, 8.060]`, giving approximately 10.9 units of overall z extent including the flared rim. Sixteen units equal one block. The posed item rolls the curve downward and lets the leather loop hang beneath it.

The runtime files are:

- `src/assets/legendcraft/items/classes/knight_horn.json`
- `src/assets/legendcraft/models/item/classes/knight_horn.json`
- `src/assets/legendcraft/textures/item/classes/knight_horn.png`

The source and screenshots are explicitly tracked in this pack branch, as requested by the brief's single-worktree, single-PR deliverable. They are outside `src/` and do not enter the pack zip.

## Palette and paint

The texture uses discrete pixel clusters and plane shading, without gradients or noise. UV strips share material ramps. The bell interior and mouthpiece bore use dark smoke tones to preserve depth at item scale.

| Material | Principal colours |
|---|---|
| Polished silver | `#DCE3EC`, `#B0BCCB`, `#788B9F`, `#46566A`; isolated white edge glints |
| Heraldic gold | `#C49A3A`, `#F0D17D`, `#987126`, `#624C29` |
| Knight mark | `#1F5FB0`, one small `#4385C6` highlight |
| Cream bone | `#F0E9D5`, `#DCD2BA`, `#B6AA96`, `#81776C` |
| Weathered bone | `#E4DAC2`, `#C8BCA4`, `#A29583`, `#716961` |
| Smoke bone | `#C8BBA1`, `#AC9F8A`, `#867C70`, `#605C57` |
| Dark leather | `#79604B`, `#554235`, `#392E29`, `#251F1D`; sparse `#96744D` stitches |
| Interior | `#51483E`, `#3F3933`, `#2C2825`, `#1E1D1C` |

![Texture atlas at four times native size, nearest-neighbour](knight_horn_texture_4x.png)

## Display starting points

Rotations are degrees, translations are Java display units, and scales are multipliers. These are the exported values, including Blockbench's normalization of 180° to −180°.

| View | Rotation x, y, z | Translation x, y, z | Scale x, y, z |
|---|---|---|---|
| `firstperson_righthand` | −53.11, −73.49, 164.01 | 3.11, 4.23, 0.68 | 0.70, 0.70, 0.70 |
| `firstperson_lefthand` | −53.11, −73.49, 164.01 | 3.11, 4.23, 0.68 | 0.70, 0.70, 0.70 |
| `thirdperson_righthand` | 5, −30, −180 | −3.07, 2.57, 3.69 | 0.85, 0.85, 0.85 |
| `thirdperson_lefthand` | 5, −30, −180 | −3.07, 2.57, 3.69 | 0.85, 0.85, 0.85 |
| `gui` | 25, −140, 20 | −5, −1.1, 0 | 1.15, 1.15, 1.15 |
| `ground` | 0, 0, 0 | 0, 2, 0 | 0.60, 0.60, 0.60 |
| `fixed` | 0, 90, −35 | 0, −1, −1 | 0.80, 0.80, 0.80 |

The hand slots intentionally store equal numeric transforms. Java's left-hand display application reverses x translation and y/z rotation. Negating these again in the JSON would undo the intended mirror. The asymmetric strap and single painted mark remain on their physical side of the horn.

The GUI translation centres the geometry around its visual bounds instead of its mouthpiece pivot. The enlarged GUI capture uses a preview-camera zoom of 3; that zoom is not an additional item scale.

## Blockbench previews

Captured and inspected in Blockbench 5.2.1, Java Block/Item Display mode. First-person views use the built-in **Horn Tooting** reference (`tooting`) and its use-pose camera. The horn occupies the lower-right for the right hand and lower-left for the left hand, leaving the view centre clear. Canvas screenshots do not include Blockbench's HTML crosshair overlay.

Third-person views use the player reference with a level head, the active arm raised 85°, and 30° of inward yaw. The item attachment receives the same yaw about the shoulder; the other arm is reset to rest. These preview-only changes reproduce the level-head toot stance without adding animation to the asset. The 85°/30° constants correspond to the vanilla biped toot constants in [Fabric's mapped vanilla constant table](https://maven.fabricmc.net/docs/yarn-1.21.4%2Bbuild.8/constant-values.html#net.minecraft.client.render.entity.model.BipedEntityModel.field_39069). This is a Blockbench fit check, not a captured Minecraft client session.

The side camera is `[42,29,-22]`, targeting `[0,22,-5]`. Other third-person views use the Display editor's default camera. Ground uses the block reference and fixed uses the item-frame reference.

![GUI three-quarter view](knight_horn_gui.png)

![First-person right hand, Horn Tooting reference](knight_horn_firstperson_righthand.png)

![First-person left hand, Horn Tooting reference](knight_horn_firstperson_lefthand.png)

![Third-person right hand](knight_horn_thirdperson_righthand.png)

![Third-person side fit: mouthpiece meets the face](knight_horn_thirdperson_side.png)

![Third-person left hand](knight_horn_thirdperson_lefthand.png)

![Ground display](knight_horn_ground.png)

![Fixed display in an item frame](knight_horn_fixed.png)

### Vanilla comparison

The unmodified vanilla goat-horn model and texture were extracted from the [official Minecraft 1.21.10 client](https://piston-data.mojang.com/v1/objects/d3bdf582a7fa723ce199f3665588dcfe6bf9aca8/client.jar), opened as a separate Java project, and shown with the same first-person Horn Tooting reference and third-person player stance. Blockbench resolves its `item/generated` parent. Only comparison screenshots are included here; the vanilla assets are not added to the pack.

![Vanilla goat horn, first-person reference comparison](knight_horn_reference_goat_firstperson.png)

![Vanilla goat horn, third-person reference comparison](knight_horn_reference_goat_thirdperson.png)

## Verification

2026-09-24, branch `knight-horn`, based on freshly fetched `origin/main` at `d56ded2`.

- Blockbench exported both the `.bbmodel` source and the Java runtime model. Source/model checks passed for all 84 cube bounds and face UVs, all seven display transforms, and pixel-for-pixel equality between the embedded atlas and the runtime PNG.
- Every element coordinate is within −16..32. All rotations use one legal Java axis/angle. One 64×64 texture resolves through `legendcraft:item/classes/knight_horn`; all faces reference it. No source texture path points at this machine.
- `python tools/test_pack_manifest.py`: **5 tests passed**.
- `pwsh -NoProfile -File build.ps1`: **passed**, producing `dist/LegendCraft-Pack-0.2.4.zip`, approximately 764.7 KB. `VERSION` advances from 0.2.3 to 0.2.4 for the new asset.
- Pack SHA1: `7acb6e99b7ebc9bcb62ec52e0df08622f4e6fc62`.
- `python tools/check_pack_manifest.py --pack dist/LegendCraft-Pack-0.2.4.zip --source-tree src`: **passed**, carrying 218 item models, 8 sounds, and 1 `sounds.json`. Plugin-contributed inputs are reported **unchecked** because this is the base-pack build and no plugin source zip was provided.
- Zip entries for the horn item definition, element model, and texture were each checked byte-for-byte against `src/`.

The owner reviews these renders on the draft PR. The later on-box tune still needs to check mouth contact through the full use action, resting-hand appearance, head pitch/crouching, both player arm widths, actual client FOV, and the bell's crosshair clearance. Plugin integration and deployment are separate later work. This draft has not been merged or deployed.
