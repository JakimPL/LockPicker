# LockPicker — Art Direction

**Working title of the style: "The Instrument-Maker's Cutaway"**

## 1. Concept

You are looking into the exposed mechanism of a precision Victorian lock, clamped on a locksmith's workbench and lit by warm workshop light. Everything on screen is diegetic: the puzzle *is* the machine, and the interface is the bench around it.

The style is *lightly* steampunk — the machine-age flavor comes from materials and craftsmanship, never from props. What this is **not**: goggles, airships, decorative gears glued onto surfaces, glowing runes, neon accents. Every visible part must look like it does something: machined, filed, sprung, oiled.

Reference points: watchmaker's bench photography, museum cutaway models of lever locks, 19th-century patent drawings, the pre-rendered adventure games of the Still Life era.

## 2. Style pillars

1. **Craftsmanship over ornament.** Detail comes from chamfers, screws, knurling, machining marks, and patina. If an element could not plausibly be manufactured and serve a purpose, it does not belong.
2. **Readability first.** Game state (group, master, jammed, pushed, free) must read in under a second. Materials encode groups, light encodes focus, silhouettes stay clean. Beauty never trades against parseability. Every state has at least one non-color cue (shape, value, or position), so the game remains readable in grayscale and for color-blind players.
3. **Diegetic UI.** Buttons are engraved brass plates, menus are paper tags and blueprint sheets on the bench, the level select is a specimen cabinet of locks. Text is rendered live (crisp) over pre-rendered plates.
4. **Warm light, dark metal.** One dominant warm key light against cool dark iron. The amber-versus-gunmetal contrast carries the entire palette; nothing else competes with it.

## 3. Color

### 3.1 Brightness budget

Roughly **70 / 20 / 10**: ~70% of the frame is dark neutrals (housing, background), ~20% mid-value metals (tumblers, picks), ~10% warm highlights (glints, hover, key-light pools). The gameplay elements own the brightness budget; the background never exceeds the darkest tumbler shadow.

### 3.2 Palette

See `docs/art/palette.png` for the swatch sheet.

| Role | Hex | Notes |
|---|---|---|
| Background field / vignette | `#0D0C0B` → `#151312` | warm near-black iron |
| Chamber interior (shadow) | `#2A2622` | oiled bronze wall, baked AO in recesses |
| Chamber interior (midtone) | `#3D3630` | machining marks catch faint light |
| Key light | `#FFC98A` | warm tungsten, upper-left |
| Cool fill | `#4A5560` | dim workshop ambient |
| Group 0 — nickel-steel | base `#8C9298` · hi `#E8EDF2` · shadow `#3E4348` | cool, cleanest finish |
| Group 1 — brass | base `#C9A24B` · hi `#F2D98C` · shadow `#5C4A1E` | warm, soft anisotropic sheen |
| Group 2 — copper | base `#B26E4F` · hi `#E8A87C` · shadow `#4E2E22` | verdigris `#4E7C6B` only in crevices |
| Hover highlight | `#FFD9A0` | emissive rim/edge light — never a flat fill |
| Master marker | `#8E2F2B` | red enamel inlay in an engraved rosette |
| Jam overlay | multiply `#6E6E82` | cools and darkens the metal |
| Pick shaft | `#46586E` | blued spring steel |
| Pick ferrule | `#C9A24B` | brass |
| Pick grips | `#AFC5AF` / `#C5AFAF` | waxed cord wraps; keeps the config pick identities |

### 3.3 Contrast rules

- Groups are separated by **hue and value together**: steel is cool and light, brass warm and mid, copper warm-red and darker. A grayscale screenshot must still distinguish them.
- The three metals plus the two accent colors (hover amber, enamel red) are the only saturated notes; everything else stays within the dark neutral band.
- The warmest and brightest pixel on screen is always something the player should look at.

## 4. Materials

**Tumblers (pins).** Machined metal cylinders/bars with chamfered tips. Edges and contact faces are polished bright (handled metal wears shiny); recesses and flats carry oil film and faint tooling marks. Roughness breakup via subtle smears and brushed texture — no perfectly uniform surfaces. Master tumblers carry an engraved rosette with a red enamel inlay near the tip; regular tumblers are plainer with a slightly duller finish.

**Housing / chamber.** Dark oxidized iron and patinated bronze. Countersunk screws, plate seams, decades of oil staining. Baked ambient occlusion in every recess. The bore rails (where pins slide in) get a polished wear line — this sells the mechanism.

**Picks.** Slender blued-steel tools entering from the left: shaft, brass ferrule, cord-wrapped grip. Tip silhouettes (diamond, circle) are the pick identity and must stay readable at rest and in motion.

## 5. Visual state encoding

| State | Old encoding | New encoding | Non-color cue |
|---|---|---|---|
| Group | fill color | material (nickel / brass / copper) | value difference |
| Master | opaque vs dimmed | engraved rosette + enamel inlay | rosette shape |
| Hovered | white fill | warm rim light + glint | brightening, not recolor |
| Jammed | alpha ÷ 3 | multiply-darkened, cooled metal + seized wedge cue | wedge shape, value drop |
| Pushed / free | height = 1 | pin fully seated in its bore, faint contact shadow | position |
| Selected pick | opaque vs dimmed | full brightness vs oil-dimmed | brightness |
| Post-release ghost (editor) | grey rect | translucent ghost outline | outline style |

## 6. Lighting

- **Key: warm sun lamp** (`#FFC98A`), upper-left, ~35° elevation. Parallel rays are mandatory: sprites translate across the board at runtime, and only falloff-free light keeps their shading and shadow shapes correct at every position.
- **Fill: dim cool HDRI** (`#4A5560` ambient bias) — just enough to keep shadow sides readable.
- **Rim/kicker from the right**, low intensity, to separate dark silhouettes from the dark background.
- Any localized "oil-lamp pool" of light lives **only in the background plate**, painted/baked once. Moving elements never carry positional lighting.
- Shadows: contact AO is baked into each pin sprite; the cast shadow on the back wall is a separate translating layer.

## 7. Rendering and grade

- **Cycles, physically-based, "still-life realism, softly graded."** Real metal BRDFs (anisotropy on brass, tight highlights on steel) do the aesthetic work.
- **Orthographic camera, straight-on.** Depth is faked through modeling (bevels, extruded housing walls) and rim light — never through camera perspective, which would break sprite reuse across columns.
- Grade: filmic curve, slightly warm midtones, gentle vignette, very subtle grain — vignette and grain belong to the background plate only. No bloom on gameplay elements beyond small specular glints.
- Depth of field: background plate only; the gameplay plane stays tack sharp.

## 8. Composition and readability

- Value hierarchy per frame: background darkest → housing → tumbler shadows → tumbler bodies → highlights. Never invert it.
- Silhouettes stay rectangular and clean; surface detail must not erode the pin outline at 80 px column width.
- Tip detail (chamfer, rosette landing) fits within one height unit so a fully collapsed pin still reads.
- The pick's current column should be findable in peripheral vision: the brightest glint sits on the engaged tip.

## 9. Typography

- **Titles / headers:** engraved small-caps serif (license-friendly: Cormorant SC or similar). Used as if stamped or engraved into metal plates — letterpress shading, never plain flat text on a texture.
- **UI body / values:** humanist sans (Alegreya Sans or similar), warm off-white `#E8DFD0`, rendered live for crispness.
- Numbers on gauges/tags may use a condensed engraved style; avoid typewriter and "gothic horror" faces.

## 10. Screens beyond the game view

All screens are the same scene, different camera framing — one lighting rig, one material library, automatic consistency.

- **Main menu:** camera pulled back from the lock; the mechanism sits center-bench, options are engraved brass plates and paper tags around it. Subtle idle animation (dust motes, a breathing highlight).
- **Options:** a clipboard with a blueprint sheet; toggles are physical switches and sliding gauges.
- **Level select:** a specimen cabinet — each lock is a drawer/exhibit with a stamped serial number (level id) and a completion tag.
- **Win moment:** cascade of clicks, the cylinder rotates, the shackle springs open; brief warm flash of the key light.

## 11. Motion language

Mechanical easing everywhere: tumblers settle with a slight spring overshoot and metallic damping; picks slide with a small lag and a firm stop; nothing floats or eases like silk. UI transitions are physical too — plates slide, tags flip, drawers roll.

Audio direction (out of scope for now, noted for consistency): dry mechanical clicks, spring pings, cloth-and-brass foley; no synth pads.

## 12. Do / Don't quick reference

**Do:** chamfers, knurling, countersunk screws, oil films, worn-bright edges, baked AO, engraved lettering, patina in crevices only.

**Don't:** functionless gears, goggles, glowing runes, neon or cyan accents, flat fills, pure black `#000000` or pure white `#FFFFFF`, bloom on gameplay elements, perspective on the play plane.
