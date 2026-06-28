# Minecraft Patch Note Maker 1.0

import json
import zipfile
import click
from tkinter import Tk, filedialog

def parse_version(version):
    try:
        return [int(x) for x in version.replace("v", "").split(".")]
    except:
        return [0]


def is_newer(v_old, v_new):
    return parse_version(v_new) > parse_version(v_old)


def get_mod_info(jar_path):
    try:
        with zipfile.ZipFile(jar_path, "r") as jar:

            # Fabric / Quilt
            if "fabric.mod.json" in jar.namelist():
                with jar.open("fabric.mod.json") as f:
                    data = json.load(f)
                    return {
                        "name": data.get("name", "Nom introuvable"),
                        "version": data.get("version", "0")
                    }

            # Forge / NeoForge
            if "META-INF/mods.toml" in jar.namelist():
                with jar.open("META-INF/mods.toml") as f:
                    text = f.read().decode("utf-8", errors="ignore")

                name = "Nom introuvable"
                version = "0"

                for line in text.splitlines():
                    line = line.strip()

                    if line.startswith("displayName"):
                        name = line.split("=", 1)[1].strip().strip('"')

                    if line.startswith("version"):
                        version = line.split("=", 1)[1].strip().strip('"')

                return {"name": name, "version": version}

            return {"name": "Inconnu", "version": "0"}

    except Exception as e:
        return {"name": f"Erreur: {e}", "version": "0"}


def build_mod_dict(jar_files):
    mods = {}
    for jar in jar_files:
        info = get_mod_info(jar)
        mods[info["name"]] = info["version"]
    return mods



# --- UI ---
Tk().withdraw()

jar_files_old = filedialog.askopenfilenames(
    title="Choose the files of the old version",
    filetypes=[("Mods Minecraft", "*.jar")]
)

jar_files_new = filedialog.askopenfilenames(
    title="Choose the files of the new version",
    filetypes=[("Mods Minecraft", "*.jar")]
)

old_mods = build_mod_dict(jar_files_old)
new_mods = build_mod_dict(jar_files_new)

added = []
removed = []
updated = []

# --- comparaison ---
for name, new_version in new_mods.items():
    if name not in old_mods:
        added.append((name, new_version))
    else:
        old_version = old_mods[name]
        if is_newer(old_version, new_version):
            updated.append((name, old_version, new_version))

for name in old_mods:
    if name not in new_mods:
        removed.append((name, old_mods[name]))

# --- dev note ---
if click.confirm("Do you want to add a note to this patch note?", default=True):
    dev_not = click.prompt("Enter your note", type=str)
    dev_not_bool = True
else:
    dev_not_bool = False

# --- display ---
print("\n=== MODS ADDED ===")
for m in added:
    print(f"+ {m[0]} ({m[1]})")

print("\n=== DELETED MODS ===")
for m in removed:
    print(f"- {m[0]} ({m[1]})")

print("\n=== UPDATED MODS ===")
for m in updated:
    print(f"↑ {m[0]} : {m[1]} → {m[2]}")

print("=== DEV NOTE ===")
if dev_not_bool == True:
    print(dev_not)
else :
    print("No note added.")
