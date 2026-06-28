# Minecraft Modpack Patch Note Generator

> Being a lazy dev has never being this easy!

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

Creating patch notes for a Minecraft modpack can be tedious.

This tool automatically compares two **mods** folders and generates a clean changelog showing exactly what changed between releases.

### Detects

* Newly added mods
* Removed mods
* Updated mod versions
* Custom developer notes
* Ready-to-publish patch notes

---

## Example Output

```text
=== MODS ADDED ===
+ Voxy Server Side (0.2.2)
+ Chunky Pregenerator (2.2.0)
+ Chunky (1.4.55)
+ SeeU (0.6-1.21.11)
+ Voxy (0.2.16-beta)
+ Macaw's Bridges (3.1.2)

=== DELETED MODS ===
- Punchy (2.5.5)

=== UPDATED MODS ===
↑ FancyMenu : 3.9.1 → 3.9.6
↑ NotEnoughAnimations : 1.12.3 → 1.12.4
↑ Simple Discord Link : 3.4.2 → 3.4.3
↑ WaveyCapes : 1.9.2 → 1.10.2
↑ Balm : 21.11.9 → 21.11.9.1
↑ Cristel Lib : 3.1.2 → 3.1.7
↑ EntityCulling : 1.10.2 → 1.10.5
↑ Just Enough Items : 27.4.0.22 → 27.4.0.24
↑ Xaero's Minimap : 25.3.12 → 26.1.4
↑ Collective : 8.25 → 8.32
↑ 3D Skin Layers : 1.11.1 → 1.11.2
↑ Xaero's World Map : 1.40.16 → 1.41.2

=== DEV NOTE ===
(Your custom Dev Note)
```

---

## How It Works

1. Select the **old** modpack `mods` folder.
2. Select the **new** modpack `mods` folder.
3. The program scans every `.jar` file.
4. It reads each mod's metadata and version.
5. A complete patch note is generated automatically.

No manual editing required.

---

## Supported Mod Loaders

* ✅ Fabric
* ✅ Quilt
* ✅ Forge *(mods using `mods.toml`)*
* ✅ NeoForge *(where supported by metadata)*

---

## ❤️ Why?

Having to write down patch notes by hand is annoying af because you have to compare the versions by hand and then write them, ugh... Since I'm a lazy person, I decided to put my skills to good use and create this little tool!
