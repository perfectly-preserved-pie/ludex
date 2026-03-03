from __future__ import annotations
from games.expedition33.calculator.core import (
    CalculationResult,
    CalculatorRow,
    CalculatorState,
    ControlStyles,
    HIDDEN_STYLE,
    VISIBLE_STYLE,
    base_result,
    clamp_int,
    clean_text,
    extract_first_int,
    number_from_row,
    parse_rank_requirement,
    rank_matches,
    result,
    text_from_row,
)
from games.expedition33.calculator.pictos import PictoSummary
from games.expedition33.calculator.weapons import WeaponSummary

SCIEL_FORETELL_RATES = {
    "End Slice": 0.20,
    "End Slice 30 Foretell": 0.20,
    "Twilight Dance": 0.25,
    "Phantom Blade": 0.35,
    "Dark Wave": 0.25,
    "Delaying Slash": 0.30,
    "Twilight Slash": 0.25,
}

LUNE_STAIN_KEYS = (
    "earth_stains",
    "fire_stains",
    "ice_stains",
    "lightning_stains",
    "light_stains",
)


def split_pipe_values(value: object) -> list[str]:
    """Split a pipe-delimited sheet field into normalized entries."""

    text = clean_text(value)
    if not text:
        return []
    return [part.strip() for part in text.split("|") if part.strip() and part.strip() != "-"]


def lune_stain_inventory(state: CalculatorState) -> dict[str, int]:
    """Read Lune's current stain counts from calculator state."""

    return {
        "earth": clamp_int(state.get("earth_stains"), 0, 4),
        "fire": clamp_int(state.get("fire_stains"), 0, 4),
        "ice": clamp_int(state.get("ice_stains"), 0, 4),
        "lightning": clamp_int(state.get("lightning_stains"), 0, 4),
        "light": clamp_int(state.get("light_stains"), 0, 4),
    }


def format_lune_stains(value: object) -> str:
    """Format a stain requirement string for UI text."""

    stains = split_pipe_values(value)
    if not stains:
        return "stains"
    if len(stains) == 1 and stains[0].lower() == "all":
        return "all stains"
    return " + ".join(stains)


def can_satisfy_lune_stains(requirements_text: object, state: CalculatorState) -> bool:
    """Check whether Lune's current stains satisfy a requirement list."""

    requirements: dict[str, int] = {}
    for stain in split_pipe_values(requirements_text):
        normalized = stain.lower()
        if normalized == "all":
            continue
        requirements[normalized] = requirements.get(normalized, 0) + 1

    if not requirements:
        return False

    inventory = lune_stain_inventory(state)
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


def calculate_gustave(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Gustave's effective skill multiplier.

    Args:
        row: The selected Gustave skill row.
        state: The normalized Gustave control state.

    Returns:
        A normalized calculation result describing the effective multiplier and
        scenario for the selected skill.
    """

    skill = clean_text(row.get("Skill"))
    if skill.startswith("Overcharge"):
        charges = clamp_int(state.get("charges"), 0, 10)
        base_multiplier = number_from_row(row, "Damage Multi") or 0
        multiplier = base_multiplier * (1 + (0.2 * charges))
        return result(round(multiplier, 2), f"{charges} Charges", "Derived from note text")

    return base_result(row)


def calculate_lune(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Lune's effective skill multiplier.

    Args:
        row: The selected Lune skill row.
        state: The normalized Lune control state.

    Returns:
        A normalized calculation result describing the effective multiplier and
        scenario for the selected skill.
    """

    skill = clean_text(row.get("Skill"))
    mode = text_from_row(row, "Lune Mode")
    base_multiplier = number_from_row(row, "Damage Multi")
    conditional = number_from_row(row, "Dmg Con1")
    maximum = number_from_row(row, "Dmg Max")
    all_crit_multiplier = number_from_row(row, "All Crit Dmg")
    condition = text_from_row(row, "Condition 1").lower()
    max_condition = text_from_row(row, "Con Max Dmg").lower()
    stains = clamp_int(state.get("stains"), 0, 4)
    turns = clamp_int(state.get("turns"), 1, 5)
    all_crits = bool(state.get("all_crits"))
    consume_ready = can_satisfy_lune_stains(text_from_row(row, "Consume Stains"), state)
    required_ready = can_satisfy_lune_stains(text_from_row(row, "Required Stains"), state)

    if mode == "utility":
        return result(None, "No direct damage", "Sheet")

    if mode == "utility_extra_turn":
        warning = "Additional turn from consume is not folded into this damage number." if consume_ready else None
        return result(base_multiplier, "Direct hit only", "Damage Multi", warning)

    if mode == "burn" or skill.startswith("Burn "):
        ticks = clamp_int(state.get("turns"), 1, 3)
        return result(round((base_multiplier or 0) * ticks, 2), f"{ticks} Burn tick(s)", "Derived from burn rows")

    if mode == "requires_stains":
        if not required_ready:
            return result(
                None,
                "Missing required stains",
                "Required Stains",
                f"Requires {format_lune_stains(text_from_row(row, 'Required Stains'))}. Light stains can substitute missing elemental stains.",
            )
        return result(base_multiplier, "Required stains met", "Damage Multi")

    if mode == "consume":
        if consume_ready and conditional is not None:
            return result(conditional, text_from_row(row, "Condition 1") or "Consume ready", "Dmg Con1")
        return result(base_multiplier, "Base hit sequence", "Damage Multi")

    if mode == "crit":
        if all_crits and all_crit_multiplier is not None:
            return result(all_crit_multiplier, "All hits crit", "All Crit Dmg")
        return result(base_multiplier, "Base hit sequence", "Damage Multi")

    if mode == "consume_crit":
        if all_crits and consume_ready and maximum is not None:
            return result(maximum, text_from_row(row, "Con Max Dmg") or "Consume + all crits", "Dmg Max")
        if all_crits and all_crit_multiplier is not None:
            return result(all_crit_multiplier, "All hits crit", "All Crit Dmg")
        if consume_ready and conditional is not None:
            return result(conditional, text_from_row(row, "Condition 1") or "Consume ready", "Dmg Con1")
        return result(base_multiplier, "Base hit sequence", "Damage Multi")

    if mode == "duration_consume":
        base_turns = clamp_int(number_from_row(row, "Base Turns"), 1, 10)
        max_turns = clamp_int(number_from_row(row, "Max Turns"), base_turns, 10)
        allowed_turns = max_turns if consume_ready else base_turns
        applied_turns = min(turns, allowed_turns)
        total = round((base_multiplier or 0) * applied_turns, 2)
        warning = None
        if turns > allowed_turns:
            warning = f"Capped at {allowed_turns} turn(s) for the selected stain state."
        scenario = f"{applied_turns} turn(s)"
        if consume_ready:
            scenario = f"{scenario} | consume ready"
        return result(total, scenario, "Damage Multi x turns", warning)

    if mode == "storm_caller":
        per_proc = conditional if consume_ready and conditional is not None else base_multiplier
        total = round((per_proc or 0) * turns, 2)
        scenario = f"{turns} end-turn proc(s)"
        if consume_ready:
            scenario = f"{scenario} | consume ready"
        return result(
            total,
            scenario,
            "Derived from per-proc scaling",
            "Reactive 0.2 follow-up hits from other damage events are not modeled.",
        )

    if mode == "consume_all":
        consumed_stains = stains
        multiplier = round((base_multiplier or 0) * (1 + consumed_stains), 2)
        scenario = "Base hit sequence" if consumed_stains == 0 else f"Consume {consumed_stains} stain(s)"
        return result(multiplier, scenario, "Derived from consume-all scaling")

    if mode == "fire_rage":
        warning = "Per-turn stacking remains unclear in the sheet, so only the immediate hit is modeled."
        if consume_ready and conditional is not None:
            return result(conditional, text_from_row(row, "Condition 1") or "Consume ready", "Dmg Con1", warning)
        return result(base_multiplier, "Immediate hit only", "Damage Multi", warning)

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
    """Calculate Maelle's effective skill multiplier.

    Args:
        row: The selected Maelle skill row.
        state: The normalized Maelle control state.

    Returns:
        A normalized calculation result describing the effective multiplier and
        scenario for the selected skill.
    """

    skill = clean_text(row.get("Skill"))
    mode = text_from_row(row, "Maelle Mode")
    base_multiplier = number_from_row(row, "Damage Multi")
    maximum = number_from_row(row, "DmMax")
    stance = clean_text(state.get("stance")) or "Stanceless"
    burn_stacks = clamp_int(state.get("burn_stacks"), 0, 100)
    hits_taken = clamp_int(state.get("hits_taken"), 0, 5)
    marked = bool(state.get("marked"))
    all_crits = bool(state.get("all_crits"))
    turns = clamp_int(state.get("turns"), 1, 3)

    def with_stance(skill_result: CalculationResult) -> CalculationResult:
        """Apply stance scaling when the selected skill is stance-sensitive.

        Args:
            skill_result: The base result calculated for the current skill.

        Returns:
            The original result when no stance bonus applies, otherwise a new
            result with the stance multiplier folded in.
        """

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

    if mode == "burning_canvas":
        base_scaling = number_from_row(row, "Base Scaling") or base_multiplier or 0
        hit_count = clamp_int(number_from_row(row, "Hit Count"), 1, 20)
        multiplier = sum(
            base_scaling * (1 + (0.1 * (burn_stacks + hit_index)))
            for hit_index in range(hit_count)
        )
        return with_stance(
            result(
                round(multiplier, 2),
                f"{burn_stacks} starting Burn stack(s)",
                "Derived from note text",
            )
        )

    if mode == "combustion":
        multiplier = round((base_multiplier or 0) * (1 + (0.4 * min(burn_stacks, 10))), 2)
        return with_stance(result(multiplier, f"Consume {min(burn_stacks, 10)} Burn", "Derived from note text"))

    if mode == "revenge":
        multiplier = round((base_multiplier or 0) * (1 + (1.5 * hits_taken)), 2)
        return with_stance(result(multiplier, f"{hits_taken} hit(s) taken last round", "Derived from note text"))

    if skill.startswith("Burn "):
        return result(round((base_multiplier or 0) * turns, 2), f"{turns} Burn tick(s)", "Derived from burn rows")

    if mode == "marked" and marked and maximum is not None:
        return with_stance(result(maximum, "Marked target", "DmMax"))

    if mode == "all_crits" and all_crits and maximum is not None:
        return with_stance(result(maximum, "All crits", "DmMax"))

    return with_stance(base_result(row))


def monoco_mask_factor(row: CalculatorRow) -> float | None:
    """Infer Monoco's mask damage factor from sheet breakpoints."""

    base_multiplier = number_from_row(row, "Damage Multi")
    masked_multiplier = number_from_row(row, "Dmg Con1")
    if base_multiplier in (None, 0) or masked_multiplier is None:
        return None
    return masked_multiplier / base_multiplier


def monoco_secondary_only_multiplier(row: CalculatorRow) -> float | None:
    """Infer a Monoco secondary-condition multiplier without mask bonus."""

    maximum = number_from_row(row, "Dmg Max")
    mask_factor = monoco_mask_factor(row)
    if maximum is None or mask_factor in (None, 0):
        return None
    return round(maximum / mask_factor, 2)


def uses_mask_condition(row: CalculatorRow) -> bool:
    """Check whether a Monoco row explicitly references mask state.

    Args:
        row: The selected Monoco skill row.

    Returns:
        ``True`` when the row's condition or notes mention masks, otherwise
        ``False``.
    """

    texts = (
        text_from_row(row, "Condition 1"),
        text_from_row(row, "Con Max Dmg"),
        text_from_row(row, "Notes"),
    )
    return any("mask" in text.lower() for text in texts if text)


def monoco_mask_type(row: CalculatorRow) -> str:
    """Read the mask type associated with a Monoco skill row.

    Args:
        row: The selected Monoco skill row.

    Returns:
        The normalized mask label from the row, or an empty string when the row
        has no mask value.
    """

    return clean_text(row.get("Mask")).strip()


def has_explicit_monoco_mask_breakpoint(row: CalculatorRow) -> bool:
    """Check whether the sheet already includes a mask-specific breakpoint.

    Args:
        row: The selected Monoco skill row.

    Returns:
        ``True`` when the row's condition columns already describe a masked
        breakpoint, otherwise ``False``.
    """

    texts = (
        text_from_row(row, "Condition 1"),
        text_from_row(row, "Con Max Dmg"),
    )
    return any("mask" in text.lower() for text in texts if text)


def can_apply_generic_monoco_mask_bonus(row: CalculatorRow) -> bool:
    """Determine whether Monoco's generic mask bonus should apply.

    Args:
        row: The selected Monoco skill row.

    Returns:
        ``True`` when the row has a non-gradient mask type and no explicit
        sheet breakpoint for that mask, otherwise ``False``.
    """

    mask_type = monoco_mask_type(row).upper()
    return bool(mask_type and mask_type != "GRADIENT" and not has_explicit_monoco_mask_breakpoint(row))


def apply_monoco_mask_bonus(row: CalculatorRow, skill_result: CalculationResult) -> CalculationResult:
    """Apply Monoco's fallback generic mask multiplier.

    Args:
        row: The selected Monoco skill row.
        skill_result: The current calculated result before any generic mask
            bonus is applied.

    Returns:
        The original result when no generic mask bonus applies, otherwise a new
        result with the mask multiplier included.
    """

    multiplier = skill_result.get("multiplier")
    if multiplier is None or not can_apply_generic_monoco_mask_bonus(row):
        return skill_result

    mask_type = monoco_mask_type(row).upper()
    bonus_multiplier = 5.0 if mask_type == "ALMIGHTY" else 3.0
    label = "Almighty mask" if mask_type == "ALMIGHTY" else f"{monoco_mask_type(row)} mask"

    return result(
        round(multiplier * bonus_multiplier, 2),
        f"{skill_result['scenario']} | {label} bonus",
        f"{skill_result['source']} + generic mask bonus",
        skill_result.get("warning"),
    )


def calculate_monoco(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Monoco's effective skill multiplier.

    Args:
        row: The selected Monoco skill row.
        state: The normalized Monoco control state.

    Returns:
        A normalized calculation result describing the effective multiplier and
        scenario for the selected skill.
    """

    skill = clean_text(row.get("Skill"))
    mode = text_from_row(row, "Monoco Mode")
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

    def with_generic_mask(skill_result: CalculationResult) -> CalculationResult:
        """Conditionally apply Monoco's generic mask bonus.

        Args:
            skill_result: The base result calculated for the current skill.

        Returns:
            The original result when the mask is inactive, otherwise the result
            after applying any eligible generic mask bonus.
        """

        if not mask_active:
            return skill_result
        return apply_monoco_mask_bonus(row, skill_result)

    def mask_mode_result(active_label: str, extra_active: bool) -> CalculationResult:
        secondary_only = monoco_secondary_only_multiplier(row)
        if mask_active and extra_active and maximum is not None:
            return result(maximum, f"Mask active + {active_label}", "Dmg Max")
        if extra_active and secondary_only is not None:
            return result(secondary_only, active_label, "Derived from Dmg Max / mask factor")
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")
        return base_result(row)

    if skill.startswith("Burn "):
        return result(round((base_multiplier or 0) * turns, 2), f"{turns} Burn tick(s)", "Derived from burn rows")

    if mode == "utility":
        return result(None, "No direct damage", "Sheet")

    if mode == "cost_mask":
        return result(base_multiplier, "Direct hit only", "Damage Multi")

    if mode == "stunned":
        if stunned and maximum is not None:
            return result(maximum, "Stunned target", "Dmg Max")
        return base_result(row)

    if mode == "mask":
        if mask_active and conditional is not None:
            return result(conditional, "Mask active", "Dmg Con1")
        return base_result(row)

    if mode == "mask_stunned":
        return mask_mode_result("stunned target", stunned)

    if mode == "mask_marked":
        return mask_mode_result("marked target", marked)

    if mode == "mask_powerless":
        return mask_mode_result("powerless target", powerless)

    if mode == "mask_burning":
        return mask_mode_result("burning target", burning)

    if mode == "mask_low_life":
        return mask_mode_result("low life", low_life)

    if mode == "mask_full_life":
        return mask_mode_result("full life", full_life)

    if mode == "mask_all_crits":
        return mask_mode_result("all crits", all_crits)

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

    if mask_active and has_explicit_monoco_mask_breakpoint(row) and conditional is not None:
        return result(conditional, "Mask active", "Dmg Con1")

    return with_generic_mask(base_result(row))


def effective_sciel_foretell(foretell: int, twilight: bool) -> int:
    """Calculate Sciel's Twilight-adjusted foretell count.

    Args:
        foretell: The applied foretell count from the UI.
        twilight: Whether Twilight is currently active.

    Returns:
        The effective foretell count used by Sciel's formulas.
    """

    if twilight:
        return max(foretell, 0) * 2
    return max(foretell, 0)


def calculate_sciel(row: CalculatorRow, state: CalculatorState) -> CalculationResult:
    """Calculate Sciel's effective skill multiplier.

    Args:
        row: The selected Sciel skill row.
        state: The normalized Sciel control state.

    Returns:
        A normalized calculation result describing the effective multiplier and
        scenario for the selected skill.
    """

    skill = clean_text(row.get("Skill"))
    base_multiplier = number_from_row(row, "Damage Multi")
    conditional = number_from_row(row, "ConDmg")
    twilight_value = number_from_row(row, "TwilightDmg")
    foretell = max(clamp_int(state.get("foretell"), 0, 999), 0)
    twilight = bool(state.get("twilight"))
    full_life = bool(state.get("full_life"))
    effective_foretell = effective_sciel_foretell(foretell, twilight)

    if skill in SCIEL_FORETELL_RATES:
        rate = SCIEL_FORETELL_RATES[skill]
        multiplier = (base_multiplier or 0) * (1 + (rate * effective_foretell))
        scenario = f"{effective_foretell} Twilight-effective Foretell" if twilight else f"{foretell} Foretell"
        source = "Derived from note text"
        if twilight:
            multiplier *= 1.5
            scenario = f"{scenario} from {foretell} applied Foretell, Twilight"
            source = "Derived from note text + Twilight"
        return result(round(multiplier, 2), scenario, source)

    if skill == "Our Sacrifice":
        multiplier = (base_multiplier or 0) * (1 + (0.3 * effective_foretell))
        scenario_parts = [f"{effective_foretell} Twilight-effective Foretell" if twilight else f"{foretell} Foretell"]
        if full_life:
            multiplier *= 3.97
            scenario_parts.append("Full life")
        if twilight:
            multiplier *= 1.5
            scenario_parts.append(f"Twilight from {foretell} applied Foretell")
        return result(round(multiplier, 2), ", ".join(scenario_parts), "Derived from note text")

    if skill == "Sealed Fate":
        if foretell >= 1 and twilight and twilight_value is not None:
            return result(twilight_value, f"{effective_foretell} Twilight-effective Foretell, Twilight", "TwilightDmg")
        if foretell >= 1 and conditional is not None:
            return result(conditional, f"{foretell} Foretell", "ConDmg")
        return base_result(row)

    if skill == "Firing Shadow":
        consumed_foretell = min(effective_foretell, 3)
        multiplier = (base_multiplier or 0) * (1 + (consumed_foretell / 3))
        scenario = (
            f"{consumed_foretell} Twilight-effective Foretell consumed from {foretell} applied Foretell"
            if twilight
            else f"{consumed_foretell} Foretell consumed"
        )
        if twilight:
            multiplier *= 1.5
        return result(round(multiplier, 2), scenario, "Derived from note text")

    if twilight and twilight_value is not None:
        return result(twilight_value, f"Twilight from {foretell} applied Foretell", "TwilightDmg")

    return base_result(row)


def apply_verso_rank_bonus(
    rank: str,
    skill_result: CalculationResult,
    enabled: bool = True,
) -> CalculationResult:
    """Apply Verso's general rank multiplier when appropriate.

    Args:
        rank: The currently selected Verso rank.
        skill_result: The current calculated result before the general rank
            bonus is applied.
        enabled: Whether the general rank bonus should be applied at all.

    Returns:
        The original result when no general rank bonus applies, otherwise a new
        result with the rank multiplier included.
    """

    multiplier = skill_result.get("multiplier")
    source = skill_result.get("source", "")
    if multiplier is None or source == "SRankMAX" or not enabled:
        return skill_result

    rank_bonus = {
        "D": 1.0,
        "C": 1.25,
        "B": 1.5,
        "A": 2.0,
        "S": 3.0,
    }.get(rank, 1.0)

    if rank_bonus == 1.0:
        return skill_result

    return result(
        round(multiplier * rank_bonus, 2),
        f"{skill_result['scenario']} | {rank} Rank bonus",
        f"{source} + general rank bonus",
        skill_result.get("warning"),
    )


def calculate_verso(
    row: CalculatorRow,
    state: CalculatorState,
    disable_rank_bonus: bool = False,
) -> CalculationResult:
    """Calculate Verso's effective skill multiplier.

    Args:
        row: The selected Verso skill row.
        state: The normalized Verso control state.
        disable_rank_bonus: Whether weapon effects should suppress Verso's
            generic rank bonus.

    Returns:
        A normalized calculation result describing the effective multiplier and
        scenario for the selected skill.
    """

    skill = clean_text(row.get("Skill"))
    mode = text_from_row(row, "Verso Mode")
    base_multiplier = number_from_row(row, "Damage Multi")
    conditional = number_from_row(row, "ConDmg")
    maximum = number_from_row(row, "SRankMAX")
    rank = clean_text(state.get("rank")) or "D"
    stunned = bool(state.get("stunned"))
    speed_bonus = bool(state.get("speed_bonus"))
    shots = clamp_int(state.get("shots"), 0, 10)
    uses = clamp_int(state.get("uses"), 1, 6)
    missing_health = clamp_int(state.get("missing_health"), 0, 99)
    required_rank = parse_rank_requirement(text_from_row(row, "Condition"))

    if mode == "utility":
        return result(None, "No direct damage", "Sheet")

    if mode == "direct":
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if mode == "rank_damage":
        if not disable_rank_bonus and rank_matches(rank, required_rank) and conditional is not None:
            return apply_verso_rank_bonus(
                rank,
                result(conditional, f"{required_rank} Rank", "ConDmg"),
                not disable_rank_bonus,
            )
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if mode == "rank_cost":
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if mode == "end_bringer":
        if stunned and conditional is not None:
            return apply_verso_rank_bonus(
                rank,
                result(conditional, "Stunned target", "ConDmg"),
                not disable_rank_bonus,
            )
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if mode == "follow_up":
        multiplier = round((base_multiplier or 0) * (1 + (0.5 * shots)), 2)
        scenario = "Base value" if shots == 0 else f"{shots} ranged shot(s)"
        return apply_verso_rank_bonus(
            rank,
            result(multiplier, scenario, "Derived from note text"),
            not disable_rank_bonus,
        )

    if mode == "ascending_assault":
        bonus_uses = max(uses - 1, 0)
        multiplier = round((base_multiplier or 0) * (1 + (0.3 * min(bonus_uses, 5))), 2)
        scenario = "Base value" if uses <= 1 else f"Use {uses}"
        return apply_verso_rank_bonus(
            rank,
            result(multiplier, scenario, "Derived from note text"),
            not disable_rank_bonus,
        )

    if mode == "speed_burst":
        rank_ready = not disable_rank_bonus and rank_matches(rank, required_rank)
        if speed_bonus and rank_ready and maximum is not None:
            return result(maximum, f"{required_rank} Rank + max speed bonus", "SRankMAX")
        if speed_bonus:
            return apply_verso_rank_bonus(
                rank,
                result(round((base_multiplier or 0) * 2, 2), "Max speed bonus", "Derived from note text"),
                not disable_rank_bonus,
            )
        if rank_ready and conditional is not None:
            return apply_verso_rank_bonus(
                rank,
                result(conditional, f"{required_rank} Rank", "ConDmg"),
                not disable_rank_bonus,
            )
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if mode == "steeled_strike":
        if not disable_rank_bonus and rank_matches(rank, required_rank) and conditional is not None:
            return apply_verso_rank_bonus(
                rank,
                result(
                    conditional,
                    "S Rank after full charge",
                    "ConDmg",
                    "This attack still assumes Verso completed the charge without taking damage.",
                ),
                not disable_rank_bonus,
            )
        return apply_verso_rank_bonus(
            rank,
            result(
                base_multiplier,
                "Charge completed",
                "Damage Multi",
                "This attack still assumes Verso completed the charge without taking damage.",
            ),
            not disable_rank_bonus,
        )

    if mode == "berserk":
        multiplier = base_multiplier or 0
        scenario_parts = [f"{missing_health}% missing HP"]
        if not disable_rank_bonus and rank_matches(rank, required_rank):
            multiplier *= 1 + (0.15 * missing_health)
            scenario_parts.append(f"{required_rank} Rank")
        return apply_verso_rank_bonus(
            rank,
            result(round(multiplier, 2), " | ".join(scenario_parts), "Derived from note text"),
            not disable_rank_bonus,
        )

    if skill == "End Bringer":
        if stunned and rank == "S" and maximum is not None:
            return result(maximum, "Stunned target at S Rank", "SRankMAX")
        if stunned and conditional is not None:
            return apply_verso_rank_bonus(rank, result(conditional, "Stunned target", "ConDmg"), not disable_rank_bonus)
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if skill == "Steeled Strike":
        if rank == "S" and uses >= 2 and maximum is not None:
            return result(maximum, "S Rank with full setup", "SRankMAX")
        if rank == "S" and conditional is not None:
            return apply_verso_rank_bonus(rank, result(conditional, "S Rank", "ConDmg"), not disable_rank_bonus)
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if skill == "Follow Up":
        if rank == "S" and shots >= 10 and maximum is not None:
            return result(maximum, "10 shots at S Rank", "SRankMAX")
        if shots > 0:
            multiplier = round((base_multiplier or 0) * (1 + (0.5 * shots)), 2)
            return apply_verso_rank_bonus(rank, result(multiplier, f"{shots} ranged shot(s)", "Derived from note text"), not disable_rank_bonus)
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if skill == "Ascending Assault":
        if rank == "S" and uses >= 6 and maximum is not None:
            return result(maximum, "6th use at S Rank", "SRankMAX")
        if uses >= 2:
            multiplier = round((base_multiplier or 0) * (1 + (0.3 * min(uses - 1, 5))), 2)
            if uses >= 6 and conditional is not None:
                return apply_verso_rank_bonus(rank, result(conditional, "6th use", "ConDmg"), not disable_rank_bonus)
            return apply_verso_rank_bonus(rank, result(multiplier, f"Use {uses}", "Derived from note text"), not disable_rank_bonus)
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if skill == "Speed Burst":
        if speed_bonus and maximum is not None:
            return result(maximum, "C Rank with full speed bonus", "SRankMAX")
        if rank_matches(rank, "C") and conditional is not None:
            return apply_verso_rank_bonus(rank, result(conditional, "C Rank", "ConDmg"), not disable_rank_bonus)
        return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)

    if rank == "S" and maximum is not None and skill not in {"Ranged Attack", "Basic Attack", "Counter"}:
        return result(maximum, "S Rank", "SRankMAX")

    if rank_matches(rank, required_rank) and conditional is not None:
        return apply_verso_rank_bonus(rank, result(conditional, f"{required_rank} Rank", "ConDmg"), not disable_rank_bonus)

    return apply_verso_rank_bonus(rank, base_result(row), not disable_rank_bonus)


CALCULATORS = {
    "gustave": calculate_gustave,
    "lune": calculate_lune,
    "maelle": calculate_maelle,
    "monoco": calculate_monoco,
    "sciel": calculate_sciel,
    "verso": calculate_verso,
}


def calculate_skill_result(
    character: str,
    row: CalculatorRow,
    state: CalculatorState,
    disable_verso_rank_bonus: bool = False,
) -> CalculationResult:
    """Dispatch calculation to the active character-specific handler.

    Args:
        character: The calculator character id.
        row: The selected skill row for that character.
        state: The normalized character state from the UI.
        disable_verso_rank_bonus: Whether weapon effects should suppress
            Verso's generic rank bonus.

    Returns:
        The calculated result produced by the character-specific calculator.
    """

    if character == "verso":
        return calculate_verso(row, state, disable_verso_rank_bonus)
    return CALCULATORS[character](row, state)


def resolve_picto_attack_type(row: CalculatorRow, override: str | None) -> str:
    """Resolve the attack type used for Picto evaluation.

    Args:
        row: The selected calculator row.
        override: The optional Picto attack-type override from the UI.

    Returns:
        The attack type label used to evaluate attack-specific Picto bonuses.
    """

    if override and override != "Auto":
        return override

    explicit_attack_type = clean_text(row.get("Attack Type"))
    if explicit_attack_type:
        return explicit_attack_type

    skill = clean_text(row.get("Skill")).lower()
    if skill == "basic attack":
        return "Base Attack"
    if skill == "counter":
        return "Counterattack"
    if skill == "ranged attack":
        return "Free Aim"
    if "gradient attack" in skill:
        return "Gradient Attack"
    return "Skill"


def apply_picto_bonus(skill_result: CalculationResult, picto_summary: PictoSummary) -> CalculationResult:
    """Apply the combined Picto multiplier to a skill result.

    Args:
        skill_result: The calculated result before Picto scaling.
        picto_summary: The evaluated Picto summary containing the combined
            multiplier and status details.

    Returns:
        The original result when no Picto multiplier applies, otherwise a new
        result with the Picto factor folded into the multiplier.
    """

    multiplier = skill_result.get("multiplier")
    total_factor = picto_summary["total_factor"]
    if multiplier is None or not picto_summary["active"] or total_factor == 1:
        return skill_result

    return result(
        round(multiplier * total_factor, 2),
        skill_result["scenario"],
        f"{skill_result['source']} + Pictos",
        skill_result.get("warning"),
    )


def apply_weapon_bonus(skill_result: CalculationResult, weapon_summary: WeaponSummary) -> CalculationResult:
    """Apply the combined weapon multiplier to a skill result.

    Args:
        skill_result: The calculated result before weapon scaling.
        weapon_summary: The evaluated weapon summary containing the combined
            multiplier and passive details.

    Returns:
        The original result when no weapon multiplier applies, otherwise a new
        result with the weapon factor folded into the multiplier.
    """

    multiplier = skill_result.get("multiplier")
    total_factor = weapon_summary["total_factor"]
    if multiplier is None or not weapon_summary["active"] or total_factor == 1:
        return skill_result

    return result(
        round(multiplier * total_factor, 2),
        skill_result["scenario"],
        f"{skill_result['source']} + Weapon",
        skill_result.get("warning"),
    )


def build_skill_control_styles(character: str, row: CalculatorRow) -> ControlStyles:
    """Build per-control visibility styles for the selected skill.

    Args:
        character: The calculator character id.
        row: The selected skill row for that character.

    Returns:
        A mapping of control ids to visibility styles used by the setup panel.
    """

    skill = clean_text(row.get("Skill"))
    condition = text_from_row(row, "Condition 1", "Condition").lower()
    max_condition = text_from_row(row, "Con Max Dmg", "ConTwilight").lower()
    styles: ControlStyles = {}

    def set_visibility(control: str, is_visible: bool) -> None:
        """Store a visible or hidden style for a control.

        Args:
            control: The logical control name.
            is_visible: Whether the control should be shown.

        Returns:
            ``None``. The function mutates ``styles`` in place.
        """

        styles[control] = VISIBLE_STYLE if is_visible else HIDDEN_STYLE

    if character == "gustave":
        set_visibility("gustave_charges", skill.startswith("Overcharge"))
        return styles

    if character == "lune":
        mode = text_from_row(row, "Lune Mode")
        uses_exact_stains = mode in {"consume", "consume_crit", "duration_consume", "fire_rage", "storm_caller", "requires_stains"}

        set_visibility("lune_stains", mode == "consume_all")
        for stain_key in LUNE_STAIN_KEYS:
            set_visibility(f"lune_{stain_key}", uses_exact_stains)
        set_visibility("lune_turns", mode in {"duration_consume", "storm_caller", "burn"} or skill.startswith("Burn "))
        set_visibility("lune_all_crits", mode in {"crit", "consume_crit"})
        return styles

    if character == "maelle":
        mode = text_from_row(row, "Maelle Mode")
        set_visibility("maelle_stance", not skill.startswith("Burn ") and number_from_row(row, "Damage Multi") is not None)
        set_visibility("maelle_burn_stacks", mode in {"burning_canvas", "combustion"})
        set_visibility("maelle_hits_taken", mode == "revenge")
        set_visibility("maelle_marked", mode == "marked")
        set_visibility("maelle_all_crits", mode == "all_crits")
        return styles

    if character == "monoco":
        mode = text_from_row(row, "Monoco Mode")
        set_visibility("monoco_turns", skill.startswith("Burn "))
        set_visibility(
            "monoco_mask",
            mode in {
                "cost_mask",
                "mask",
                "mask_stunned",
                "mask_marked",
                "mask_powerless",
                "mask_burning",
                "mask_low_life",
                "mask_full_life",
                "mask_all_crits",
            }
            or (not mode and (uses_mask_condition(row) or can_apply_generic_monoco_mask_bonus(row))),
        )
        set_visibility("monoco_stunned", mode in {"stunned", "mask_stunned"} or skill == "Mighty Strike")
        set_visibility("monoco_marked", mode == "mask_marked")
        set_visibility("monoco_powerless", mode == "mask_powerless")
        set_visibility("monoco_burning", mode == "mask_burning")
        set_visibility("monoco_low_life", mode == "mask_low_life")
        set_visibility("monoco_full_life", mode == "mask_full_life")
        set_visibility("monoco_all_crits", mode == "mask_all_crits")
        return styles

    if character == "sciel":
        set_visibility("sciel_foretell", skill in SCIEL_FORETELL_RATES or skill in {"Our Sacrifice", "Sealed Fate", "Firing Shadow"})
        set_visibility("sciel_twilight", number_from_row(row, "TwilightDmg") is not None)
        set_visibility("sciel_full_life", skill == "Our Sacrifice")
        return styles

    if character == "verso":
        mode = text_from_row(row, "Verso Mode")
        set_visibility("verso_rank", mode in {"rank_damage", "rank_cost", "follow_up", "ascending_assault", "speed_burst", "steeled_strike", "berserk"} or (
            not mode
            and skill not in {"Ranged Attack", "Basic Attack", "Counter"}
            and (
                parse_rank_requirement(text_from_row(row, "Condition")) is not None
                or number_from_row(row, "SRankMAX") is not None
                or skill in {"Follow Up", "Ascending Assault", "Speed Burst", "End Bringer", "Steeled Strike"}
            )
        ))
        set_visibility("verso_shots", mode == "follow_up" or (not mode and skill == "Follow Up"))
        set_visibility("verso_uses", mode == "ascending_assault" or (not mode and skill in {"Steeled Strike", "Ascending Assault"}))
        set_visibility("verso_stunned", mode == "end_bringer" or skill == "End Bringer")
        set_visibility("verso_speed_bonus", mode == "speed_burst" or skill == "Speed Burst")
        set_visibility("verso_missing_health", mode == "berserk")
        return styles

    return styles
