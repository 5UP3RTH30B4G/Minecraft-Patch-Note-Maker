import json
import re
import zipfile
import click
import time
import os
import shutil
from collections import Counter
from tkinter import Tk, filedialog

clear = lambda: os.system('cls')
app_version = "1.4"

def fit_terminal(min_cols=120, min_lines=30):
    try:
        size = shutil.get_terminal_size()
        cols, lines = size.columns, size.lines

        if cols < min_cols or lines < min_lines:
            os.system(f"mode con: cols={min_cols} lines=999")
    except:
        pass


fit_terminal(130, 35)

print(fr"""
  __  __ _                            __ _     _____      _       _       _   _       _         __  __       _             
 |  \/  (_)                          / _| |   |  __ \    | |     | |     | \ | |     | |       |  \/  |     | |            
 | \  / |_ _ __   ___  ___ _ __ __ _| |_| |_  | |__) |_ _| |_ ___| |__   |  \| | ___ | |_ ___  | \  / | __ _| | _____ _ __ 
 | |\/| | | '_ \ / _ \/ __| '__/ _` |  _| __| |  ___/ _` | __/ __| '_ \  | . ` |/ _ \| __/ _ \ | |\/| |/ _` | |/ / _ \ '__|
 | |  | | | | | |  __/ (__| | | (_| | | | |_  | |  | (_| | || (__| | | | | |\  | (_) | ||  __/ | |  | | (_| |   <  __/ |   
 |_|  |_|_|_| |_|\___|\___|_|  \__,_|_|  \__| |_|   \__,_|\__\___|_| |_| |_| \_|\___/ \__\___| |_|  |_|\__,_|_|\_\___|_|   {app_version}

    Being a lazy dev has never being this easy!
      """)

time.sleep(2)
clear()

def parse_version(version):
    if not version:
        return None

    cleaned = str(version).strip().strip('"\'')
    if not cleaned or cleaned in {"*", "-", "?"}:
        return None

    cleaned = cleaned.lstrip("[<(").rstrip(">)]")
    cleaned = cleaned.split("#", 1)[0].strip()

    parts = re.findall(r"\d+", cleaned)
    if not parts:
        return None

    return [int(part) for part in parts]


def is_newer(v_old, v_new):
    old_parts = parse_version(v_old)
    new_parts = parse_version(v_new)

    if old_parts is None or new_parts is None:
        return False

    return new_parts > old_parts


def _extract_toml_value(line):
    if "=" not in line:
        return ""

    _, raw_value = line.split("=", 1)
    raw_value = raw_value.strip()

    if raw_value.startswith(("'", '"')) and raw_value.endswith(("'", '"')) and len(raw_value) >= 2:
        raw_value = raw_value[1:-1]

    if "#" in raw_value:
        raw_value = raw_value.split("#", 1)[0].strip()

    return raw_value.strip().strip('"\'')


def _format_mod_name(value):
    value = str(value or "").strip().strip('"\'')
    if not value:
        return ""

    value = value.replace("_", " ").replace("-", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_name(name):
    return re.sub(r"\s+", " ", str(name or "").strip().lower())


def _extract_version_from_filename(jar_path):
    basename = os.path.basename(jar_path)
    stem = os.path.splitext(basename)[0]
    candidates = re.findall(r"\d+(?:\.\d+)+", stem)
    if candidates:
        return candidates[-1]
    return ""


def _extract_minecraft_version_from_range(version_range):
    if not version_range:
        return ""

    cleaned = str(version_range).strip().strip('"\'')
    if not cleaned:
        return ""

    cleaned = cleaned.lstrip("[<(\"").rstrip(">)]")
    candidates = [part.strip() for part in cleaned.split(",") if part.strip()]
    if not candidates:
        return ""

    first_value = candidates[0]
    version_match = re.search(r"\d+(?:\.\d+)+", first_value)
    if version_match:
        return version_match.group(0)

    return ""


def _extract_minecraft_version_from_toml(text):
    current_dependency = None
    for line in text.splitlines():
        line = line.strip()
        line = line.split("#", 1)[0].strip()

        if line.startswith("[[") and line.endswith("]]" ):
            current_dependency = None
            continue

        if line.startswith("modId"):
            value = _extract_toml_value(line)
            if value == "minecraft":
                current_dependency = "minecraft"
            else:
                current_dependency = None
            continue

        if current_dependency == "minecraft" and line.startswith("versionRange"):
            return _extract_minecraft_version_from_range(_extract_toml_value(line))

    return ""


def _extract_minecraft_version_from_mcmod_info(jar_path):
    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            for entry in ("mcmod.info", "mcmod.info.json"):
                if entry in jar.namelist():
                    with jar.open(entry) as f:
                        data = json.load(f)

                    if isinstance(data, list) and data:
                        data = data[0]

                    if isinstance(data, dict):
                        return data.get("mcversion") or ""
    except Exception:
        return ""

    return ""


def _extract_minecraft_version_from_fabric_json(jar):
    try:
        namelist = [name for name in jar.namelist()]
        target_files = [name for name in namelist if name.lower().endswith("fabric.mod.json") or name.lower().endswith("quilt.mod.json")]
        if not target_files:
            return ""

        with jar.open(target_files[0]) as f:
            data = json.load(f)

        for section in ("depends", "breaks", "suggests"):
            value = data.get(section)
            if isinstance(value, dict) and "minecraft" in value:
                return _extract_minecraft_version_from_range(value["minecraft"]) or str(value["minecraft"]).strip()

        return ""
    except Exception:
        return ""


def _extract_minecraft_version_from_filename(jar_path):
    basename = os.path.basename(jar_path).lower()

    # Prefer explicit Minecraft version markers such as mc1.21.11 or minecraft-1.21.11.
    mc_match = re.search(r"mc(?:raft)?[-_.]?([0-9]+(?:\.[0-9]+){1,2})", basename)
    if mc_match:
        return mc_match.group(1)

    # If the filename uses a mod version + mc version pattern, use the last numeric version after a plus sign.
    plus_matches = re.findall(r"\+([0-9]+(?:\.[0-9]+){1,2})", basename)
    if plus_matches:
        return plus_matches[-1]

    # Fall back to any standalone 1.x version if explicit mc markers are missing.
    match = re.search(r"(?<!\d)(1\.\d+(?:\.\d+)?)(?!\d)", basename)
    if match:
        return match.group(1)

    return ""


def get_minecraft_version(jar_path):
    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            if "META-INF/mods.toml" in jar.namelist():
                with jar.open("META-INF/mods.toml") as f:
                    text = f.read().decode("utf-8", errors="ignore")
                version = _extract_minecraft_version_from_toml(text)
                if version:
                    return version

            fabric_version = _extract_minecraft_version_from_fabric_json(jar)
            if fabric_version:
                return fabric_version

            mcmod_version = _extract_minecraft_version_from_mcmod_info(jar_path)
            if mcmod_version:
                return mcmod_version

            return _extract_minecraft_version_from_filename(jar_path)
    except Exception:
        return _extract_minecraft_version_from_filename(jar_path)


def infer_minecraft_version(jar_files):
    versions = []
    for jar in jar_files:
        version = get_minecraft_version(jar)
        if version:
            versions.append(version)

    if not versions:
        return ""

    most_common_version, _ = Counter(versions).most_common(1)[0]
    return most_common_version


def _resolve_metadata_value(raw_value, jar_path, mod_id="", display_name=""):
    value = str(raw_value or "").strip().strip('"\'')
    if not value:
        return ""

    if value.startswith("${") and value.endswith("}"):
        placeholder = value[2:-1]

        if placeholder in {"file.jarVersion", "version"}:
            return _extract_version_from_filename(jar_path)

        if placeholder in {"mod_name", "modName"}:
            return display_name or _format_mod_name(mod_id) or ""

        if placeholder in {"mod_id", "modid"}:
            return mod_id or ""

        if placeholder in {"mod_download", "mod_description", "mod_credits", "mod_authors"}:
            return ""

        return ""

    return value


def _read_mcmod_info(jar_path):
    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            for entry in ("mcmod.info", "mcmod.info.json"):
                if entry in jar.namelist():
                    with jar.open(entry) as f:
                        data = json.load(f)

                    if isinstance(data, list) and data:
                        data = data[0]

                    if isinstance(data, dict):
                        return {
                            "name": data.get("name") or data.get("modid") or "Nom introuvable",
                            "version": data.get("version") or "0"
                        }
    except Exception:
        return None

    return None


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

            mcmod_info = _read_mcmod_info(jar_path)
            if mcmod_info:
                return {
                    "name": _format_mod_name(mcmod_info.get("name", "Nom introuvable")) or "Nom introuvable",
                    "version": mcmod_info.get("version", "0")
                }

            # Forge / NeoForge
            if "META-INF/mods.toml" in jar.namelist():
                with jar.open("META-INF/mods.toml") as f:
                    text = f.read().decode("utf-8", errors="ignore")

                name = "Nom introuvable"
                version = "0"
                mod_id = ""
                in_mod_section = False

                for line in text.splitlines():
                    line = line.strip()
                    line = line.split("#", 1)[0].strip()

                    if line.startswith("[[") and line.endswith("]]" ):
                        if in_mod_section:
                            break
                        if line == "[[mods]]":
                            in_mod_section = True
                        continue

                    if not in_mod_section:
                        continue

                    if not line:
                        continue

                    if line.startswith("modId"):
                        mod_id = _extract_toml_value(line)

                    if line.startswith("displayName"):
                        name = _resolve_metadata_value(_extract_toml_value(line), jar_path, mod_id, name)

                    if line.startswith("version") and not line.startswith("versionRange"):
                        version = _resolve_metadata_value(_extract_toml_value(line), jar_path, mod_id, name)

                if not name or name == "Nom introuvable":
                    name = mod_id or name

                if not version or version in {"0", "*", "-", "?"}:
                    version = _extract_version_from_filename(jar_path)

                return {"name": name, "version": version}

            return {"name": "Inconnu", "version": "0"}

    except Exception as e:
        return {"name": f"Erreur: {e}", "version": "0"}


def build_mod_dict(jar_files):
    mods = {}
    for jar in jar_files:
        info = get_mod_info(jar)
        key = normalize_name(info["name"])
        mods[key] = {
            "name": info["name"],
            "version": info["version"]
        }
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

old_mc_version = ""
new_mc_version = ""

old_mc_version = infer_minecraft_version(jar_files_old)
new_mc_version = infer_minecraft_version(jar_files_new)

added = []
removed = []
updated = []

# --- comparaison ---
for normalized_name, new_mod in new_mods.items():
    old_mod = old_mods.get(normalized_name)
    if old_mod is None:
        added.append((new_mod["name"], new_mod["version"]))
    else:
        old_version = old_mod["version"]
        new_version = new_mod["version"]
        if is_newer(old_version, new_version):
            updated.append((new_mod["name"], old_version, new_version))

for normalized_name, old_mod in old_mods.items():
    if normalized_name not in new_mods:
        removed.append((old_mod["name"], old_mod["version"]))

# --- dev note ---
if click.confirm("Do you want to add a note to this patch note?", default=True):
    dev_not = click.prompt("Enter your note", type=str)
    dev_not_bool = True
else:
    dev_not_bool = False

# --- display ---
print("\n# === MINECRAFT VERSION ===")
if old_mc_version and new_mc_version:
    if old_mc_version != new_mc_version:
        print(f"{old_mc_version} → {new_mc_version}")
    else:
        print(new_mc_version)
else:
    print("Unable to determine Minecraft version.")

print("\n## === MODS ADDED ===")
if added:
    for m in added:
        print(f"+ {m[0]} ({m[1]})")
else:
    print("No mods added.")

print("\n## === DELETED MODS ===")
if removed:
    for m in removed:
        print(f"- {m[0]} ({m[1]})")
else:
    print("No mods deleted.")

print("\n## === UPDATED MODS ===")
if updated:
    for m in updated:
        print(f"+ {m[0]} : {m[1]} → {m[2]}")
else:
    print("No mods updated.")

print("\n## === DEV NOTE ===")
if dev_not_bool == True:
    print(dev_not)
else :
    print("No note added.")

print("\nMade with 'Minecraft Patch Note Maker' by @5UP3RTH30B4G (github.com/5UP3RTH30B4G)")

input("\nPress Enter to exit...")