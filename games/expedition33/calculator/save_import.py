from __future__ import annotations

import base64
import binascii
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from typing import Any, TypedDict
import unicodedata

from games.expedition33.calculator.core import CALCULATOR_DATA, DEFAULT_CHARACTER
from games.expedition33.calculator.pictos import PICTO_DEFINITIONS
from games.expedition33.calculator.weapons import WEAPON_DEFINITIONS, normalize_weapon_level


class SaveImportError(RuntimeError):
    """Raised when a save file cannot be converted or normalized."""


class ImportedCharacterBuild(TypedDict):
    """Normalized calculator-facing build data for one character."""

    save_name: str
    level: int
    lumina_from_consumables: int
    attributes: dict[str, int]
    raw_equipped_weapon: str | None
    equipped_weapon: str | None
    raw_weapon_level: int | None
    weapon_level: str
    raw_equipped_skills: list[str]
    equipped_skills: list[str]
    unmatched_skills: list[str]
    raw_equipped_pictos: list[str]
    equipped_pictos: list[str]
    unmatched_pictos: list[str]


class SaveImportPayload(TypedDict):
    """Serializable payload stored in Dash after a save import."""

    filename: str
    preferred_character: str
    warnings: list[str]
    characters: dict[str, ImportedCharacterBuild]


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_UESAVE_BINARIES = {
    ("Linux", "x86_64"): ROOT_DIR / "tools" / "uesave" / "uesave_cli-x86_64-unknown-linux-gnu" / "uesave",
}
ATTRIBUTE_LABELS = {
    0: "Vitality",
    1: "Strength",
    2: "Intelligence",
    3: "Agility",
    4: "Defense",
    5: "Luck",
}
SAVE_CHARACTER_TO_CALCULATOR = {
    "Frey": "gustave",
    "Gustave": "gustave",
    "Lune": "lune",
    "Maelle": "maelle",
    "Monoco": "monoco",
    "Sciel": "sciel",
    "Verso": "verso",
}
WEAPON_NAME_ALIASES = {
    "Sirenim_1": "Choralim",
    "Sirenim_2": "Colim",
    "Reacherim_2": "Lithelim",
    "Dualim": "Troubadim",
    "Troubadum": "Chalium",
    "Reacharo_2": "Fragaro",
    "Sireso_2": "Dreameso",
    "Chaliso": "Dualiso",
    "Reacheso_2": "Liteso",
}
PICTO_NAME_ALIASES = {
    "LastStand": "At Death's Door",
    "AugmentedAim": "Augmented Aim",
    "AugmentedAttack": "Augmented Attack",
    "CounterUpdragdeA": "Augmented Counter I",
    "CounterUpdragdeB": "Augmented Counter II",
    "CounterUpdragdeC": "Augmented Counter III",
    "Augmented1stStrike": "Augmented First Strike",
    "BreakSpecialist": "Break Specialist",
    "BurnAffinity": "Burn Affinity",
    "ConfidentFighter": "Confident Fighter",
    "PowerDodgeCombo": "Empowering Dodge",
    "ReinforcementParade": "Empowering Parry",
    "ExhaustAffinity": "Exhausting Power",
    "FirstOffensive": "First Offensive",
    "Stand": "Full Strength",
    "GlassCanon": "Glass Cannon",
    "GradientFighter": "Gradient Fighter",
    "Immaculate": "Immaculate",
    "InvertedAffinity": "Inverted Affinity",
    "PiercingShot": "Piercing Shot",
    "FullEnergyAttack": "Powered Attack",
    "PowerfulShield": "Powerful Shield",
    "ShieldAffinity": "Shield Affinity",
    "SoloFighter": "Solo Fighter",
    "StunBoost": "Stun Boost",
    "Tainted": "Tainted",
    "Teamwork": "Teamwork",
    "Warming": "Warming Up",
}
MONOCO_SKILL_ALIASES = {
    "AbbestMelee": "Abbest Wind",
    "AberrationBurningLight": "Abberation Light",
    "BalletCharm": "Ballet Charm",
    "BenisseurMortar": "Benissuer Mortar",
    "BoucheclierShield": "Bouchelier Fortify",
    "HammerSmash": "Braseleur Smash",
    "BrulerAnchorSmash": "Bruler Bash",
    "ChalierRelentlessSword": "Chalier Combo",
    "ChapelierAxeSlash": "Chapelier Slash",
    "ChevaliereCAOECombo": "Chevaliere Ice",
    "ChevaliereCAC": "Chevaliere Piercing",
    "ChevaliereBAoECombo": "Chevaliere Thrusts",
    "ClairEnfeeble": "Clair Enfeeble",
    "ContorsionnisteAngryBlast": "Contorsionniste Blast",
    "CreationFromTheVoid": "Creation Void",
    "CrulerShield": "Cruler Barrier",
    "HeavyCultistBloodSword": "Cultist Blood",
    "FlyingSlashes": "Cultists Slashes",
    "DanseuseWingDance": "Danseuse Waltz",
    "DemineurThunderStrike": "Demineur Thunder",
    "StormBlood": "Duallist Storm",
    "EchassierCombo": "Echassier Stabs",
    "EvequeSpear": "Eveque Spear",
    "GaultCombo": "Gault Fury",
    "GlaiseEarthquakes": "Glaise Earthquakes",
    "GrosseTeteWrecking": "Grosse Tete Whack",
    "HexgaCombo": "Hexga Crush",
    "JarCombo": "Jar Lampstorm",
    "LampmasterSwordOfLight": "Lampmaster Light 0",
    "LancelierEstoc": "Lancelier Impale",
    "LusterCombo": "Luster Slices",
    "MoissonneuseVendange": "Moissonneuse Vendange",
    "ObscurCombo": "Obscur Sword",
    "OrphelinBuff": "Orphelin Cheers",
    "PortierCrashingDown": "Portier Crash",
    "PotierBuff": "Potier Energy",
    "PelerinFreshAir": "Perelin Heal",
    "RamasseurBonk": "Ramasseur Bonk",
    "RocherHammering": "Rocher Hammering",
    "ThunderEstoc": "Sakapate Estoc",
    "ThunderThrows": "Sakapate Explosion",
    "PotatobagBossFireShots": "Sakapate Fire",
    "PotatobagSlam": "Sakapate Slam",
    "SaplingAbsorption": "Sapling Absorbtion",
    "StalactCombo": "Stalact Punches",
    "Trumpet": "Troubadour Trumpet",
    "MightyStrike": "Mighty Strike",
    "Sanctuary": "Sanctuary",
    "BreakPoint": "Breakpoint",
}
SKILL_NAME_ALIASES = {
    "gustave": {
        "UnleashCharge": "Overcharge 0 Charges",
        "Combo1_Gustave": "Basic Attack",
    },
    "lune": {
        "IceGust": "Ice Lance",
    },
    "sciel": {
        "Grimprediction": "Grim Harvest",
        "Foretelling2": "Focused Foretell",
    },
    "monoco": MONOCO_SKILL_ALIASES,
}
SKILL_LOOKUPS = {
    character: {
        re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", skill).encode("ascii", "ignore").decode("ascii").lower()): skill
        for skill in CALCULATOR_DATA[character]["skills"]
    }
    for character in CALCULATOR_DATA
}


def decode_upload_contents(contents: str) -> bytes:
    """Decode Dash upload contents into raw save bytes."""

    _, _, encoded = contents.partition(",")
    if not encoded:
        raise SaveImportError("Upload payload was empty.")

    try:
        return base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise SaveImportError("Uploaded file could not be base64-decoded.") from exc


def parse_uploaded_save(contents: str, filename: str | None = None) -> SaveImportPayload:
    """Convert uploaded `.sav` contents into normalized calculator state."""

    save_bytes = decode_upload_contents(contents)
    save_json = convert_save_bytes_to_json(save_bytes)
    payload = build_import_payload(save_json, filename or "uploaded.sav")
    if not payload["characters"]:
        raise SaveImportError("No supported Expedition 33 characters were found in the uploaded save.")
    return payload


def convert_save_bytes_to_json(save_bytes: bytes) -> dict[str, Any]:
    """Run the official uesave CLI against raw bytes and parse the JSON output."""

    executable = resolve_uesave_binary()
    process = subprocess.run(
        [str(executable), "to-json", "--no-warn", "-i", "-", "-o", "-"],
        input=save_bytes,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        error_text = process.stderr.decode("utf-8", errors="replace").strip()
        raise SaveImportError(error_text or "uesave failed to parse the uploaded save.")

    try:
        return json.loads(process.stdout.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise SaveImportError("uesave returned invalid JSON for the uploaded save.") from exc


def resolve_uesave_binary() -> Path:
    """Locate the bundled or user-provided uesave executable."""

    for env_name in ("UESAVE_BIN", "LUDEx_UESAVE_BIN", "LUDEX_UESAVE_BIN"):
        env_value = os.environ.get(env_name)
        if env_value:
            candidate = Path(env_value).expanduser()
            if candidate.is_file():
                return candidate

    bundled = DEFAULT_UESAVE_BINARIES.get((platform.system(), platform.machine()))
    if bundled and bundled.is_file():
        return bundled

    system_binary = shutil.which("uesave")
    if system_binary:
        return Path(system_binary)

    raise SaveImportError(
        "No compatible uesave binary was found. Set UESAVE_BIN to a valid executable path."
    )


def build_import_payload(save_json: dict[str, Any], filename: str) -> SaveImportPayload:
    """Normalize raw uesave JSON into the subset the calculator understands."""

    properties = save_json.get("root", {}).get("properties", {})
    characters_map = list_entries(properties.get("CharactersCollection_0"))
    weapon_levels = extract_weapon_levels(properties)
    imported_characters: dict[str, ImportedCharacterBuild] = {}

    for entry in characters_map:
        if not isinstance(entry, dict):
            continue
        save_name = clean_name(read_name_value(entry.get("key")))
        character = SAVE_CHARACTER_TO_CALCULATOR.get(save_name)
        if not character:
            continue

        struct = struct_value(entry.get("value"))
        imported_characters[character] = parse_character_build(character, save_name, struct, weapon_levels)

    preferred_character = next(
        (character for character in CALCULATOR_DATA if character in imported_characters),
        DEFAULT_CHARACTER,
    )
    return {
        "filename": filename,
        "preferred_character": preferred_character,
        "warnings": [
            "Attack Power is not stored directly in the save schema, so the calculator attack input remains manual.",
        ],
        "characters": imported_characters,
    }


def extract_weapon_levels(properties: dict[str, Any]) -> dict[str, int]:
    """Build a raw item-id to level mapping from the save payload."""

    progressions = list_entries(properties.get("WeaponProgressions_0"))
    levels: dict[str, int] = {}
    for entry in progressions:
        struct = struct_value(entry)
        raw_name = clean_name(read_name_field(struct, "DefinitionID_"))
        if not raw_name:
            continue
        levels[raw_name] = read_int_field(struct, "CurrentLevel_")
    return levels


def parse_character_build(
    character: str,
    save_name: str,
    struct: dict[str, Any],
    weapon_levels: dict[str, int],
) -> ImportedCharacterBuild:
    """Extract the fields used by the calculator from one character payload."""

    raw_weapon = extract_equipped_weapon(struct)
    matched_weapon = match_weapon_name(character, raw_weapon)
    raw_level = weapon_levels.get(raw_weapon) if raw_weapon else None
    matched_skills, unmatched_skills = match_skill_names(character, extract_name_array(struct, "EquippedSkills_"))
    matched_pictos, unmatched_pictos = match_picto_names(extract_name_array(struct, "EquippedPassiveEffects_"))

    return {
        "save_name": save_name,
        "level": read_int_field(struct, "CurrentLevel_"),
        "lumina_from_consumables": read_int_field(struct, "LuminaFromConsumables_"),
        "attributes": extract_attributes(struct),
        "raw_equipped_weapon": raw_weapon,
        "equipped_weapon": matched_weapon,
        "raw_weapon_level": raw_level,
        "weapon_level": str(normalize_weapon_level(raw_level or 0)),
        "raw_equipped_skills": extract_name_array(struct, "EquippedSkills_"),
        "equipped_skills": matched_skills,
        "unmatched_skills": unmatched_skills,
        "raw_equipped_pictos": extract_name_array(struct, "EquippedPassiveEffects_"),
        "equipped_pictos": matched_pictos,
        "unmatched_pictos": unmatched_pictos,
    }


def extract_equipped_weapon(struct: dict[str, Any]) -> str | None:
    """Read the first equipped weapon id from the save structure."""

    slots = list_entries(read_prefixed_field(struct, "EquippedItemsPerSlot_"))
    fallback: str | None = None
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        value = clean_name(read_name_value(slot.get("value")))
        if not value or value.lower() == "none":
            continue
        if is_weapon_slot(slot.get("key")):
            return value
        if fallback is None:
            fallback = value
    return fallback


def extract_attributes(struct: dict[str, Any]) -> dict[str, int]:
    """Parse the assigned attribute map into stable display labels."""

    attributes: dict[str, int] = {}
    entries = list_entries(read_prefixed_field(struct, "AssignedAttributePoints_"))
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        label = clean_name(read_attribute_key(entry.get("key")))
        match = re.search(r"(\d+)$", label)
        if not match:
            continue
        attr_label = ATTRIBUTE_LABELS.get(int(match.group(1)))
        if not attr_label:
            continue
        attributes[attr_label] = read_int_value(entry.get("value"))
    return attributes


def extract_name_array(struct: dict[str, Any], prefix: str) -> list[str]:
    """Read a NameProperty array from a prefixed save field."""

    names: list[str] = []
    for item in list_entries(read_prefixed_field(struct, prefix)):
        name = clean_name(read_name_value(item))
        if name:
            names.append(name)
    return names


def match_weapon_name(character: str, raw_name: str | None) -> str | None:
    """Translate a save weapon id into the calculator's supported weapon label."""

    if not raw_name:
        return None
    translated = WEAPON_NAME_ALIASES.get(raw_name, raw_name)
    return translated if translated in WEAPON_DEFINITIONS.get(character, {}) else None


def match_picto_names(raw_names: list[str]) -> tuple[list[str], list[str]]:
    """Translate equipped passive ids into calculator Picto labels."""

    matched: list[str] = []
    unmatched: list[str] = []
    for raw_name in raw_names:
        translated = PICTO_NAME_ALIASES.get(raw_name, raw_name)
        if translated in PICTO_DEFINITIONS and translated not in matched:
            matched.append(translated)
        elif raw_name not in unmatched:
            unmatched.append(raw_name)
    return matched, unmatched


def match_skill_names(character: str, raw_names: list[str]) -> tuple[list[str], list[str]]:
    """Match save skill ids against the calculator CSV names."""

    matched: list[str] = []
    unmatched: list[str] = []
    for raw_name in raw_names:
        translated = match_skill_name(character, raw_name)
        if translated and translated not in matched:
            matched.append(translated)
        elif raw_name not in unmatched:
            unmatched.append(raw_name)
    return matched, unmatched


def match_skill_name(character: str, raw_name: str) -> str | None:
    """Resolve one raw save skill id into a calculator skill name."""

    aliases = SKILL_NAME_ALIASES.get(character, {})
    if raw_name in aliases and aliases[raw_name] in CALCULATOR_DATA[character]["skills"]:
        return aliases[raw_name]

    lookup = SKILL_LOOKUPS[character]
    candidates = {
        raw_name,
        raw_name.replace("_", " "),
        re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw_name),
        re.sub(r"_?(gustave|frey|lune|maelle|monoco|sciel|verso)$", "", raw_name, flags=re.IGNORECASE),
        re.sub(r"\d+$", "", raw_name),
    }
    for candidate in candidates:
        normalized = normalize_text(candidate)
        if normalized in lookup:
            return lookup[normalized]
    return None


def read_prefixed_field(struct: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Return the first nested field whose key starts with the requested prefix."""

    for key, value in struct.items():
        if key.startswith(prefix):
            return value
    return {}


def read_name_field(struct: dict[str, Any], prefix: str) -> str:
    """Read a NameProperty value by field prefix."""

    return clean_name(read_name_value(read_prefixed_field(struct, prefix)))


def read_int_field(struct: dict[str, Any], prefix: str) -> int:
    """Read an IntProperty value by field prefix."""

    return read_int_value(read_prefixed_field(struct, prefix))


def list_entries(value: Any) -> list[Any]:
    """Return list-like save payloads in either raw-uesave or mapped-json form."""

    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []
    if "Map" in value and isinstance(value["Map"], list):
        return value["Map"]
    if "Array" in value:
        array_value = value["Array"]
        if isinstance(array_value, dict):
            base_value = array_value.get("Base")
            if isinstance(base_value, dict) and isinstance(base_value.get("Name"), list):
                return base_value["Name"]
            struct_value = array_value.get("Struct")
            if isinstance(struct_value, dict) and isinstance(struct_value.get("value"), list):
                return struct_value["value"]
    return []


def struct_value(value: Any) -> dict[str, Any]:
    """Extract a struct payload from either raw or nested mapped JSON."""

    if isinstance(value, dict):
        if "Struct" in value and isinstance(value["Struct"], dict):
            nested = value["Struct"]
            if "Struct" in nested and isinstance(nested["Struct"], dict):
                return nested["Struct"]
            return nested
        return value
    return {}


def read_name_value(value: Any) -> str:
    """Read a name/string value across raw and mapped save payloads."""

    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if isinstance(value.get("Name"), str):
            return value["Name"]
    return ""


def read_int_value(value: Any) -> int:
    """Read an integer value across raw and mapped save payloads."""

    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, dict):
        if "Int" in value:
            return read_int_value(value["Int"])
        if "value" in value:
            return read_int_value(value["value"])
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def read_attribute_key(value: Any) -> str:
    """Read an attribute enum key across raw and mapped save payloads."""

    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        byte_value = value.get("Byte")
        if isinstance(byte_value, dict) and isinstance(byte_value.get("Label"), str):
            return byte_value["Label"]
    return ""


def is_weapon_slot(value: Any) -> bool:
    """Return whether an equipped-item slot corresponds to the weapon slot."""

    if not isinstance(value, dict):
        return False
    for key, item_value in value.items():
        if key.startswith("ItemType_"):
            item_type = clean_name(read_name_value(item_value) or item_value)
            return item_type.endswith("NewEnumerator0")
    return False


def clean_name(value: Any) -> str:
    """Coerce a raw save field into a clean display string."""

    return str(value or "").strip()


def normalize_text(value: str) -> str:
    """Normalize identifiers for fuzzy matching across save and CSV names."""

    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.lower())
