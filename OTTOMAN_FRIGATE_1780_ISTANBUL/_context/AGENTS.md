# Ships Project Rules

## Project identity
- This directory is the standalone Ships project. It is NOT MenuTasarimi.
- All ship assets, reports, renders, exports, temporary recovery files and workflow metadata stay under `C:\Users\Murat\Desktop\Ships`.
- Every ship has its own folder named `{TYPE}_{YEAR}_{NAME}`. Final deliverables are separated into mandatory `Blender/`, `Materials/`, `Textures/`, and `FBX/` folders; references, renders, reports and archives remain in their own supporting folders.

## User and agent policy
- Communicate with Murat in Turkish and give short progress updates.
- Use only free/local tooling unless Murat explicitly authorizes otherwise.
- Do not use external Codex, Claude Code or OpenCode agents.
- Internal specialist analysis may use Hermes `delegate_task`, maximum three children concurrently.
- The Kanban board is the durable source of truth. A card is not complete until evidence is attached or referenced in its completion summary.

## Absolute ship quality requirements
- Low-poly, stylized, blockout-looking or visibly simplified final assets are forbidden.
- Target: photorealistic, historically plausible, game-ready, high-detail 16th–18th century ships.
- Required systems: hull, deck, masts/rigging, sails, cannons, fittings/details and boats where historically appropriate.
- Use dense enough geometry, subdivision-compatible topology, UV unwraps and physically based materials.
- Materials must distinguish wood species/finish, metal, rope, canvas and weathering. Missing textures or pink materials are failures.
- Waterline is `Z=0`. Draft must come from the approved historical ship specification; the old approximate 7 m target applies only where a large-ship specification explicitly supports it and never as a default for small craft.
- Ships use a hybrid modular architecture. Structural hull-core geometry may be joined into an approved core mesh, but every gameplay-swappable system must remain a separate module with stable pivots/sockets and a versioned assembly manifest. Never join sails, mast/rig sets, cannons, rudders, figureheads, cabins or other yard-upgrade modules into the hull core.

## Safety and file discipline
- Never overwrite the only copy of a `.blend`. Save versioned files (`v001`, `v002`, ...), then promote an approved copy to the master filename.
- Never delete source/reference assets during automated work. Move superseded files to the ship's `_archive` folder.
- Never run destructive cleanup without an inventory report.
- Use persistent `dir:` workspaces for Blender and final artifacts; never use scratch workspaces for deliverables.
- One writer at a time for the master `.blend`. Parallel agents may research or work on isolated module copies only.
- Never store a final `.blend`, material library/manifest, texture map or FBX loose in the ship root. Use the mandatory delivery folders.
- Blender image paths in the final master must be relative to the ship package. Packed textures may be included as a backup, but never replace the external files under `Textures/`.

## Mandatory final package layout
- `Blender/`: `{SHIP_ID}_master.blend`, versioned source `.blend` files and pre-change backups.
- `Materials/`: reusable material-library `.blend` plus material manifest/metadata and optional previews.
- `Textures/`: external PBR maps grouped by material family; expected sets include BaseColor, DirectX Normal and ORM where applicable.
- `FBX/`: independently exported Hull Core and every gameplay-swappable module, plus an export manifest with source version and hashes.
- `references/`, `renders/`, `reports/` and `_archive/`: supporting evidence, not final asset buckets.

## Completion gates
A ship/model task is not done because code ran or a file was written. Completion requires:
1. Expected files exist in the ship folder.
2. The `.blend` opens in Blender 5.2 without blocking errors.
3. Scene audit JSON is generated.
4. Object, mesh, material, UV, missing-texture, scale, bounds and waterline checks are reviewed.
5. Required components, hull-core integrity, module boundaries, socket compatibility and assembly manifest are verified.
6. At least bow, stern, port/starboard, deck and three-quarter views are visually inspected.
7. `computer_use` visual verification is performed on the live Blender scene or rendered images.
8. QA score is at least 90/100, with no hard-fail condition.
9. Final report records evidence paths and known limitations.
10. After Gate B, `Blender/`, `Materials/`, `Textures/`, and `FBX/` contain the expected non-empty deliverables; texture paths are relative and every FBX is re-import verified.

## Human gates
- Gate A: approve historical identity, dimensions, reference pack and intended quality before expensive modeling.
- Gate B: approve final visual/technical QA before promoting the master asset or exporting.
- Allowed decisions: `ONAYLA`, `DEĞİŞTİR`, `RAFA KALDIR`.
- Human gates must never auto-approve.

## Workflow order
`SCENE_INTAKE -> HISTORICAL_RESEARCH + TECHNICAL_AUDIT + VISUAL_AUDIT -> DESIGN_GATE -> HULL_CORE + SWAPPABLE_MODULES -> UV_PBR -> SOCKET_MANIFEST -> MODULAR_ASSEMBLY -> WATERLINE_CHECK -> TECHNICAL_QA -> VISUAL_QA -> FINAL_GATE -> PACKAGE_EXPORT -> PACKAGE_REIMPORT_QA -> ACCEPTED or RECOVERY`.
