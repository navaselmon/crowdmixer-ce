# Crowd Mixer 2.0 – Community Edition

![Crowd Mixer 2.0](https://assets.superhivemarket.com/cache/14cd938ac18dbe345cd6ebcb6e4b12ea.png)

This repository is the **public bug tracker** for Crowd Mixer 2.0 – Community Edition (CMX CE). It does not host the add-on's source code.

## What is this add-on?

Crowd Mixer is a Blender add-on built to **populate a scene with believable crowds fast**, then let you refine only the parts that actually matter for the final shot. Crowds are generated with **Geometry Nodes**, and characters are placed and varied automatically so you don't have to position people one by one.

## How it works

Everything is organized around a central **Crowd Manager**:

1. **Load a character source** – either a ready-made Single Mesh character set, or (in the full version) a custom-built one.
2. **Create a crowd** – choose a crowd type (Standing, Flow Curve or Stadium) and link it to a source.
3. **Adjust the Crowd Setting** – control density, placement, and variation for that crowd.
4. Optionally, **load a Crowd Preset** to generate a complete ready-made scene (characters + layout + animation) in one click.

## Features

### 3 crowd types

| Type | Use case |
|---|---|
| **Standing Crowd** | Static groups, waiting zones, and event spaces that need dense placement without path animation |
| **Flow Curve Crowd** | Moving crowds guided along a path, with clear directional motion |
| **Stadium Crowd** | Audience seating and large row-based layouts |

### Individual placement

- **Snap to Scene** – place specific characters exactly where you want them in the shot

### Faster preview

- **Proxy Mode** – lightweight viewport characters so heavier scenes stay easy to navigate; final renders always use full-quality assets
- **Crowd visibility control** – split crowds into separate groups so you can toggle sets on/off while previewing

### Crowd presets included in this edition

Community Edition ships with **3 ready-made crowd presets**:

- **Sports Stadium** – seated audience for sports or large events
- **Urban Street** – street-level scene with walking and standing pedestrians
- **Seminar** – seated audience in a seminar, classroom or conference setting

*(The full Pro version includes 10 presets in total, adding Calm Sports Stadium, Exhibition, Transportation Station, Protest March, Protest Standing, Concert and Beach.)*

## Characters

Community Edition uses the **Single Mesh** workflow only. Character content is limited to a single free set:

**CasualWinter** – 20 Single Mesh characters, available as a separate bonus download (see [Asset For Community Edition](#asset-for-community-edition) below).

The full Pro version includes 91 Single Mesh characters across 7 themes, plus a Modular Mesh system with 2 base characters and 196 customizable parts.

## Community Edition limits

Not included in this edition (Pro-only features):

- **Modular Mesh Workflow** – base characters with customizable head, body, clothing and animation parts
- **Instance Override** – editing individual characters at specific positions without regenerating the crowd
- **Random variation** (Variation > Random) – part of the Modular Mesh workflow
- **7 additional crowd presets** – CE includes only Sports Stadium, Urban Street and Seminar
- **Full character library** – Pro includes 91 characters across 7 themes; CE includes only the CasualWinter set
- The number of crowd characters/agents per scene is limited

## Installation

Install directly from the official Blender Extensions Platform:

**[extensions.blender.org/approval-queue/crowdmixer-ce](https://extensions.blender.org/approval-queue/crowdmixer-ce/)**

Installing this way lets Blender manage updates automatically. Requires **Blender 4.3 or newer**.

## Asset For Community Edition

The **CasualWinter** character set is a free bonus pack for this edition, available as a separate download on Gumroad:

**[navalab.gumroad.com/l/cmx_ce_asset](https://navalab.gumroad.com/l/cmx_ce_asset)**

> Note: this is a raw asset pack (meshes, rigs, textures, presets) read by CMX CE via its **Asset Path** preference — it is not the add-on itself, and is distributed under its own asset license (see the Gumroad page for details).

## Documentation

Full manual, covering Crowd Manager, Character Customization, Preset Collection, and all three crowd types:

**[navalab-studio.com/ProductsPage/crowd-mixer-doc.html](https://navalab-studio.com/ProductsPage/crowd-mixer-doc.html)**

## Reporting a bug

Please [open a new issue](https://github.com/navaselmon/crowdmixer-ce/issues/new?template=bug_report.md) using the bug report template. Include:

- Blender version
- CMX CE version
- Operating system
- Steps to reproduce
- Screenshots or console log, if applicable

## Support

- Documentation: **[navalab-studio.com/ProductsPage/crowd-mixer-doc.html](https://navalab-studio.com/ProductsPage/crowd-mixer-doc.html)**
- Discord: **[discord.gg/v6BZ7Tntbe](https://discord.gg/v6BZ7Tntbe)**

## License

The add-on's Python source code and bundled UI/preset assets (icons, thumbnails, geometry node templates) are licensed under the **GNU General Public License v3.0 or later** (see [LICENSE](LICENSE)).

Character/asset packs distributed separately (e.g. the CasualWinter bonus pack) are covered by their own asset license, provided with that download — not by the GPL license in this repository.

---

## About this edition

This is the **free Community Edition** of Crowd Mixer. Interested in learning more about the full add-on? Find more information at **[navalab-studio.com](https://navalab-studio.com/ProductsPage/crowd-mixer.html)**.

© 2026 Nava Lab. All rights reserved except as expressly granted above.
# Crowd Mixer 2.0 – Community Edition

![Crowd Mixer 2.0](https://assets.superhivemarket.com/cache/14cd938ac18dbe345cd6ebcb6e4b12ea.png)

This repository is the **public bug tracker** for Crowd Mixer 2.0 – Community Edition (CMX CE). It does not host the add-on's source code.

## What is this add-on?

Crowd Mixer is a Blender add-on built to **populate a scene with believable crowds fast**, then let you refine only the parts that actually matter for the final shot. Crowds are generated with **Geometry Nodes**, and characters are placed and varied automatically so you don't have to position people one by one.

## How it works

Everything is organized around a central **Crowd Manager**:

1. **Load a character source** – either a ready-made Single Mesh character set, or (in the full version) a custom-built one.
2. **Create a crowd** – choose a crowd type (Standing, Flow Curve or Stadium) and link it to a source.
3. **Adjust the Crowd Setting** – control density, placement, and variation for that crowd.
4. Optionally, **load a Crowd Preset** to generate a complete ready-made scene (characters + layout + animation) in one click.

## Features

### Easy to start

Start from ready-made crowd presets — pick a setup, load it, and move straight into scene building without configuring the whole crowd system from scratch.

### 3 crowd types

| Type | Use case |
|---|---|
| **Standing Crowd** | Static groups, waiting zones, and event spaces that need dense placement without path animation |
| **Flow Curve Crowd** | Moving crowds guided along a path, with clear directional motion |
| **Stadium Crowd** | Audience seating and large row-based layouts |

### Crowd variation

- **Many human models** – build variety using the included Single Mesh character set (see Characters below)
- **Color Theme** – quick palette-based color changes applied across the crowd

### Individual placement

- **Snap to Scene** – place specific characters exactly where you want them in the shot

### Faster preview

- **Proxy Mode** – lightweight viewport characters so heavier scenes stay easy to navigate; final renders always use full-quality assets
- **Crowd visibility control** – split crowds into separate groups so you can toggle sets on/off while previewing

### Crowd presets included in this edition

Community Edition ships with **3 ready-made crowd presets**:

- **Sports Stadium** – seated audience for sports or large events
- **Urban Street** – street-level scene with walking and standing pedestrians
- **Seminar** – seated audience in a seminar, classroom or conference setting

*(The full Pro version includes 10 presets in total, adding Calm Sports Stadium, Exhibition, Transportation Station, Protest March, Protest Standing, Concert and Beach.)*

## Characters

Community Edition uses the **Single Mesh** workflow only. Character content is limited to a single free set:

**CasualWinter** – 20 Single Mesh characters, available as a separate bonus download (see [Bonus asset](#bonus-asset) below).

The full Pro version includes 91 Single Mesh characters across 7 themes, plus a Modular Mesh system with 2 base characters and 196 customizable parts.

## Community Edition limits

Not included in this edition (Pro-only features):

- **Modular Mesh Workflow** – base characters with customizable head, body, clothing and animation parts
- **Instance Override** – editing individual characters at specific positions without regenerating the crowd
- **Random variation** (Variation > Random) – part of the Modular Mesh workflow
- **7 additional crowd presets** – CE includes only Sports Stadium, Urban Street and Seminar
- **Full character library** – Pro includes 91 characters across 7 themes; CE includes only the CasualWinter set
- The number of crowd characters/agents per scene is limited

## Installation

Install directly from the official Blender Extensions Platform:

**[extensions.blender.org/add-ons/crowdmixer-ce](https://extensions.blender.org/add-ons/crowdmixer-ce/)**

Installing this way lets Blender manage updates automatically. Requires **Blender 4.3 or newer**.

## Bonus asset

The **CasualWinter** character set is a free bonus pack for this edition, available as a separate download on Gumroad:

**[navalab.gumroad.com/l/cmx_ce_asset](https://navalab.gumroad.com/l/cmx_ce_asset)**

> Note: this is a raw asset pack (meshes, rigs, textures, presets) read by CMX CE via its **Asset Path** preference — it is not the add-on itself, and is distributed under its own asset license (see the Gumroad page for details).

## Documentation

Full manual, covering Crowd Manager, Character Customization, Preset Collection, and all three crowd types:

**[navalab-studio.com/ProductsPage/crowd-mixer-doc.html](https://navalab-studio.com/ProductsPage/crowd-mixer-doc.html)**

## Reporting a bug

Please [open a new issue](https://github.com/navaselmon/crowdmixer-ce/issues/new?template=bug_report.md) using the bug report template. Include:

- Blender version
- CMX CE version
- Operating system
- Steps to reproduce
- Screenshots or console log, if applicable

## Support

- Documentation: see link above
- Support / Discord: see [navalab-studio.com](https://navalab-studio.com)

## License

The add-on's Python source code and bundled UI/preset assets (icons, thumbnails, geometry node templates) are licensed under the **GNU General Public License v3.0 or later** (see [LICENSE](LICENSE)).

Character/asset packs distributed separately (e.g. the CasualWinter bonus pack) are covered by their own asset license, provided with that download — not by the GPL license in this repository.

---

## About this edition

This is the **free Community Edition** of Crowd Mixer. Interested in learning more about the full add-on? Find more information at **[navalab-studio.com](https://navalab-studio.com)**.

© 2026 Nava Lab. All rights reserved except as expressly granted above.
