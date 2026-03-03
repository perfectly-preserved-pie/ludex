from __future__ import annotations
from games.expedition33.helpers import clean_frame, format_value
from pathlib import Path
from typing import Any, TypeAlias, TypedDict
import pandas as pd
import re

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


class AffinityDetails(TypedDict):
    """Resolved elemental affinity context for a selected skill."""

    element: str
    affinity: str
    factor: float
    applies: bool


CSV_DIR = Path(__file__).resolve().parents[3] / "assets" / "expedition33" / "clair_skill_damage"

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
    """Remove placeholder values from a component child list.

    Args:
        children: The raw list of Dash component children, which may contain
            ``None`` placeholders.

    Returns:
        A new child list containing only non-``None`` entries.
    """

    return [child for child in children if child is not None]


def clean_text(value: Any) -> str:
    """Normalize a raw sheet value into a trimmed string.

    Args:
        value: The raw value read from a CSV row or callback state.

    Returns:
        A stripped string with ``None`` and ``nan``-like values collapsed to an
        empty string.
    """

    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_number(value: Any) -> float | None:
    """Parse a numeric value from sheet data or callback input.

    Args:
        value: The raw value to parse.

    Returns:
        The parsed float when the value is numeric, otherwise ``None``.
    """

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
    """Extract the first integer embedded in a string value.

    Args:
        value: The raw text or sheet value to inspect.

    Returns:
        The first integer found in the value, or ``None`` when no integer is
        present.
    """

    match = re.search(r"(\d+)", clean_text(value))
    return int(match.group(1)) if match else None


def number_from_row(row: CalculatorRow, *keys: str) -> float | None:
    """Read the first parseable numeric value from a calculator row.

    Args:
        row: The selected calculator row.
        *keys: Candidate column names to inspect in order.

    Returns:
        The first successfully parsed numeric value, or ``None`` if none of the
        requested columns contain one.
    """

    for key in keys:
        number = parse_number(row.get(key))
        if number is not None:
            return number
    return None


def text_from_row(row: CalculatorRow, *keys: str) -> str:
    """Read the first non-empty text value from a calculator row.

    Args:
        row: The selected calculator row.
        *keys: Candidate column names to inspect in order.

    Returns:
        The first non-empty normalized string, or an empty string when all
        requested columns are blank.
    """

    for key in keys:
        text = clean_text(row.get(key))
        if text:
            return text
    return ""


def clamp_int(value: Any, minimum: int, maximum: int) -> int:
    """Clamp user input to an allowed integer range.

    Args:
        value: The raw control value supplied by Dash.
        minimum: The smallest allowed integer.
        maximum: The largest allowed integer.

    Returns:
        An integer constrained to the inclusive ``minimum`` and ``maximum``
        bounds. Invalid inputs fall back to ``minimum``.
    """

    try:
        number = int(value)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, min(number, maximum))


def format_multiplier(value: float | None) -> str:
    """Format a multiplier for display in the calculator UI.

    Args:
        value: The computed damage multiplier.

    Returns:
        A human-readable multiplier string such as ``"3.5x"`` or ``"-"`` when
        the multiplier is unavailable.
    """

    if value is None:
        return "-"
    text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{text}x"


def calculate_damage(attack: float | None, multiplier: float | None) -> float | None:
    """Convert attack and multiplier inputs into estimated damage.

    Args:
        attack: The effective attack power used by the calculator.
        multiplier: The effective damage multiplier for the selected scenario.

    Returns:
        The rounded estimated damage, or ``None`` when either input is missing.
    """

    if attack is None or multiplier is None:
        return None
    return round(attack * multiplier, 2)


def skill_element(row: CalculatorRow) -> str:
    """Read the skill's elemental typing from the loaded sheet row."""

    return clean_text(text_from_row(row, "Damage Element", "Element"))


def normalize_affinity(value: str | None) -> str:
    """Normalize the selected affinity option to a supported value."""

    normalized = clean_text(value).lower()
    return normalized if normalized in {"neutral", "weak", "resist"} else "neutral"


def resolve_affinity(row: CalculatorRow, affinity: str | None) -> AffinityDetails:
    """Resolve whether an affinity modifier applies to the current skill."""

    element = skill_element(row)
    normalized_affinity = normalize_affinity(affinity)
    applies = bool(element) and element.lower() not in {"physical", "none", "non-elemental", "neutral"}
    factor = 1.0
    if applies and normalized_affinity == "weak":
        factor = 1.5
    elif applies and normalized_affinity == "resist":
        factor = 0.5

    return {
        "element": element,
        "affinity": normalized_affinity,
        "factor": factor,
        "applies": applies,
    }


def result(
    multiplier: float | None,
    scenario: str,
    source: str,
    warning: str | None = None,
) -> CalculationResult:
    """Build a normalized calculation result payload.

    Args:
        multiplier: The effective damage multiplier for the selected scenario.
        scenario: A short description of the scenario that produced the result.
        source: The sheet column or derived rule used for the multiplier.
        warning: Optional warning text shown alongside the result.

    Returns:
        A standardized result dictionary consumed by the calculator UI.
    """

    return {
        "multiplier": multiplier,
        "scenario": scenario,
        "source": source,
        "warning": warning,
    }


def base_result(
    row: CalculatorRow,
    scenario: str | None = None,
    source: str = "Damage Multi",
) -> CalculationResult:
    """Build the default result for a calculator row.

    Args:
        row: The selected calculator row.
        scenario: An optional scenario label override.
        source: The source label for the multiplier value.

    Returns:
        A normalized result payload based on the row's base multiplier and sheet
        condition text.
    """

    condition = text_from_row(row, "Condition 1", "Condition")
    return result(
        number_from_row(row, "Damage Multi"),
        scenario or ("Base value" if not condition else f"Base value | breakpoint: {condition}"),
        source,
    )


def load_calculator_data() -> dict[str, CalculatorPayload]:
    """Load and normalize all calculator CSV data.

    Returns:
        A mapping of character ids to their default attack values, raw records,
        and skill lookup dictionaries.
    """

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
    """Build dropdown options for a character's skills.

    Args:
        character: The calculator character id.

    Returns:
        A case-insensitively sorted list of dropdown option dictionaries for the
        character's skills.
    """

    return sorted(
        [{"label": record["Skill"], "value": record["Skill"]} for record in CALCULATOR_DATA[character]["records"]],
        key=lambda option: option["label"].lower(),
    )


def get_row(character: str, skill: str | None) -> CalculatorRow:
    """Resolve the selected skill row for a character.

    Args:
        character: The calculator character id.
        skill: The requested skill name, if one is selected.

    Returns:
        The matching skill row, or the character's configured fallback/default
        row when the requested skill is unavailable.
    """

    skills: dict[str, CalculatorRow] = CALCULATOR_DATA[character]["skills"]
    if skill in skills:
        return skills[skill]

    fallback_skill = DEFAULT_SKILLS.get(character)
    if fallback_skill in skills:
        return skills[fallback_skill]

    return CALCULATOR_DATA[character]["records"][0]


def parse_rank_requirement(value: str) -> str | None:
    """Extract a Verso rank requirement from text.

    Args:
        value: The sheet condition text to inspect.

    Returns:
        A rank letter when one is present and recognized, otherwise ``None``.
    """

    match = re.search(r"\b([DCBAS])\b", clean_text(value))
    if not match:
        return None
    rank = match.group(1)
    return rank if rank in RANK_ORDER else None


def rank_matches(current_rank: str, required_rank: str | None) -> bool:
    """Check whether a Verso rank matches an exact requirement.

    Args:
        current_rank: The currently selected Verso rank.
        required_rank: The exact rank required by the skill.

    Returns:
        ``True`` when the current rank exactly matches the required rank,
        otherwise ``False``.
    """

    if required_rank is None:
        return False
    return clean_text(current_rank) == clean_text(required_rank)


def build_sheet_rows(row: CalculatorRow) -> list[SheetScenario]:
    """Collect distinct multiplier breakpoints from a sheet row.

    Args:
        row: The selected calculator row.

    Returns:
        A de-duplicated list of sheet scenarios used by the summary table.
    """

    entries: list[SheetScenario] = []
    lune_mode = text_from_row(row, "Lune Mode")

    def add_entry(label: str, value: float | None) -> None:
        """Append a unique summary entry when the value is usable.

        Args:
            label: The scenario label to show in the summary table.
            value: The multiplier to store for that scenario.

        Returns:
            ``None``. The function mutates ``entries`` in place.
        """

        if value is None:
            return
        if any(existing["label"] == label and existing["value"] == value for existing in entries):
            return
        entries.append({"label": label, "value": value})

    if lune_mode == "duration_consume":
        per_turn = number_from_row(row, "Damage Multi")
        base_turns = clamp_int(number_from_row(row, "Base Turns"), 1, 10)
        max_turns = clamp_int(number_from_row(row, "Max Turns"), base_turns, 10)
        add_entry("1 turn", per_turn)
        if per_turn is not None and base_turns > 1:
            add_entry(f"{base_turns} turns", round(per_turn * base_turns, 2))
        if per_turn is not None and max_turns > base_turns:
            add_entry(f"Consume | {max_turns} turns", round(per_turn * max_turns, 2))
        return entries

    add_entry("Base", number_from_row(row, "Damage Multi"))

    all_crit_value = number_from_row(row, "All Crit Dmg")
    if all_crit_value is not None and all_crit_value != number_from_row(row, "Damage Multi"):
        add_entry("All hits crit", all_crit_value)

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
    """Calculate the AP cost shown for the selected state.

    Args:
        character: The calculator character id.
        row: The selected calculator row.
        state: The normalized state dictionary for the active character.

    Returns:
        The AP cost string after applying any character-specific reductions.
    """

    raw_cost = clean_text(row.get("Cost"))
    numeric_cost = parse_number(row.get("Cost"))
    skill = clean_text(row.get("Skill"))

    def split_pipe_values(value: Any) -> list[str]:
        text = clean_text(value)
        if not text:
            return []
        return [part.strip() for part in text.split("|") if part.strip() and part.strip() != "-"]

    def lune_can_consume(requirements_text: Any) -> bool:
        requirements: dict[str, int] = {}
        for stain in split_pipe_values(requirements_text):
            normalized = stain.lower()
            if normalized == "all":
                continue
            requirements[normalized] = requirements.get(normalized, 0) + 1

        if not requirements:
            return False

        inventory = {
            "earth": clamp_int(state.get("earth_stains"), 0, 4),
            "fire": clamp_int(state.get("fire_stains"), 0, 4),
            "ice": clamp_int(state.get("ice_stains"), 0, 4),
            "lightning": clamp_int(state.get("lightning_stains"), 0, 4),
            "light": clamp_int(state.get("light_stains"), 0, 4),
        }
        light_required = requirements.pop("light", 0)
        available_light = inventory["light"]
        if available_light < light_required:
            return False

        jokers = available_light - light_required
        for stain, needed in requirements.items():
            available = inventory.get(stain, 0)
            if available >= needed:
                continue
            deficit = needed - available
            if jokers < deficit:
                return False
            jokers -= deficit

        return True

    if numeric_cost is None:
        return raw_cost or "-"

    if character == "lune" and skill in {"Healing Light", "Rebirth"} and lune_can_consume(row.get("Consume Stains")):
        return "0"

    if character == "maelle" and state.get("stance") == "Virtuoso" and skill in {"Momentum Strike", "Percee"}:
        return format_value(max(numeric_cost - 3, 0))

    if character == "monoco" and text_from_row(row, "Monoco Mode") == "cost_mask" and state.get("mask_active"):
        return "0"

    if character == "verso":
        rank = clean_text(state.get("rank")) or "D"
        if skill in {"Follow Up", "Ascending Assault"} and rank == "S":
            return "2"
        if skill == "Perfect Break" and rank_matches(rank, "B"):
            return "5"
        if skill == "Phantom Stars" and rank == "S":
            return "5"

    return format_value(numeric_cost)
