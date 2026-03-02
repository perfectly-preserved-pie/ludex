from __future__ import annotations

from pathlib import Path
import re
from typing import Any, TypeAlias, TypedDict

from dash import Input, Output, callback, dcc, html, register_page
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd

from games.expedition33.helpers import clean_frame, format_value

CalculatorRow: TypeAlias = dict[str, Any]
CalculatorState: TypeAlias = dict[str, Any]
ComponentChildren: TypeAlias = list[Any]
SkillOption: TypeAlias = dict[str, str]
StyleRule: TypeAlias = dict[str, str]
CharacterStyles: TypeAlias = dict[str, StyleRule]
NumericInput: TypeAlias = int | float | None
ToggleInput: TypeAlias = bool | None
ControlStyles: TypeAlias = dict[str, StyleRule]


class CalculationResult(TypedDict):
    """Normalized payload describing the selected damage scenario."""
    multiplier: float | None
    scenario: str
    source: str
    warning: str | None


class SheetScenario(TypedDict):
    """A spreadsheet breakpoint displayed in the summary table."""
    label: str
    value: float


class CalculatorPayload(TypedDict):
    """Loaded calculator data for a single character."""
    default_attack: float
    records: list[CalculatorRow]
    skills: dict[str, CalculatorRow]

CSV_DIR = Path(__file__).resolve().parents[2] / "assets" / "expedition33" / "clair_skill_damage"

CHARACTER_META = {
    "gustave": {"label": "Gustave"},
    "lune": {"label": "Lune"},
    "maelle": {"label": "Maelle"},
    "monoco": {"label": "Monoco"},
    "sciel": {"label": "Sciel"},
    "verso": {"label": "Verso"},
}

DEFAULT_CHARACTER = "lune"
DEFAULT_SKILLS = {
    "gustave": "Overcharge 0 Charges",
    "lune": "Lightning Dance",
    "maelle": "Burning Canvas",
    "monoco": "Sakapate Estoc",
    "sciel": "End Slice",
    "verso": "Strike Storm",
}
RANK_ORDER = {"D": 0, "C": 1, "B": 2, "A": 3, "S": 4}
VISIBLE_STYLE: StyleRule = {}
HIDDEN_STYLE: StyleRule = {"display": "none"}


def compact(children: ComponentChildren) -> ComponentChildren:
    """Remove placeholder entries from a component list."""
    return [child for child in children if child is not None]


def clean_text(value: Any) -> str:
    """Convert raw CSV values into trimmed display-safe strings."""
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_number(value: Any) -> float | None:
    """Parse a numeric cell value while tolerating sheet punctuation."""
    if value is None:
        return None
    if isinstance(value, (int, float)) and not pd.isna(value):
        return float(value)

    text = clean_text(value).replace(",", "").replace("?", "")
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def extract_first_int(value: Any) -> int | None:
    """Extract the first integer embedded in a condition string."""
    match = re.search(r"(\d+)", clean_text(value))
    return int(match.group(1)) if match else None


def number_from_row(row: CalculatorRow, *keys: str) -> float | None:
    """Return the first parseable numeric value from the provided columns."""
    for key in keys:
        number = parse_number(row.get(key))
        if number is not None:
            return number
    return None


def text_from_row(row: CalculatorRow, *keys: str) -> str:
    """Return the first non-empty text value from the provided columns."""
    for key in keys:
        text = clean_text(row.get(key))
        if text:
            return text
    return ""


def clamp_int(value: Any, minimum: int, maximum: int) -> int:
    """Clamp user input to an integer range used by calculator controls."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, min(number, maximum))


def format_multiplier(value: float | None) -> str:
    """Format a damage multiplier for result-card display."""
    if value is None:
        return "-"
    text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{text}x"


def calculate_damage(attack: float | None, multiplier: float | None) -> float | None:
    """Convert attack and multiplier values into estimated damage."""
    if attack is None or multiplier is None:
        return None
    return round(attack * multiplier, 2)


def base_result(
    row: CalculatorRow,
    scenario: str | None = None,
    source: str = "Damage Multi",
) -> CalculationResult:
    """Build the default result payload for a skill row."""
    condition = text_from_row(row, "Condition 1", "Condition")
    return {
        "multiplier": number_from_row(row, "Damage Multi"),
        "scenario": scenario or ("Base value" if not condition else f"Base value | breakpoint: {condition}"),
        "source": source,
        "warning": None,
    }


def result(
    multiplier: float | None,
    scenario: str,
    source: str,
    warning: str | None = None,
) -> CalculationResult:
    """Build a normalized result payload for a calculated scenario."""
    return {
        "multiplier": multiplier,
        "scenario": scenario,
        "source": source,
        "warning": warning,
    }


def load_calculator_data() -> dict[str, CalculatorPayload]:
    """Load and normalize every character CSV into calculator-friendly payloads."""
    payloads: dict[str, CalculatorPayload] = {}

    for character in CHARACTER_META:
        frame = clean_frame(pd.read_csv(CSV_DIR / f"{character}.csv"))
        frame = frame.dropna(subset=["Skill"]).copy()
        safe_frame = frame.astype(object).where(pd.notnull(frame), None)

        records: list[CalculatorRow] = []
        for record in safe_frame.to_dict("records"):
            skill = clean_text(record.get("Skill"))
            if not skill or skill.lower().startswith("skill tierlist"):
                continue
            record["Skill"] = skill
            records.append(record)

        default_attack = None
        for key in ("Test Basic Attack Dmg", "Base Attack", "Test Basic Attack"):
            for record in records:
                value = parse_number(record.get(key))
                if value is not None and value > 0:
                    default_attack = value
                    break
            if default_attack is not None:
                break

        payloads[character] = {
            "default_attack": float(default_attack or 1000),
            "records": records,
            "skills": {record["Skill"]: record for record in records},
        }

    return payloads


CALCULATOR_DATA: dict[str, CalculatorPayload] = load_calculator_data()


def skill_options_for(character: str) -> list[SkillOption]:
    """Build the dropdown option list for a character's skills, sorted alphabetically."""
    return sorted(
        [
        {"label": record["Skill"], "value": record["Skill"]}
        for record in CALCULATOR_DATA[character]["records"]
        ],
        key=lambda option: option["label"].lower(),
    )


def get_row(character: str, skill: str | None) -> CalculatorRow:
    """Return the selected skill row, falling back to the character default."""
    skills: dict[str, CalculatorRow] = CALCULATOR_DATA[character]["skills"]
    if skill in skills:
        return skills[skill]

    fallback_skill = DEFAULT_SKILLS.get(character)
    if fallback_skill in skills:
        return skills[fallback_skill]

    return CALCULATOR_DATA[character]["records"][0]


def parse_rank_requirement(value: str) -> str | None:
    """Extract a Verso rank requirement from a condition label."""
    match = re.search(r"\b([DCBAS])\b", clean_text(value))
    if not match:
        return None
    rank = match.group(1)
    return rank if rank in RANK_ORDER else None


def rank_at_least(current_rank: str, required_rank: str | None) -> bool:
    """Check whether the current Verso rank satisfies a rank gate."""
    if required_rank is None:
        return False
    return RANK_ORDER.get(current_rank, -1) >= RANK_ORDER.get(required_rank, 99)


def build_sheet_rows(row: CalculatorRow) -> list[SheetScenario]:
    """Collect the distinct sheet breakpoints shown in the summary card."""
    entries: list[SheetScenario] = []
    def add_entry(label: str, value: float | None) -> None:
        """Append a unique spreadsheet scenario to the summary list."""

        if value is None:
            return
        if any(existing["label"] == label and existing["value"] == value for existing in entries):
            return
        entries.append({"label": label, "value": value})

    add_entry("Base", number_from_row(row, "Damage Multi"))

    conditional_value = number_from_row(row, "Dmg Con1", "ConDmg")
    conditional_label = text_from_row(row, "Condition 1", "Condition")
    if conditional_value is not None and conditional_value != number_from_row(row, "Damage Multi"):
        add_entry(conditional_label or "Conditional", conditional_value)

    maelle_value = number_from_row(row, "DmMax")
    maelle_label = text_from_row(row, "Condition")
    if maelle_value is not None and maelle_value != number_from_row(row, "Damage Multi"):
        add_entry(maelle_label or "Maximum", maelle_value)

    max_value = number_from_row(row, "Dmg Max", "TwilightDmg", "SRankMAX")
    max_label = text_from_row(row, "Con Max Dmg", "ConTwilight")
    if max_value is not None:
        if "TwilightDmg" in row and max_value == number_from_row(row, "TwilightDmg"):
            add_entry(max_label or "Twilight", max_value)
        elif "SRankMAX" in row and max_value == number_from_row(row, "SRankMAX"):
            add_entry(max_label or "S Rank", max_value)
        elif max_value != number_from_row(row, "Damage Multi"):
            add_entry(max_label or "Maximum", max_value)

    return entries


def calculate_current_cost(character: str, row: CalculatorRow, state: CalculatorState) -> str:
    """Return the displayed AP cost after character-specific modifiers."""
    raw_cost = clean_text(row.get("Cost"))
    numeric_cost = parse_number(row.get("Cost"))
    skill = clean_text(row.get("Skill"))

    if numeric_cost is None:
        return raw_cost or "-"

    if character == "maelle" and state.get("stance") == "Virtuoso" and skill in {"Momentum Strike", "Percee"}:
        return format_value(max(numeric_cost - 3, 0))

    if character == "verso":
        rank = clean_text(state.get("rank")) or "D"
        if skill in {"Follow Up", "Ascending Assault"} and rank == "S":
            return "2"
        if skill == "Perfect Break" and rank_at_least(rank, "B"):
            return "5"

    return format_value(numeric_cost)


def calculate_gustave(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Gustave skill damage from charge-based state."""
    skill = clean_text(row.get("Skill"))
    if skill.startswith("Overcharge"):
        charges = clamp_int(state.get("charges"), 0, 10)
        overcharge_base = 2.1
        multiplier = overcharge_base * (1 + (0.2 * charges))
        if charges >= 10:
            multiplier *= 1.25
        return result(round(multiplier, 2), f"{charges} Charges", "Derived from Overcharge note")

    return base_result(row)


def calculate_lune(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Lune skill damage from stain, turn, and crit state."""
    skill = clean_text(row.get("Skill"))
    base_multiplier = number_from_row(row, "Damage Multi")
    conditional = number_from_row(row, "Dmg Con1")
    maximum = number_from_row(row, "Dmg Max")
    condition = text_from_row(row, "Condition 1").lower()
    max_condition = text_from_row(row, "Con Max Dmg").lower()
    stains = clamp_int(state.get("stains"), 0, 4)
    turns = clamp_int(state.get("turns"), 1, 5)
    all_crits = bool(state.get("all_crits"))

    if skill.startswith("Burn "):
        ticks = clamp_int(state.get("turns"), 1, 3)
        return result(round((base_multiplier or 0) * ticks, 2), f"{ticks} Burn tick(s)", "Derived from burn rows")

    if condition == "turn start dmg" and stains > 0 and conditional is not None:
        total = round((base_multiplier or 0) + (conditional * turns), 2)
        return result(total, f"{turns} turn(s) with stains", "Derived from Damage Multi + Dmg Con1")

    if skill == "Fire Rage":
        if turns >= 3 and maximum is not None:
            return result(maximum, "Turn 3", "Dmg Max")
        if turns >= 2 and conditional is not None:
            return result(conditional, "Turn 2", "Dmg Con1")
        return base_result(row, "Turn 1")

    if skill == "Fire Rage Stained":
        if turns >= 3 and stains >= 1 and maximum is not None:
            return result(maximum, "Stained Turn 3", "Dmg Max")
        if turns >= 2 and stains >= 2 and conditional is not None:
            return result(conditional, "2 Stains on Turn 2", "Dmg Con1")
        return base_result(row, "Turn 1")

    max_threshold = extract_first_int(max_condition)
    cond_threshold = extract_first_int(condition)

    if maximum is not None:
        if "crit" in max_condition and all_crits and (max_threshold is None or stains >= max_threshold):
            return result(maximum, text_from_row(row, "Con Max Dmg") or "Maximum", "Dmg Max")
        if "burn" in max_condition and turns >= 3 and (max_threshold is None or stains >= max_threshold):
            return result(maximum, text_from_row(row, "Con Max Dmg") or "Maximum", "Dmg Max")
        if "t3" in max_condition and turns >= 3:
            return result(maximum, text_from_row(row, "Con Max Dmg") or "Maximum", "Dmg Max")
        if max_threshold is not None and "stain" in max_condition and stains >= max_threshold:
            return result(maximum, text_from_row(row, "Con Max Dmg") or "Maximum", "Dmg Max")

    if conditional is not None:
        if "t2" in condition and turns >= 2:
            return result(conditional, text_from_row(row, "Condition 1") or "Conditional", "Dmg Con1")
        if cond_threshold is not None and "stain" in condition and stains >= cond_threshold:
            return result(conditional, text_from_row(row, "Condition 1") or "Conditional", "Dmg Con1")
        if condition.startswith("grad"):
            return result(conditional, text_from_row(row, "Condition 1") or "Conditional", "Dmg Con1")

    return base_result(row)


def calculate_maelle(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Maelle skill damage from burn, marked, and hit-based state."""
    skill = clean_text(row.get("Skill"))
    base_multiplier = number_from_row(row, "Damage Multi")
    maximum = number_from_row(row, "DmMax")
    stance = clean_text(state.get("stance")) or "Stanceless"
    burn_stacks = clamp_int(state.get("burn_stacks"), 0, 100)
    hits_taken = clamp_int(state.get("hits_taken"), 0, 5)
    marked = bool(state.get("marked"))
    all_crits = bool(state.get("all_crits"))
    turns = clamp_int(state.get("turns"), 1, 3)

    def with_stance(skill_result: CalculationResult) -> CalculationResult:
        """Apply Maelle's offensive or virtuoso stance multiplier to hit damage."""
        multiplier = skill_result.get("multiplier")
        stance_multiplier = {
            "Offensive": 1.5,
            "Virtuoso": 3.0,
        }.get(stance)

        if multiplier is None or stance_multiplier is None or skill.startswith("Burn "):
            return skill_result

        return result(
            round(multiplier * stance_multiplier, 2),
            f"{skill_result['scenario']} | {stance} stance",
            f"{skill_result['source']} + stance bonus",
            skill_result.get("warning"),
        )

    if skill == "Burning Canvas":
        multiplier = round((base_multiplier or 0) * (1 + (0.1 * burn_stacks)), 2)
        return with_stance(result(multiplier, f"{burn_stacks} Burn stack(s)", "Derived from note text"))

    if skill == "Combustion":
        multiplier = round((base_multiplier or 0) * (1 + (0.4 * min(burn_stacks, 10))), 2)
        return with_stance(result(multiplier, f"Consume {min(burn_stacks, 10)} Burn", "Derived from note text"))

    if skill == "Revenge":
        multiplier = round((base_multiplier or 0) * (1 + (1.5 * hits_taken)), 2)
        return with_stance(result(multiplier, f"{hits_taken} hit(s) taken last round", "Derived from note text"))

    if skill.startswith("Burn "):
        return result(round((base_multiplier or 0) * turns, 2), f"{turns} Burn tick(s)", "Derived from burn rows")

    if skill in {"G-Homage", "Momentum Strike", "Percee"} and marked and maximum is not None:
        return with_stance(result(maximum, "Marked target", "DmMax"))

    if skill == "Sword Ballet" and all_crits and maximum is not None:
        return with_stance(result(maximum, "All crits", "DmMax"))

    return with_stance(base_result(row))


def calculate_monoco(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Monoco skill damage from mask and target status state."""
    skill = clean_text(row.get("Skill"))
    base_multiplier = number_from_row(row, "Damage Multi")
    conditional = number_from_row(row, "Dmg Con1")
    maximum = number_from_row(row, "Dmg Max")
    mask_active = bool(state.get("mask_active"))
    turns = clamp_int(state.get("turns"), 1, 3)
    stunned = bool(state.get("stunned"))
    marked = bool(state.get("marked"))
    powerless = bool(state.get("powerless"))
    burning = bool(state.get("burning"))
    low_life = bool(state.get("low_life"))
    full_life = bool(state.get("full_life"))
    all_crits = bool(state.get("all_crits"))

    if skill.startswith("Burn "):
        return result(round((base_multiplier or 0) * turns, 2), f"{turns} Burn tick(s)", "Derived from burn rows")

    if skill == "Mighty Strike" and stunned and maximum is not None:
        return result(maximum, "Stunned target", "Dmg Max")

    if skill == "Sakapate Estoc":
        if mask_active and stunned and maximum is not None:
            return result(maximum, "Masked and stunned", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Sakapate Fire":
        if mask_active and turns >= 3 and maximum is not None:
            return result(maximum, "Mask active with 3 Burn turns", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Cultist Slashes":
        if mask_active and low_life and maximum is not None:
            return result(maximum, "Mask active at low life", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Sakapate Slam":
        if mask_active and marked and maximum is not None:
            return result(maximum, "Masked and marked target", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Obscur Sword":
        if mask_active and powerless and maximum is not None:
            return result(maximum, "Masked and powerless target", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Danseuse Waltz":
        if mask_active and burning and maximum is not None:
            return result(maximum, "Mask active vs burning target", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Chevalier Thrusts":
        if mask_active and all_crits and maximum is not None:
            return result(maximum, "Mask active and all crits", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Sakapate Explosion":
        if mask_active and all_crits and maximum is not None:
            return result(maximum, "Mask active and all crits", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Cultist Blood":
        if mask_active and full_life and maximum is not None:
            return result(maximum, "Mask active at full life", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if skill == "Abberation Light":
        if mask_active and turns >= 3 and maximum is not None:
            return result(maximum, "Mask active with 3 Burn turns", "Dmg Max")
        if turns >= 3 and conditional is not None:
            return result(conditional, "3 Burn turns", "Dmg Con1")

    if skill == "Braseleur Smash":
        if mask_active and turns >= 3 and maximum is not None:
            return result(maximum, "Mask active with 3 Burn turns", "Dmg Max")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")

    if mask_active and conditional is not None:
        return result(conditional, "Mask active", "Dmg Con1")

    return base_result(row)


SCIEL_FORETELL_RATES = {
    "End Slice": 0.20,
    "End Slice 30 Foretell": 0.20,
    "Twilight Dance": 0.25,
    "Phantom Blade": 0.35,
    "Dark Wave": 0.25,
    "Delaying Slash": 0.30,
    "Twilight Slash": 0.25,
}


def calculate_sciel(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Sciel skill damage from foretell, twilight, and life state."""
    skill = clean_text(row.get("Skill"))
    base_multiplier = number_from_row(row, "Damage Multi")
    conditional = number_from_row(row, "ConDmg")
    twilight_value = number_from_row(row, "TwilightDmg")
    foretell = clamp_int(state.get("foretell"), 0, 30)
    twilight = bool(state.get("twilight"))
    full_life = bool(state.get("full_life"))

    if skill in SCIEL_FORETELL_RATES:
        rate = SCIEL_FORETELL_RATES[skill]
        multiplier = (base_multiplier or 0) * (1 + (rate * foretell))
        scenario = f"{foretell} Foretell"
        source = "Derived from note text"
        if twilight:
            multiplier *= 1.5
            scenario = f"{scenario}, Twilight"
            source = "Derived from note text + Twilight"
        return result(round(multiplier, 2), scenario, source)

    if skill == "Our Sacrifice":
        multiplier = (base_multiplier or 0) * (1 + (0.3 * foretell))
        scenario_parts = [f"{foretell} Foretell"]
        if full_life:
            multiplier *= 3.97
            scenario_parts.append("Full life")
        if twilight:
            multiplier *= 1.5
            scenario_parts.append("Twilight")
        return result(round(multiplier, 2), ", ".join(scenario_parts), "Derived from note text")

    if skill == "Sealed Fate":
        if foretell >= 1 and twilight and twilight_value is not None:
            return result(twilight_value, "1-6 Foretell, Twilight", "TwilightDmg")
        if foretell >= 1 and conditional is not None:
            return result(conditional, "1-6 Foretell", "ConDmg")
        return base_result(row)

    if skill == "Firing Shadow":
        multiplier = (base_multiplier or 0) * (1 + (min(foretell, 3) / 3))
        scenario = f"{min(foretell, 3)} Foretell consumed"
        if twilight:
            multiplier *= 1.5
            scenario = f"{scenario}, Twilight"
        return result(round(multiplier, 2), scenario, "Derived from note text")

    if twilight and twilight_value is not None:
        return result(twilight_value, "Twilight", "TwilightDmg")

    return base_result(row)


def calculate_verso(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Verso skill damage from rank and setup state."""
    skill = clean_text(row.get("Skill"))
    base_multiplier = number_from_row(row, "Damage Multi")
    conditional = number_from_row(row, "ConDmg")
    maximum = number_from_row(row, "SRankMAX")
    rank = clean_text(state.get("rank")) or "D"
    stunned = bool(state.get("stunned"))
    speed_bonus = bool(state.get("speed_bonus"))
    shots = clamp_int(state.get("shots"), 0, 10)
    uses = clamp_int(state.get("uses"), 1, 6)
    required_rank = parse_rank_requirement(text_from_row(row, "Condition"))

    if skill == "End Bringer":
        if stunned and rank == "S" and maximum is not None:
            return result(maximum, "Stunned target at S Rank", "SRankMAX")
        if stunned and conditional is not None:
            return result(conditional, "Stunned target", "ConDmg")
        return base_result(row)

    if skill == "Steeled Strike":
        if rank == "S" and uses >= 2 and maximum is not None:
            return result(maximum, "S Rank with full setup", "SRankMAX")
        if rank == "S" and conditional is not None:
            return result(conditional, "S Rank", "ConDmg")
        return base_result(row)

    if skill == "Follow Up":
        if rank == "S" and shots >= 10 and maximum is not None:
            return result(maximum, "10 shots at S Rank", "SRankMAX")
        if shots > 0:
            multiplier = round((base_multiplier or 0) * (1 + (0.5 * shots)), 2)
            return result(multiplier, f"{shots} ranged shot(s)", "Derived from note text")
        return base_result(row)

    if skill == "Ascending Assault":
        if rank == "S" and uses >= 6 and maximum is not None:
            return result(maximum, "6th use at S Rank", "SRankMAX")
        if uses >= 2:
            multiplier = round((base_multiplier or 0) * (1 + (0.3 * min(uses - 1, 5))), 2)
            if uses >= 6 and conditional is not None:
                return result(conditional, "6th use", "ConDmg")
            return result(multiplier, f"Use {uses}", "Derived from note text")
        return base_result(row)

    if skill == "Speed Burst":
        if speed_bonus and maximum is not None:
            return result(maximum, "C Rank with full speed bonus", "SRankMAX")
        if rank_at_least(rank, "C") and conditional is not None:
            return result(conditional, "C Rank", "ConDmg")
        return base_result(row)

    if rank == "S" and maximum is not None and skill not in {"Ranged Attack", "Basic Attack", "Counter"}:
        return result(maximum, "S Rank", "SRankMAX")

    if rank_at_least(rank, required_rank) and conditional is not None:
        return result(conditional, f"{required_rank} Rank", "ConDmg")

    return base_result(row)


def calculate_skill_result(
    character: str,
    row: CalculatorRow,
    state: CalculatorState,
) -> CalculationResult:
    """Dispatch skill calculation to the character-specific calculator."""
    calculators = {
        "gustave": calculate_gustave,
        "lune": calculate_lune,
        "maelle": calculate_maelle,
        "monoco": calculate_monoco,
        "sciel": calculate_sciel,
        "verso": calculate_verso,
    }
    return calculators[character](row, state)


def build_badges(character: str, row: CalculatorRow, current_cost: str) -> ComponentChildren:
    """Build metadata badges shown above the result cards."""
    difficulty = clean_text(row.get("Game Description")).title()
    difficulty_color = {
        "Low": "green",
        "Medium": "yellow",
        "High": "orange",
        "Very High": "red",
        "Extreme": "pink",
    }.get(difficulty, "gray")

    aoe_value = clean_text(row.get("AOE")).upper()
    aoe_label = "AOE" if aoe_value == "TRUE" else "Single Target"

    badges = [
        dmc.Badge(CHARACTER_META[character]["label"], color="blue", variant="light"),
        dmc.Badge(f"Cost: {current_cost} AP", color="gray", variant="outline"),
        dmc.Badge(aoe_label, color="teal", variant="outline"),
    ]

    if difficulty:
        badges.append(dmc.Badge(difficulty, color=difficulty_color, variant="light"))

    for key in ("Stance", "Mask", "Lunar"):
        value = clean_text(row.get(key))
        if value:
            badges.append(dmc.Badge(value, color="indigo", variant="outline"))

    return badges


def build_result_body(
    character: str,
    row: CalculatorRow,
    attack: float | None,
    current_cost: str,
    skill_result: CalculationResult,
) -> ComponentChildren:
    """Build the result card body for the selected skill state."""
    multiplier = skill_result.get("multiplier")
    damage = calculate_damage(attack, multiplier if isinstance(multiplier, (int, float)) else None)
    notes = clean_text(row.get("Notes"))

    return compact(
        [
            html.H3(clean_text(row.get("Skill")), className="mb-3"),
            dmc.Group(build_badges(character, row, current_cost), gap="xs"),
            dbc.Row(
                [
                    dbc.Col(
                        dmc.Paper(
                            [
                                dmc.Text(
                                    "Estimated Damage",
                                    size="sm",
                                    style={"color": "var(--mantine-color-dimmed)"},
                                ),
                                html.H2(format_value(damage), className="mb-0"),
                            ],
                            withBorder=True,
                            p="lg",
                            radius="md",
                        ),
                        md=6,
                        className="mb-3",
                    ),
                    dbc.Col(
                        dmc.Paper(
                            [
                                dmc.Text(
                                    "Applied Multiplier",
                                    size="sm",
                                    style={"color": "var(--mantine-color-dimmed)"},
                                ),
                                html.H2(format_multiplier(multiplier), className="mb-0"),
                            ],
                            withBorder=True,
                            p="lg",
                            radius="md",
                        ),
                        md=6,
                        className="mb-3",
                    ),
                ],
                className="g-3 mt-1",
            ),
            dmc.Paper(
                [
                    dmc.Text("Applied Scenario", fw=600),
                    dmc.Text(clean_text(skill_result.get("scenario"))),
                    dmc.Text(
                        f"Source: {clean_text(skill_result.get('source'))}",
                        size="sm",
                        style={"color": "var(--mantine-color-dimmed)"},
                    ),
                ],
                withBorder=True,
                p="md",
                radius="md",
            ),
            dbc.Alert(skill_result["warning"], color="warning", className="mb-0") if skill_result.get("warning") else None,
            dmc.Paper(
                [
                    dmc.Text("Notes", fw=600),
                    dmc.Text(notes or "No extra notes in the sheet."),
                ],
                withBorder=True,
                p="md",
                radius="md",
            ),
        ]
    )


def build_summary_body(row: CalculatorRow, attack: float | None) -> ComponentChildren:
    """Build the spreadsheet breakpoint summary table."""
    rows = build_sheet_rows(row)
    header_attack = format_value(attack) if attack is not None else "-"

    table_rows = [
        html.Tr(
            [
                html.Td(entry["label"]),
                html.Td(format_multiplier(entry["value"])),
                html.Td(format_value(calculate_damage(attack, entry["value"]))),
            ]
        )
        for entry in rows
    ]

    return [
        dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Sheet Scenario"),
                            html.Th("Multiplier"),
                            html.Th(f"Damage @ {header_attack} ATK"),
                        ]
                    )
                ),
                html.Tbody(table_rows),
            ],
            bordered=False,
            hover=True,
            responsive=True,
            className="mb-0",
        )
    ]


def build_character_section_styles(active_character: str) -> tuple[list[str], CharacterStyles]:
    """Return accordion visibility styles for the active character."""

    active_item = [f"setup-{active_character}"]

    styles = {
        character: VISIBLE_STYLE if character == active_character else HIDDEN_STYLE
        for character in CHARACTER_META
    }
    return active_item, styles


def uses_mask_condition(row: CalculatorRow) -> bool:
    """Return whether a Monoco row's sheet data explicitly depends on mask state."""

    texts = (
        text_from_row(row, "Condition 1"),
        text_from_row(row, "Con Max Dmg"),
        text_from_row(row, "Notes"),
    )
    return any("mask" in text.lower() for text in texts if text)


def build_skill_control_styles(character: str, row: CalculatorRow) -> ControlStyles:
    """Return per-control visibility styles for the selected character skill."""

    skill = clean_text(row.get("Skill"))
    condition = text_from_row(row, "Condition 1", "Condition").lower()
    max_condition = text_from_row(row, "Con Max Dmg", "ConTwilight").lower()
    styles: ControlStyles = {}

    def set_visibility(control: str, is_visible: bool) -> None:
        """Store the display style for a single control wrapper."""

        styles[control] = VISIBLE_STYLE if is_visible else HIDDEN_STYLE

    if character == "gustave":
        set_visibility("gustave_charges", skill.startswith("Overcharge"))
        return styles

    if character == "lune":
        set_visibility(
            "lune_stains",
            "stain" in condition or "stain" in max_condition or skill in {"Storm Caller"},
        )
        set_visibility(
            "lune_turns",
            skill.startswith("Burn ")
            or condition == "turn start dmg"
            or skill in {"Fire Rage", "Fire Rage Stained", "Storm Caller"},
        )
        set_visibility("lune_all_crits", "crit" in max_condition)
        return styles

    if character == "maelle":
        set_visibility("maelle_stance", not skill.startswith("Burn "))
        set_visibility("maelle_burn_stacks", skill in {"Burning Canvas", "Combustion"})
        set_visibility("maelle_hits_taken", skill == "Revenge")
        set_visibility("maelle_marked", skill in {"G-Homage", "Momentum Strike", "Percee"})
        set_visibility("maelle_all_crits", skill == "Sword Ballet")
        return styles

    if character == "monoco":
        set_visibility(
            "monoco_turns",
            skill.startswith("Burn ") or skill in {"Sakapate Fire", "Abberation Light", "Braseleur Smash"},
        )
        set_visibility("monoco_mask", uses_mask_condition(row))
        set_visibility("monoco_stunned", skill in {"Mighty Strike", "Sakapate Estoc"})
        set_visibility("monoco_marked", skill == "Sakapate Slam")
        set_visibility("monoco_powerless", skill == "Obscur Sword")
        set_visibility("monoco_burning", skill == "Danseuse Waltz")
        set_visibility("monoco_low_life", skill == "Cultist Slashes")
        set_visibility("monoco_full_life", skill == "Cultist Blood")
        set_visibility("monoco_all_crits", skill in {"Chevalier Thrusts", "Sakapate Explosion"})
        return styles

    if character == "sciel":
        set_visibility(
            "sciel_foretell",
            skill in SCIEL_FORETELL_RATES or skill in {"Our Sacrifice", "Sealed Fate", "Firing Shadow"},
        )
        set_visibility("sciel_twilight", number_from_row(row, "TwilightDmg") is not None)
        set_visibility("sciel_full_life", skill == "Our Sacrifice")
        return styles

    if character == "verso":
        set_visibility(
            "verso_rank",
            skill not in {"Ranged Attack", "Basic Attack", "Counter"}
            and (
                parse_rank_requirement(text_from_row(row, "Condition")) is not None
                or number_from_row(row, "SRankMAX") is not None
                or skill in {"Follow Up", "Ascending Assault", "Speed Burst", "End Bringer", "Steeled Strike"}
            ),
        )
        set_visibility("verso_shots", skill == "Follow Up")
        set_visibility("verso_uses", skill in {"Steeled Strike", "Ascending Assault"})
        set_visibility("verso_stunned", skill == "End Bringer")
        set_visibility("verso_speed_bonus", skill == "Speed Burst")
        return styles

    return styles


def build_empty_control_notice(character: str) -> html.Div:
    """Build the placeholder shown when a skill has no extra inputs."""

    return html.Div(
        dmc.Text(
            f"{CHARACTER_META[character]['label']} has no extra inputs for this skill.",
            c="dimmed",
            size="sm",
        ),
        id=f"exp33-calculator-empty-{character}",
        style=HIDDEN_STYLE,
    )


character_select = dmc.Select(
    id="exp33-calculator-character",
    label="Character",
    value=DEFAULT_CHARACTER,
    data=[{"label": meta["label"], "value": key} for key, meta in CHARACTER_META.items()],
    clearable=False,
)

skill_dropdown = dcc.Dropdown(
    id="exp33-calculator-skill",
    options=skill_options_for(DEFAULT_CHARACTER),
    value=DEFAULT_SKILLS[DEFAULT_CHARACTER],
    clearable=False,
)

attack_input = dmc.NumberInput(
    id="exp33-calculator-attack",
    label="Attack stat",
    value=CALCULATOR_DATA[DEFAULT_CHARACTER]["default_attack"],
    min=1,
    step=1,
)

calculator_controls = dbc.Accordion(
    [
        dbc.AccordionItem(
            dmc.Stack(
                [
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-gustave-charges",
                            label="Charges",
                            value=0,
                            min=0,
                            max=10,
                            step=1,
                        ),
                        id="exp33-calculator-control-gustave-charges",
                    ),
                    build_empty_control_notice("gustave"),
                ],
                gap="sm",
            ),
            id="exp33-calculator-item-gustave",
            item_id="setup-gustave",
            title="Gustave Controls",
            style={"display": "none"},
        ),
        dbc.AccordionItem(
            dmc.Stack(
                [
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-stains",
                            label="Stains",
                            value=0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-stains",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-turns",
                            label="Turns / burn ticks",
                            value=1,
                            min=1,
                            max=5,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-turns",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-lune-all-crits", label="All hits crit"),
                        id="exp33-calculator-control-lune-all-crits",
                    ),
                    build_empty_control_notice("lune"),
                ],
                gap="sm",
            ),
            id="exp33-calculator-item-lune",
            item_id="setup-lune",
            title="Lune Controls",
        ),
        dbc.AccordionItem(
            dmc.Stack(
                [
                    html.Div(
                        dmc.Select(
                            id="exp33-calculator-maelle-stance",
                            label="Current stance",
                            value="Offensive",
                            data=["Offensive", "Defensive", "Virtuoso", "Stanceless"],
                            clearable=False,
                        ),
                        id="exp33-calculator-control-maelle-stance",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-maelle-burn-stacks",
                            label="Burn stacks",
                            value=0,
                            min=0,
                            max=100,
                            step=1,
                        ),
                        id="exp33-calculator-control-maelle-burn-stacks",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-maelle-hits-taken",
                            label="Hits taken last round",
                            value=0,
                            min=0,
                            max=5,
                            step=1,
                        ),
                        id="exp33-calculator-control-maelle-hits-taken",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-maelle-marked", label="Target is marked"),
                        id="exp33-calculator-control-maelle-marked",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-maelle-all-crits", label="All hits crit"),
                        id="exp33-calculator-control-maelle-all-crits",
                    ),
                    build_empty_control_notice("maelle"),
                ],
                gap="sm",
            ),
            id="exp33-calculator-item-maelle",
            item_id="setup-maelle",
            title="Maelle Controls",
            style={"display": "none"},
        ),
        dbc.AccordionItem(
            dmc.Stack(
                [
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-monoco-turns",
                            label="Burn / setup turns",
                            value=1,
                            min=1,
                            max=3,
                            step=1,
                        ),
                        id="exp33-calculator-control-monoco-turns",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-mask", label="Mask active"),
                        id="exp33-calculator-control-monoco-mask",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-stunned", label="Target is stunned"),
                        id="exp33-calculator-control-monoco-stunned",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-marked", label="Target is marked"),
                        id="exp33-calculator-control-monoco-marked",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-powerless", label="Target is powerless"),
                        id="exp33-calculator-control-monoco-powerless",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-burning", label="Target is burning"),
                        id="exp33-calculator-control-monoco-burning",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-low-life", label="Monoco is low life"),
                        id="exp33-calculator-control-monoco-low-life",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-full-life", label="Monoco is full life"),
                        id="exp33-calculator-control-monoco-full-life",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-monoco-all-crits", label="All hits crit"),
                        id="exp33-calculator-control-monoco-all-crits",
                    ),
                    build_empty_control_notice("monoco"),
                ],
                gap="sm",
            ),
            id="exp33-calculator-item-monoco",
            item_id="setup-monoco",
            title="Monoco Controls",
            style={"display": "none"},
        ),
        dbc.AccordionItem(
            dmc.Stack(
                [
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-sciel-foretell",
                            label="Foretell",
                            value=0,
                            min=0,
                            max=30,
                            step=1,
                        ),
                        id="exp33-calculator-control-sciel-foretell",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-sciel-twilight", label="Twilight active"),
                        id="exp33-calculator-control-sciel-twilight",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-sciel-full-life", label="Allies at full life"),
                        id="exp33-calculator-control-sciel-full-life",
                    ),
                    build_empty_control_notice("sciel"),
                ],
                gap="sm",
            ),
            id="exp33-calculator-item-sciel",
            item_id="setup-sciel",
            title="Sciel Controls",
            style={"display": "none"},
        ),
        dbc.AccordionItem(
            dmc.Stack(
                [
                    html.Div(
                        dmc.Select(
                            id="exp33-calculator-verso-rank",
                            label="Current rank",
                            value="D",
                            data=["D", "C", "B", "A", "S"],
                            clearable=False,
                        ),
                        id="exp33-calculator-control-verso-rank",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-verso-shots",
                            label="Ranged shots this turn",
                            value=0,
                            min=0,
                            max=10,
                            step=1,
                        ),
                        id="exp33-calculator-control-verso-shots",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-verso-uses",
                            label="Uses / setup turns",
                            value=1,
                            min=1,
                            max=6,
                            step=1,
                        ),
                        id="exp33-calculator-control-verso-uses",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-verso-stunned", label="Target is stunned"),
                        id="exp33-calculator-control-verso-stunned",
                    ),
                    html.Div(
                        dmc.Switch(id="exp33-calculator-verso-speed-bonus", label="Max speed bonus active"),
                        id="exp33-calculator-control-verso-speed-bonus",
                    ),
                    build_empty_control_notice("verso"),
                ],
                gap="sm",
            ),
            id="exp33-calculator-item-verso",
            item_id="setup-verso",
            title="Verso Controls",
            style={"display": "none"},
        ),
    ],
    id="exp33-calculator-character-accordion",
    active_item=["setup-lune"],
    always_open=True,
    start_collapsed=True,
    flush=True,
)

layout = dbc.Container(
    [
        html.H1("Calculator"),
        dbc.Alert(
            html.Span(
                [
                    "Spreadsheet damage values are used as breakpoints. When the note text clearly exposes the formula, the calculator derives intermediate values from it.",
                ]
            ),
            color="info",
            className="mt-2",
        ),
        dcc.Markdown(
            "Choose a character, pick a skill, then adjust the relevant combat state. "
            "The result card shows the applied breakpoint or derived formula and estimates damage from your current attack stat."
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Setup"),
                            dbc.CardBody(
                                dmc.Stack(
                                    [
                                        character_select,
                                        html.Div(
                                            [
                                                html.Label("Skill", className="form-label"),
                                                skill_dropdown,
                                            ]
                                        ),
                                        attack_input,
                                        calculator_controls,
                                    ],
                                    gap="md",
                                )
                            ),
                        ]
                    ),
                    lg=5,
                    className="mb-4",
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Result"),
                                dbc.CardBody(id="exp33-calculator-result-body"),
                            ],
                            className="mb-3",
                        ),
                        dbc.Card(
                            [
                                dbc.CardHeader("Sheet Summary"),
                                dbc.CardBody(id="exp33-calculator-summary-body"),
                            ]
                        ),
                    ],
                    lg=7,
                    className="mb-4",
                ),
            ],
            className="g-4",
        ),
    ],
    fluid=True,
)

@callback(
    Output("exp33-calculator-skill", "options"),
    Output("exp33-calculator-skill", "value"),
    Output("exp33-calculator-attack", "value"),
    Input("exp33-calculator-character", "value"),
)
def update_skill_dropdown(character: str | None) -> tuple[list[SkillOption], str, float]:
    """Refresh the skill dropdown and default attack when the character changes."""
    selected_character = character or DEFAULT_CHARACTER
    options = skill_options_for(selected_character)
    default_skill = DEFAULT_SKILLS.get(selected_character, options[0]["value"])
    if default_skill not in {option["value"] for option in options}:
        default_skill = options[0]["value"]
    attack = CALCULATOR_DATA[selected_character]["default_attack"]
    return options, default_skill, attack


@callback(
    Output("exp33-calculator-character-accordion", "active_item"),
    Output("exp33-calculator-item-gustave", "style"),
    Output("exp33-calculator-item-lune", "style"),
    Output("exp33-calculator-item-maelle", "style"),
    Output("exp33-calculator-item-monoco", "style"),
    Output("exp33-calculator-item-sciel", "style"),
    Output("exp33-calculator-item-verso", "style"),
    Output("exp33-calculator-control-gustave-charges", "style"),
    Output("exp33-calculator-control-lune-stains", "style"),
    Output("exp33-calculator-control-lune-turns", "style"),
    Output("exp33-calculator-control-lune-all-crits", "style"),
    Output("exp33-calculator-control-maelle-stance", "style"),
    Output("exp33-calculator-control-maelle-burn-stacks", "style"),
    Output("exp33-calculator-control-maelle-hits-taken", "style"),
    Output("exp33-calculator-control-maelle-marked", "style"),
    Output("exp33-calculator-control-maelle-all-crits", "style"),
    Output("exp33-calculator-control-monoco-turns", "style"),
    Output("exp33-calculator-control-monoco-mask", "style"),
    Output("exp33-calculator-control-monoco-stunned", "style"),
    Output("exp33-calculator-control-monoco-marked", "style"),
    Output("exp33-calculator-control-monoco-powerless", "style"),
    Output("exp33-calculator-control-monoco-burning", "style"),
    Output("exp33-calculator-control-monoco-low-life", "style"),
    Output("exp33-calculator-control-monoco-full-life", "style"),
    Output("exp33-calculator-control-monoco-all-crits", "style"),
    Output("exp33-calculator-empty-gustave", "style"),
    Output("exp33-calculator-empty-lune", "style"),
    Output("exp33-calculator-empty-maelle", "style"),
    Output("exp33-calculator-empty-monoco", "style"),
    Output("exp33-calculator-empty-sciel", "style"),
    Output("exp33-calculator-empty-verso", "style"),
    Output("exp33-calculator-control-sciel-foretell", "style"),
    Output("exp33-calculator-control-sciel-twilight", "style"),
    Output("exp33-calculator-control-sciel-full-life", "style"),
    Output("exp33-calculator-control-verso-rank", "style"),
    Output("exp33-calculator-control-verso-shots", "style"),
    Output("exp33-calculator-control-verso-uses", "style"),
    Output("exp33-calculator-control-verso-stunned", "style"),
    Output("exp33-calculator-control-verso-speed-bonus", "style"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-skill", "value"),
)
def sync_visible_controls(
    character: str | None,
    skill: str | None,
) -> tuple[
    list[str],
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
    StyleRule,
]:
    """Show only the control section relevant to the selected character."""
    active_character = character or DEFAULT_CHARACTER
    active_item, styles = build_character_section_styles(active_character)
    row = get_row(active_character, skill)
    control_styles = build_skill_control_styles(active_character, row)

    def control_style(control: str) -> StyleRule:
        """Return the style for a single control wrapper."""

        return control_styles.get(control, HIDDEN_STYLE)

    def empty_state_style(prefix: str) -> StyleRule:
        """Show the placeholder when no controls are visible for the section."""

        return VISIBLE_STYLE if not any(key.startswith(prefix) and value == VISIBLE_STYLE for key, value in control_styles.items()) else HIDDEN_STYLE

    return (
        active_item,
        styles["gustave"],
        styles["lune"],
        styles["maelle"],
        styles["monoco"],
        styles["sciel"],
        styles["verso"],
        control_style("gustave_charges"),
        control_style("lune_stains"),
        control_style("lune_turns"),
        control_style("lune_all_crits"),
        control_style("maelle_stance"),
        control_style("maelle_burn_stacks"),
        control_style("maelle_hits_taken"),
        control_style("maelle_marked"),
        control_style("maelle_all_crits"),
        control_style("monoco_turns"),
        control_style("monoco_mask"),
        control_style("monoco_stunned"),
        control_style("monoco_marked"),
        control_style("monoco_powerless"),
        control_style("monoco_burning"),
        control_style("monoco_low_life"),
        control_style("monoco_full_life"),
        control_style("monoco_all_crits"),
        empty_state_style("gustave"),
        empty_state_style("lune"),
        empty_state_style("maelle"),
        empty_state_style("monoco"),
        empty_state_style("sciel"),
        empty_state_style("verso"),
        control_style("sciel_foretell"),
        control_style("sciel_twilight"),
        control_style("sciel_full_life"),
        control_style("verso_rank"),
        control_style("verso_shots"),
        control_style("verso_uses"),
        control_style("verso_stunned"),
        control_style("verso_speed_bonus"),
    )


@callback(
    Output("exp33-calculator-result-body", "children"),
    Output("exp33-calculator-summary-body", "children"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-skill", "value"),
    Input("exp33-calculator-attack", "value"),
    Input("exp33-calculator-gustave-charges", "value"),
    Input("exp33-calculator-lune-stains", "value"),
    Input("exp33-calculator-lune-turns", "value"),
    Input("exp33-calculator-lune-all-crits", "checked"),
    Input("exp33-calculator-maelle-stance", "value"),
    Input("exp33-calculator-maelle-burn-stacks", "value"),
    Input("exp33-calculator-maelle-hits-taken", "value"),
    Input("exp33-calculator-maelle-marked", "checked"),
    Input("exp33-calculator-maelle-all-crits", "checked"),
    Input("exp33-calculator-monoco-turns", "value"),
    Input("exp33-calculator-monoco-mask", "checked"),
    Input("exp33-calculator-monoco-stunned", "checked"),
    Input("exp33-calculator-monoco-marked", "checked"),
    Input("exp33-calculator-monoco-powerless", "checked"),
    Input("exp33-calculator-monoco-burning", "checked"),
    Input("exp33-calculator-monoco-low-life", "checked"),
    Input("exp33-calculator-monoco-full-life", "checked"),
    Input("exp33-calculator-monoco-all-crits", "checked"),
    Input("exp33-calculator-sciel-foretell", "value"),
    Input("exp33-calculator-sciel-twilight", "checked"),
    Input("exp33-calculator-sciel-full-life", "checked"),
    Input("exp33-calculator-verso-rank", "value"),
    Input("exp33-calculator-verso-shots", "value"),
    Input("exp33-calculator-verso-uses", "value"),
    Input("exp33-calculator-verso-stunned", "checked"),
    Input("exp33-calculator-verso-speed-bonus", "checked"),
)
def update_calculator_result(
    character: str | None,
    skill: str | None,
    attack: NumericInput,
    gustave_charges: NumericInput,
    lune_stains: NumericInput,
    lune_turns: NumericInput,
    lune_all_crits: ToggleInput,
    maelle_stance: str | None,
    maelle_burn_stacks: NumericInput,
    maelle_hits_taken: NumericInput,
    maelle_marked: ToggleInput,
    maelle_all_crits: ToggleInput,
    monoco_turns: NumericInput,
    monoco_mask: ToggleInput,
    monoco_stunned: ToggleInput,
    monoco_marked: ToggleInput,
    monoco_powerless: ToggleInput,
    monoco_burning: ToggleInput,
    monoco_low_life: ToggleInput,
    monoco_full_life: ToggleInput,
    monoco_all_crits: ToggleInput,
    sciel_foretell: NumericInput,
    sciel_twilight: ToggleInput,
    sciel_full_life: ToggleInput,
    verso_rank: str | None,
    verso_shots: NumericInput,
    verso_uses: NumericInput,
    verso_stunned: ToggleInput,
    verso_speed_bonus: ToggleInput,
) -> tuple[ComponentChildren, ComponentChildren]:
    """Recalculate the selected skill and rebuild both result panels."""

    selected_character = character or DEFAULT_CHARACTER
    row = get_row(selected_character, skill)
    attack_value = parse_number(attack) or CALCULATOR_DATA[selected_character]["default_attack"]

    states: dict[str, CalculatorState] = {
        "gustave": {
            "charges": gustave_charges,
        },
        "lune": {
            "stains": lune_stains,
            "turns": lune_turns,
            "all_crits": lune_all_crits,
        },
        "maelle": {
            "stance": maelle_stance,
            "burn_stacks": maelle_burn_stacks,
            "hits_taken": maelle_hits_taken,
            "marked": maelle_marked,
            "all_crits": maelle_all_crits,
            "turns": 3,
        },
        "monoco": {
            "turns": monoco_turns,
            "mask_active": monoco_mask,
            "stunned": monoco_stunned,
            "marked": monoco_marked,
            "powerless": monoco_powerless,
            "burning": monoco_burning,
            "low_life": monoco_low_life,
            "full_life": monoco_full_life,
            "all_crits": monoco_all_crits,
        },
        "sciel": {
            "foretell": sciel_foretell,
            "twilight": sciel_twilight,
            "full_life": sciel_full_life,
        },
        "verso": {
            "rank": verso_rank,
            "shots": verso_shots,
            "uses": verso_uses,
            "stunned": verso_stunned,
            "speed_bonus": verso_speed_bonus,
        },
    }

    skill_result = calculate_skill_result(selected_character, row, states[selected_character])
    current_cost = calculate_current_cost(selected_character, row, states[selected_character])

    return (
        build_result_body(selected_character, row, attack_value, current_cost, skill_result),
        build_summary_body(row, attack_value),
    )


register_page(__name__, path="/calculator", name="Calculator", layout=layout)
