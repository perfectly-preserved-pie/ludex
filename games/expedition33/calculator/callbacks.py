from __future__ import annotations
from dash import html, Input, Output, State, callback, no_update
from loguru import logger
from typing import Any, TypeAlias, TypedDict
from games.expedition33.calculator.core import (
    AffinityDetails,
    calculate_current_cost,
    CALCULATOR_DATA,
    CalculationResult,
    CalculatorRow,
    CalculatorState,
    CHARACTER_META,
    CharacterStyles,
    clamp_int,
    ComponentChildren,
    ControlStyles,
    DEFAULT_CHARACTER,
    DEFAULT_SKILLS,
    get_row,
    HIDDEN_STYLE,
    normalize_affinity,
    NumericInput,
    parse_number,
    resolve_affinity,
    skill_options_for,
    SkillOption,
    StyleRule,
    ToggleInput,
    VISIBLE_STYLE,
)
from games.expedition33.calculator.ui.result_views import (
    build_comparison_overview,
    build_result_body,
    build_summary_body,
)
from games.expedition33.calculator.logic import (
    apply_weapon_bonus,
    apply_picto_bonus,
    build_skill_control_styles,
    calculate_skill_result,
    resolve_picto_attack_type,
)
from games.expedition33.calculator.pictos import PictoSummary, evaluate_pictos, required_picto_controls
from games.expedition33.calculator.save_import import SaveImportError, parse_uploaded_save
from games.expedition33.calculator.weapons import (
    WeaponSummary,
    evaluate_weapon,
    normalize_weapon_level,
    required_weapon_character_controls,
    required_weapon_controls,
    weapon_options_for,
)

SkillDropdownUpdate: TypeAlias = tuple[list[SkillOption], str, list[SkillOption], str | None, float]
VisibleControlsUpdate: TypeAlias = tuple[Any, ...]
CalculatorResultPanels: TypeAlias = tuple[
    StyleRule,
    ComponentChildren,
    int,
    ComponentChildren,
    ComponentChildren,
    StyleRule,
    ComponentChildren,
    ComponentChildren,
]

class EvaluatedSkillView(TypedDict):
    """Fully evaluated calculator state for one selected skill."""

    row: CalculatorRow
    affinity: AffinityDetails
    picto_summary: PictoSummary
    weapon_summary: WeaponSummary
    skill_result: CalculationResult
    current_cost: str
    total_bonus_factor: float


def imported_build(save_import: dict[str, Any] | None, character: str) -> dict[str, Any] | None:
    """Return the imported build payload for one character when available."""

    if not isinstance(save_import, dict):
        return None
    characters = save_import.get("characters")
    if not isinstance(characters, dict):
        return None
    build = characters.get(character)
    return build if isinstance(build, dict) else None


def build_import_summary(build: dict[str, Any], filename: str) -> ComponentChildren:
    """Render a compact summary of the currently imported build."""

    attributes = build.get("attributes", {})
    attribute_text = (
        ", ".join(f"{name}: {value}" for name, value in attributes.items())
        if isinstance(attributes, dict) and attributes
        else "No assigned attribute points found."
    )
    weapon_name = build.get("equipped_weapon") or build.get("raw_equipped_weapon") or "None"
    raw_weapon_level = build.get("raw_weapon_level")
    weapon_level = build.get("weapon_level")
    if raw_weapon_level is None:
        weapon_level_text = "No weapon progression found."
    else:
        weapon_level_text = f"Save level {raw_weapon_level} -> calculator passive tier {weapon_level}"

    matched_skills = ", ".join(build.get("equipped_skills") or []) or "No equipped skills matched the calculator list."
    unmatched_skills = ", ".join(build.get("unmatched_skills") or []) or "None"
    matched_pictos = ", ".join(build.get("equipped_pictos") or []) or "No supported equipped lumina were matched."
    unmatched_pictos = ", ".join(build.get("unmatched_pictos") or []) or "None"

    return [
        html.P(f"Source: {filename}", className="mb-2"),
        html.P(f"Level: {build.get('level', 0)}", className="mb-1"),
        html.P(
            f"Lumina from consumables: {build.get('lumina_from_consumables', 0)}",
            className="mb-1",
        ),
        html.P(f"Attributes: {attribute_text}", className="mb-1"),
        html.P(f"Equipped weapon: {weapon_name}", className="mb-1"),
        html.P(weapon_level_text, className="mb-1"),
        html.P(f"Matched equipped skills: {matched_skills}", className="mb-1"),
        html.P(f"Unmatched save skill ids: {unmatched_skills}", className="mb-1"),
        html.P(f"Matched equipped lumina: {matched_pictos}", className="mb-1"),
        html.P(f"Unmatched save lumina ids: {unmatched_pictos}", className="mb-0"),
    ]


def build_character_section_styles(active_character: str) -> tuple[list[str], CharacterStyles]:
    """Build accordion state for the active character section.

    Args:
        active_character: The character id currently selected in the UI.

    Returns:
        A tuple containing the accordion item to open and the per-character
        visibility styles for each setup section.
    """

    active_item = [f"setup-{active_character}"]
    styles = {
        character: VISIBLE_STYLE if character == active_character else HIDDEN_STYLE
        for character in CALCULATOR_DATA
    }
    return active_item, styles


def control_style(control_styles: ControlStyles, control: str) -> StyleRule:
    """Read the visibility style for a single control.

    Args:
        control_styles: The full control-style mapping for the selected skill.
        control: The logical control name to look up.

    Returns:
        The control's style rule, defaulting to the shared hidden style.
    """

    return control_styles.get(control, HIDDEN_STYLE)


def merge_control_styles(*style_sets: ControlStyles) -> ControlStyles:
    """Merge multiple control-style maps, keeping any visible control visible.

    Args:
        *style_sets: One or more control-style mappings to combine.

    Returns:
        A merged style map where a control remains visible if any input mapping
        marks it visible.
    """

    merged: ControlStyles = {}
    for style_set in style_sets:
        for control, style in style_set.items():
            if style == VISIBLE_STYLE:
                merged[control] = VISIBLE_STYLE
            elif control not in merged:
                merged[control] = HIDDEN_STYLE
    return merged


def empty_state_style(control_styles: ControlStyles, prefix: str) -> StyleRule:
    """Decide whether a character section should show its empty-state notice.

    Args:
        control_styles: The full control-style mapping for the selected skill.
        prefix: The control-name prefix belonging to a single character section.

    Returns:
        The visible style when no controls in the section are shown, otherwise
        the hidden style.
    """

    has_visible_control = any(
        key.startswith(prefix) and value == VISIBLE_STYLE
        for key, value in control_styles.items()
    )
    return HIDDEN_STYLE if has_visible_control else VISIBLE_STYLE


def build_calculator_states(
    gustave_charges: NumericInput,
    lune_stains: NumericInput,
    lune_earth_stains: NumericInput,
    lune_fire_stains: NumericInput,
    lune_ice_stains: NumericInput,
    lune_lightning_stains: NumericInput,
    lune_light_stains: NumericInput,
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
    verso_missing_health: NumericInput,
) -> dict[str, CalculatorState]:
    """Normalize raw callback inputs into per-character calculator state.

    Args:
        gustave_charges: Gustave's Overcharge count.
        lune_stains: Lune's fallback active stain count.
        lune_earth_stains: Lune's active Earth Stain count.
        lune_fire_stains: Lune's active Fire Stain count.
        lune_ice_stains: Lune's active Ice Stain count.
        lune_lightning_stains: Lune's active Lightning Stain count.
        lune_light_stains: Lune's active Light Stain count.
        lune_turns: The number of turns elapsed for turn-based Lune skills.
        lune_all_crits: Whether all relevant Lune hits crit.
        maelle_stance: Maelle's current stance.
        maelle_burn_stacks: Burn stacks consumed or referenced by Maelle skills.
        maelle_hits_taken: Hits Maelle took in the previous round.
        maelle_marked: Whether the target is marked for Maelle.
        maelle_all_crits: Whether all relevant Maelle hits crit.
        monoco_turns: Burn turns elapsed for Monoco skills.
        monoco_mask: Whether Monoco's mask bonus is active.
        monoco_stunned: Whether the target is stunned for Monoco.
        monoco_marked: Whether the target is marked for Monoco.
        monoco_powerless: Whether the target is powerless.
        monoco_burning: Whether the target is burning.
        monoco_low_life: Whether the target is at low life.
        monoco_full_life: Whether the target is at full life.
        monoco_all_crits: Whether all relevant Monoco hits crit.
        sciel_foretell: Sciel's applied foretell count.
        sciel_twilight: Whether Twilight is active for Sciel.
        sciel_full_life: Whether Sciel is at full life.
        verso_rank: Verso's current rank.
        verso_shots: The number of stored shots for Follow Up.
        verso_uses: The use count for repeat-use Verso skills.
        verso_stunned: Whether Verso's target is stunned.
        verso_speed_bonus: Whether Verso has the full speed bonus active.
        verso_missing_health: Verso's missing HP percentage for Berserk Slash.

    Returns:
        A mapping of character ids to the normalized state dictionary expected
        by the calculator logic.
    """

    lune_elemental_stains = {
        "earth_stains": clamp_int(lune_earth_stains, 0, 4),
        "fire_stains": clamp_int(lune_fire_stains, 0, 4),
        "ice_stains": clamp_int(lune_ice_stains, 0, 4),
        "lightning_stains": clamp_int(lune_lightning_stains, 0, 4),
        "light_stains": clamp_int(lune_light_stains, 0, 4),
    }
    typed_lune_stains = sum(lune_elemental_stains.values())

    return {
        "gustave": {
            "charges": gustave_charges,
        },
        "lune": {
            "stains": min(4, typed_lune_stains) if typed_lune_stains > 0 else clamp_int(lune_stains, 0, 4),
            "turns": lune_turns,
            "all_crits": lune_all_crits,
            **lune_elemental_stains,
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
            "missing_health": verso_missing_health,
        },
    }


def build_picto_state(
    resolved_attack_type: str,
    picto_below_10_health: ToggleInput,
    picto_target_burning: ToggleInput,
    picto_target_stunned: ToggleInput,
    picto_exhausted: ToggleInput,
    picto_full_health: ToggleInput,
    picto_unhit: ToggleInput,
    picto_inverted: ToggleInput,
    picto_consume_ap: ToggleInput,
    picto_shield_points: NumericInput,
    picto_fighting_alone: ToggleInput,
    picto_all_allies_alive: ToggleInput,
    picto_status_effects: NumericInput,
    picto_dodge_stacks: NumericInput,
    picto_parry_stacks: NumericInput,
    picto_warming_up_stacks: NumericInput,
    picto_first_hit: ToggleInput,
) -> dict[str, Any]:
    """Normalize raw callback inputs into Picto evaluation state.

    Args:
        resolved_attack_type: The attack type used for attack-specific Pictos.
        picto_below_10_health: Whether the user is below 10% health.
        picto_target_burning: Whether the target is burning.
        picto_target_stunned: Whether the target is stunned.
        picto_exhausted: Whether the user is exhausted.
        picto_full_health: Whether the user is at full health.
        picto_unhit: Whether the user has not been hit yet.
        picto_inverted: Whether the user is inverted.
        picto_consume_ap: Whether the attack consumes AP on hit.
        picto_shield_points: The current shield-point count.
        picto_fighting_alone: Whether the active character is alone.
        picto_all_allies_alive: Whether all allies are alive.
        picto_status_effects: The number of status effects on self.
        picto_dodge_stacks: The current Empowering Dodge stack count.
        picto_parry_stacks: The current Empowering Parry stack count.
        picto_warming_up_stacks: The current Warming Up stack count.
        picto_first_hit: Whether the current hit is the first hit of battle.

    Returns:
        A normalized Picto state dictionary consumed by ``evaluate_pictos``.
    """

    return {
        "attack_type": resolved_attack_type,
        "below_10_health": picto_below_10_health,
        "target_burning": picto_target_burning,
        "target_stunned": picto_target_stunned,
        "exhausted": picto_exhausted,
        "full_health": picto_full_health,
        "unhit": picto_unhit,
        "inverted": picto_inverted,
        "consume_ap": picto_consume_ap,
        "shield_points": picto_shield_points,
        "fighting_alone": picto_fighting_alone,
        "all_allies_alive": picto_all_allies_alive,
        "status_effects": picto_status_effects,
        "dodge_stacks": picto_dodge_stacks,
        "parry_stacks": picto_parry_stacks,
        "warming_up_stacks": picto_warming_up_stacks,
        "first_hit": picto_first_hit,
    }


def build_weapon_state(
    resolved_attack_type: str,
    picto_shield_points: NumericInput,
    weapon_unhit_turns: NumericInput,
    weapon_stain_consume_stacks: NumericInput,
    weapon_light_stains: NumericInput,
    weapon_dark_stains: NumericInput,
    weapon_self_burn_stacks: NumericInput,
    sciel_foretell: NumericInput,
    sciel_twilight: ToggleInput,
    weapon_moon_charges: NumericInput,
    weapon_cursed: ToggleInput,
    weapon_ap_consumed: NumericInput,
    weapon_critical_hit: ToggleInput,
    weapon_monoco_mask_type: str | None,
    verso_rank: str | None,
) -> dict[str, Any]:
    """Normalize raw callback inputs into weapon evaluation state.

    Args:
        resolved_attack_type: The attack type used for attack-specific bonuses.
        picto_shield_points: Shared shield-point input used by Pictos and
            weapons.
        weapon_unhit_turns: Consecutive no-hit turns or stacks.
        weapon_stain_consume_stacks: Lune's current stain-consume stack count.
        weapon_light_stains: The active Light Stain count.
        weapon_dark_stains: The active Dark Stain count.
        weapon_self_burn_stacks: Maelle's self Burn stack count.
        sciel_foretell: Sciel's applied foretell count.
        sciel_twilight: Whether Twilight is active for Sciel.
        weapon_moon_charges: The active Moon charge count.
        weapon_cursed: Whether the character is Cursed.
        weapon_ap_consumed: The AP consumed by the current attack.
        weapon_critical_hit: Whether the current hit crits.
        weapon_monoco_mask_type: Monoco's current mask.
        verso_rank: Verso's current rank.

    Returns:
        A normalized weapon-state dictionary consumed by ``evaluate_weapon``.
    """

    return {
        "attack_type": resolved_attack_type,
        "shield_points": picto_shield_points,
        "unhit_turns": weapon_unhit_turns,
        "stain_consume_stacks": weapon_stain_consume_stacks,
        "light_stains": weapon_light_stains,
        "dark_stains": weapon_dark_stains,
        "self_burn_stacks": weapon_self_burn_stacks,
        "foretell": sciel_foretell,
        "twilight": sciel_twilight,
        "moon_charges": weapon_moon_charges,
        "cursed": weapon_cursed,
        "ap_consumed": weapon_ap_consumed,
        "critical_hit": weapon_critical_hit,
        "monoco_mask_type": weapon_monoco_mask_type,
        "rank": verso_rank,
    }


@callback(
    Output("exp33-calculator-save-import-store", "data"),
    Output("exp33-calculator-save-import-status", "children"),
    Output("exp33-calculator-save-import-status", "color"),
    Output("exp33-calculator-save-import-status", "is_open"),
    Output("exp33-calculator-character", "value"),
    Input("exp33-calculator-save-upload", "contents"),
    State("exp33-calculator-save-upload", "filename"),
    State("exp33-calculator-character", "value"),
    prevent_initial_call=True,
)
def import_save_file(
    contents: str | None,
    filename: str | None,
    current_character: str | None,
) -> tuple[dict[str, Any] | None, str | Any, str | Any, bool | Any, str | Any]:
    """Parse an uploaded `.sav` file into calculator-ready state."""

    if not contents:
        return no_update, no_update, no_update, no_update, no_update

    try:
        payload = parse_uploaded_save(contents, filename)
    except SaveImportError as exc:
        return None, str(exc), "danger", True, no_update
    except Exception as exc:
        logger.exception("Unexpected failure while importing uploaded save: {}", exc)
        return None, "Uploaded save could not be imported.", "danger", True, no_update

    available_characters = [
        CHARACTER_META[character]["label"]
        for character in CALCULATOR_DATA
        if character in payload["characters"]
    ]
    preferred_character = (
        current_character
        if current_character in payload["characters"]
        else payload["preferred_character"]
    )
    message = (
        f"Imported {payload['filename']} for {', '.join(available_characters)}. "
        "Attack Power still needs manual input."
    )
    return payload, message, "info", True, preferred_character


@callback(
    Output("exp33-calculator-save-summary-card", "style"),
    Output("exp33-calculator-save-summary-body", "children"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-save-import-store", "data"),
)
def update_import_summary(
    character: str | None,
    save_import: dict[str, Any] | None,
) -> tuple[StyleRule, ComponentChildren]:
    """Show the imported build summary for the active character."""

    selected_character = character or DEFAULT_CHARACTER
    build = imported_build(save_import, selected_character)
    if not build:
        return HIDDEN_STYLE, []

    filename = (
        str(save_import.get("filename") or "uploaded.sav")
        if isinstance(save_import, dict)
        else "uploaded.sav"
    )
    return VISIBLE_STYLE, build_import_summary(build, filename)


@callback(
    Output("exp33-calculator-skill", "options"),
    Output("exp33-calculator-skill", "value"),
    Output("exp33-calculator-compare-skill", "options"),
    Output("exp33-calculator-compare-skill", "value"),
    Output("exp33-calculator-attack", "value"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-save-import-store", "data"),
)
def update_skill_dropdown(
    character: str | None,
    save_import: dict[str, Any] | None,
) -> SkillDropdownUpdate:
    """Refresh the skill dropdown and default attack when the character changes.

    Args:
        character: The selected calculator character id.
        save_import: Optional imported build data from an uploaded save.

    Returns:
        A tuple of ``(primary_options, primary_skill, compare_options,
        compare_skill, default_attack)`` for the newly selected character.
        The compare skill resets to ``None`` so stale selections do not carry
        across characters.
    """

    selected_character = character or DEFAULT_CHARACTER
    options = skill_options_for(selected_character)
    default_skill = DEFAULT_SKILLS.get(selected_character, options[0]["value"])
    compare_skill = None
    if default_skill not in {option["value"] for option in options}:
        default_skill = options[0]["value"]
    attack = CALCULATOR_DATA[selected_character]["default_attack"]
    build = imported_build(save_import, selected_character)
    if build:
        option_values = {option["value"] for option in options}
        matched_skills = [
            skill
            for skill in build.get("equipped_skills", [])
            if skill in option_values
        ]
        if matched_skills:
            default_skill = matched_skills[0]
        if len(matched_skills) > 1:
            compare_skill = next(
                (skill for skill in matched_skills[1:] if skill != default_skill),
                None,
            )
    return options, default_skill, options, compare_skill, attack


@callback(
    Output("exp33-calculator-weapon", "data"),
    Output("exp33-calculator-weapon", "value"),
    Output("exp33-calculator-weapon-level", "value"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-save-import-store", "data"),
)
def update_weapon_dropdown(
    character: str | None,
    save_import: dict[str, Any] | None,
) -> tuple[list[SkillOption], str | None, str]:
    """Refresh the weapon dropdown when the character changes.

    Args:
        character: The selected calculator character id.
        save_import: Optional imported build data from an uploaded save.

    Returns:
        A tuple of ``(options, selected_weapon, selected_level)`` for the
        active character.
    """

    selected_character = character or DEFAULT_CHARACTER
    options = weapon_options_for(selected_character)
    build = imported_build(save_import, selected_character)
    if not build:
        return options, None, "20"

    option_values = {option["value"] for option in options}
    selected_weapon = build.get("equipped_weapon")
    if selected_weapon not in option_values:
        return options, None, "20"

    selected_level = str(build.get("weapon_level") or "20")
    return options, selected_weapon, selected_level


@callback(
    Output("exp33-calculator-pictos", "value"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-save-import-store", "data"),
)
def update_imported_pictos(
    character: str | None,
    save_import: dict[str, Any] | None,
) -> list[str]:
    """Prefill equipped lumina from the imported save when available."""

    selected_character = character or DEFAULT_CHARACTER
    build = imported_build(save_import, selected_character)
    if not build:
        return []
    return [str(name) for name in build.get("equipped_pictos", [])]


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
    Output("exp33-calculator-control-lune-earth-stains", "style"),
    Output("exp33-calculator-control-lune-fire-stains", "style"),
    Output("exp33-calculator-control-lune-ice-stains", "style"),
    Output("exp33-calculator-control-lune-lightning-stains", "style"),
    Output("exp33-calculator-control-lune-light-stains", "style"),
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
    Output("exp33-calculator-control-verso-missing-health", "style"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-skill", "value"),
    Input("exp33-calculator-compare-skill", "value"),
    Input("exp33-calculator-weapon", "value"),
    Input("exp33-calculator-weapon-level", "value"),
)
def sync_visible_controls(
    character: str | None,
    skill: str | None,
    compare_skill: str | None,
    weapon: str | None,
    weapon_level: str | None,
) -> VisibleControlsUpdate:
    """Show only the setup controls relevant to the selected skills.

    Args:
        character: The selected calculator character id.
        skill: The currently selected skill name.
        compare_skill: The optional secondary skill used for comparison.
        weapon: The currently selected weapon name, if any.
        weapon_level: The selected weapon unlock level.

    Returns:
        A Dash callback tuple containing the active accordion item plus the
        visibility styles for every character setup section and control wrapper.
        When a compare skill is active, controls required by either selected
        skill stay visible.
    """

    active_character = character or DEFAULT_CHARACTER
    available_skills = {option["value"] for option in skill_options_for(active_character)}
    active_compare_skill = compare_skill if compare_skill in available_skills else None
    active_item, styles = build_character_section_styles(active_character)
    primary_row = get_row(active_character, skill)
    style_sets = [build_skill_control_styles(active_character, primary_row)]
    if active_compare_skill:
        compare_row = get_row(active_character, active_compare_skill)
        style_sets.append(build_skill_control_styles(active_character, compare_row))

    control_styles = merge_control_styles(*style_sets)
    for control in required_weapon_character_controls(active_character, weapon, weapon_level):
        control_styles[control] = VISIBLE_STYLE

    return (
        active_item,
        styles["gustave"],
        styles["lune"],
        styles["maelle"],
        styles["monoco"],
        styles["sciel"],
        styles["verso"],
        control_style(control_styles, "gustave_charges"),
        control_style(control_styles, "lune_stains"),
        control_style(control_styles, "lune_earth_stains"),
        control_style(control_styles, "lune_fire_stains"),
        control_style(control_styles, "lune_ice_stains"),
        control_style(control_styles, "lune_lightning_stains"),
        control_style(control_styles, "lune_light_stains"),
        control_style(control_styles, "lune_turns"),
        control_style(control_styles, "lune_all_crits"),
        control_style(control_styles, "maelle_stance"),
        control_style(control_styles, "maelle_burn_stacks"),
        control_style(control_styles, "maelle_hits_taken"),
        control_style(control_styles, "maelle_marked"),
        control_style(control_styles, "maelle_all_crits"),
        control_style(control_styles, "monoco_turns"),
        control_style(control_styles, "monoco_mask"),
        control_style(control_styles, "monoco_stunned"),
        control_style(control_styles, "monoco_marked"),
        control_style(control_styles, "monoco_powerless"),
        control_style(control_styles, "monoco_burning"),
        control_style(control_styles, "monoco_low_life"),
        control_style(control_styles, "monoco_full_life"),
        control_style(control_styles, "monoco_all_crits"),
        empty_state_style(control_styles, "gustave"),
        empty_state_style(control_styles, "lune"),
        empty_state_style(control_styles, "maelle"),
        empty_state_style(control_styles, "monoco"),
        empty_state_style(control_styles, "sciel"),
        empty_state_style(control_styles, "verso"),
        control_style(control_styles, "sciel_foretell"),
        control_style(control_styles, "sciel_twilight"),
        control_style(control_styles, "sciel_full_life"),
        control_style(control_styles, "verso_rank"),
        control_style(control_styles, "verso_shots"),
        control_style(control_styles, "verso_uses"),
        control_style(control_styles, "verso_stunned"),
        control_style(control_styles, "verso_speed_bonus"),
        control_style(control_styles, "verso_missing_health"),
    )


@callback(
    Output("exp33-calculator-control-weapon-level", "style"),
    Output("exp33-calculator-pictos-collapse", "is_open"),
    Output("exp33-calculator-picto-control-attack-type", "style"),
    Output("exp33-calculator-picto-control-below-10-health", "style"),
    Output("exp33-calculator-picto-control-target-burning", "style"),
    Output("exp33-calculator-picto-control-target-stunned", "style"),
    Output("exp33-calculator-picto-control-exhausted", "style"),
    Output("exp33-calculator-picto-control-full-health", "style"),
    Output("exp33-calculator-picto-control-unhit", "style"),
    Output("exp33-calculator-picto-control-inverted", "style"),
    Output("exp33-calculator-picto-control-consume-ap", "style"),
    Output("exp33-calculator-picto-control-shield-points", "style"),
    Output("exp33-calculator-picto-control-fighting-alone", "style"),
    Output("exp33-calculator-picto-control-all-allies-alive", "style"),
    Output("exp33-calculator-picto-control-status-effects", "style"),
    Output("exp33-calculator-picto-control-dodge-stacks", "style"),
    Output("exp33-calculator-picto-control-parry-stacks", "style"),
    Output("exp33-calculator-picto-control-warming-up-stacks", "style"),
    Output("exp33-calculator-picto-control-first-hit", "style"),
    Output("exp33-calculator-weapon-control-unhit-turns", "style"),
    Output("exp33-calculator-weapon-control-stain-consume-stacks", "style"),
    Output("exp33-calculator-weapon-control-light-stains", "style"),
    Output("exp33-calculator-weapon-control-dark-stains", "style"),
    Output("exp33-calculator-weapon-control-self-burn-stacks", "style"),
    Output("exp33-calculator-weapon-control-moon-charges", "style"),
    Output("exp33-calculator-weapon-control-cursed", "style"),
    Output("exp33-calculator-weapon-control-ap-consumed", "style"),
    Output("exp33-calculator-weapon-control-critical-hit", "style"),
    Output("exp33-calculator-weapon-control-monoco-mask-type", "style"),
    Output("exp33-calculator-bonus-empty", "style"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-pictos", "value"),
    Input("exp33-calculator-weapon", "value"),
    Input("exp33-calculator-weapon-level", "value"),
)
def sync_visible_bonus_controls(
    character: str | None,
    pictos: list[str] | None,
    weapon: str | None,
    weapon_level: str | None,
) -> tuple[Any, ...]:
    """Show only the bonus-setup controls required by the current selection.

    Args:
        character: The selected calculator character id.
        pictos: The selected Picto names from the multi-select.
        weapon: The currently selected weapon name, if any.
        weapon_level: The selected weapon unlock level.

    Returns:
        A Dash callback tuple containing the collapse state and visibility
        styles for each Picto and weapon setup control.
    """

    selected_character = character or DEFAULT_CHARACTER
    required_controls = required_picto_controls(pictos) | required_weapon_controls(
        selected_character,
        weapon,
        normalize_weapon_level(weapon_level),
    )
    has_selection = bool(pictos) or bool(weapon)

    def style_for(control: str) -> StyleRule:
        """Return the visible style only for required Picto controls.

        Args:
            control: The logical Picto control name to inspect.

        Returns:
            The visible style when the control is required, otherwise the hidden
            style.
        """

        return VISIBLE_STYLE if control in required_controls else HIDDEN_STYLE

    return (
        VISIBLE_STYLE if weapon else HIDDEN_STYLE,
        has_selection,
        style_for("attack_type"),
        style_for("below_10_health"),
        style_for("target_burning"),
        style_for("target_stunned"),
        style_for("exhausted"),
        style_for("full_health"),
        style_for("unhit"),
        style_for("inverted"),
        style_for("consume_ap"),
        style_for("shield_points"),
        style_for("fighting_alone"),
        style_for("all_allies_alive"),
        style_for("status_effects"),
        style_for("dodge_stacks"),
        style_for("parry_stacks"),
        style_for("warming_up_stacks"),
        style_for("first_hit"),
        style_for("unhit_turns"),
        style_for("stain_consume_stacks"),
        style_for("light_stains"),
        style_for("dark_stains"),
        style_for("self_burn_stacks"),
        style_for("moon_charges"),
        style_for("cursed"),
        style_for("ap_consumed"),
        style_for("critical_hit"),
        style_for("monoco_mask_type"),
        VISIBLE_STYLE if has_selection and not required_controls else HIDDEN_STYLE,
    )


@callback(
    Output("exp33-calculator-compare-overview-card", "style"),
    Output("exp33-calculator-compare-overview-body", "children"),
    Output("exp33-calculator-primary-column", "lg"),
    Output("exp33-calculator-result-body", "children"),
    Output("exp33-calculator-summary-body", "children"),
    Output("exp33-calculator-compare-column", "style"),
    Output("exp33-calculator-compare-result-body", "children"),
    Output("exp33-calculator-compare-summary-body", "children"),
    Input("exp33-calculator-character", "value"),
    Input("exp33-calculator-skill", "value"),
    Input("exp33-calculator-compare-skill", "value"),
    Input("exp33-calculator-attack", "value"),
    Input("exp33-calculator-enemy-affinity", "value"),
    Input("exp33-calculator-weapon", "value"),
    Input("exp33-calculator-weapon-level", "value"),
    Input("exp33-calculator-pictos", "value"),
    Input("exp33-calculator-picto-attack-type", "value"),
    Input("exp33-calculator-picto-below-10-health", "checked"),
    Input("exp33-calculator-picto-target-burning", "checked"),
    Input("exp33-calculator-picto-target-stunned", "checked"),
    Input("exp33-calculator-picto-exhausted", "checked"),
    Input("exp33-calculator-picto-full-health", "checked"),
    Input("exp33-calculator-picto-unhit", "checked"),
    Input("exp33-calculator-picto-inverted", "checked"),
    Input("exp33-calculator-picto-consume-ap", "checked"),
    Input("exp33-calculator-picto-shield-points", "value"),
    Input("exp33-calculator-picto-fighting-alone", "checked"),
    Input("exp33-calculator-picto-all-allies-alive", "checked"),
    Input("exp33-calculator-picto-status-effects", "value"),
    Input("exp33-calculator-picto-dodge-stacks", "value"),
    Input("exp33-calculator-picto-parry-stacks", "value"),
    Input("exp33-calculator-picto-warming-up-stacks", "value"),
    Input("exp33-calculator-picto-first-hit", "checked"),
    Input("exp33-calculator-weapon-unhit-turns", "value"),
    Input("exp33-calculator-weapon-stain-consume-stacks", "value"),
    Input("exp33-calculator-weapon-light-stains", "value"),
    Input("exp33-calculator-weapon-dark-stains", "value"),
    Input("exp33-calculator-weapon-self-burn-stacks", "value"),
    Input("exp33-calculator-weapon-moon-charges", "value"),
    Input("exp33-calculator-weapon-cursed", "checked"),
    Input("exp33-calculator-weapon-ap-consumed", "value"),
    Input("exp33-calculator-weapon-critical-hit", "checked"),
    Input("exp33-calculator-weapon-monoco-mask-type", "value"),
    Input("exp33-calculator-gustave-charges", "value"),
    Input("exp33-calculator-lune-stains", "value"),
    Input("exp33-calculator-lune-earth-stains", "value"),
    Input("exp33-calculator-lune-fire-stains", "value"),
    Input("exp33-calculator-lune-ice-stains", "value"),
    Input("exp33-calculator-lune-lightning-stains", "value"),
    Input("exp33-calculator-lune-light-stains", "value"),
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
    Input("exp33-calculator-verso-missing-health", "value"),
)
def update_calculator_result(
    character: str | None,
    skill: str | None,
    compare_skill: str | None,
    attack: NumericInput,
    enemy_affinity: str | None,
    weapon: str | None,
    weapon_level: str | None,
    pictos: list[str] | None,
    picto_attack_type: str | None,
    picto_below_10_health: ToggleInput,
    picto_target_burning: ToggleInput,
    picto_target_stunned: ToggleInput,
    picto_exhausted: ToggleInput,
    picto_full_health: ToggleInput,
    picto_unhit: ToggleInput,
    picto_inverted: ToggleInput,
    picto_consume_ap: ToggleInput,
    picto_shield_points: NumericInput,
    picto_fighting_alone: ToggleInput,
    picto_all_allies_alive: ToggleInput,
    picto_status_effects: NumericInput,
    picto_dodge_stacks: NumericInput,
    picto_parry_stacks: NumericInput,
    picto_warming_up_stacks: NumericInput,
    picto_first_hit: ToggleInput,
    weapon_unhit_turns: NumericInput,
    weapon_stain_consume_stacks: NumericInput,
    weapon_light_stains: NumericInput,
    weapon_dark_stains: NumericInput,
    weapon_self_burn_stacks: NumericInput,
    weapon_moon_charges: NumericInput,
    weapon_cursed: ToggleInput,
    weapon_ap_consumed: NumericInput,
    weapon_critical_hit: ToggleInput,
    weapon_monoco_mask_type: str | None,
    gustave_charges: NumericInput,
    lune_stains: NumericInput,
    lune_earth_stains: NumericInput,
    lune_fire_stains: NumericInput,
    lune_ice_stains: NumericInput,
    lune_lightning_stains: NumericInput,
    lune_light_stains: NumericInput,
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
    verso_missing_health: NumericInput,
) -> CalculatorResultPanels:
    """Recalculate the selected skill and rebuild the calculator panels.

    Args:
        character: The selected calculator character id.
        skill: The currently selected skill name.
        compare_skill: The optional secondary skill used for side-by-side comparison.
        attack: The raw attack power input.
        enemy_affinity: The selected enemy elemental affinity modifier.
        weapon: The selected weapon name.
        weapon_level: The selected weapon unlock level.
        pictos: The selected Picto names.
        picto_attack_type: The optional Picto attack-type override.
        picto_below_10_health: Whether the user is below 10% health.
        picto_target_burning: Whether the target is burning.
        picto_target_stunned: Whether the target is stunned.
        picto_exhausted: Whether the user is exhausted.
        picto_full_health: Whether the user is at full health.
        picto_unhit: Whether the user has not been hit yet.
        picto_inverted: Whether the user is inverted.
        picto_consume_ap: Whether the hit consumes AP.
        picto_shield_points: The current shield-point count.
        picto_fighting_alone: Whether the active character is alone.
        picto_all_allies_alive: Whether all allies are alive.
        picto_status_effects: The number of status effects on self.
        picto_dodge_stacks: The current dodge stack count.
        picto_parry_stacks: The current parry stack count.
        picto_warming_up_stacks: The current Warming Up stack count.
        picto_first_hit: Whether the current hit is the first hit of battle.
        weapon_unhit_turns: Consecutive turns without taking damage.
        weapon_stain_consume_stacks: Lune's current stain-consume stack count.
        weapon_light_stains: The active Light Stain count.
        weapon_dark_stains: The active Dark Stain count.
        weapon_self_burn_stacks: Maelle's self Burn stack count.
        weapon_moon_charges: The active Moon charge count.
        weapon_cursed: Whether the character is Cursed.
        weapon_ap_consumed: The AP consumed by the current attack.
        weapon_critical_hit: Whether the current hit crits.
        weapon_monoco_mask_type: Monoco's current mask.
        gustave_charges: Gustave's Overcharge count.
        lune_stains: Lune's fallback active stain count.
        lune_earth_stains: Lune's active Earth Stain count.
        lune_fire_stains: Lune's active Fire Stain count.
        lune_ice_stains: Lune's active Ice Stain count.
        lune_lightning_stains: Lune's active Lightning Stain count.
        lune_light_stains: Lune's active Light Stain count.
        lune_turns: The number of turns elapsed for Lune.
        lune_all_crits: Whether all relevant Lune hits crit.
        maelle_stance: Maelle's current stance.
        maelle_burn_stacks: Burn stacks used by Maelle's skill logic.
        maelle_hits_taken: Hits Maelle took in the previous round.
        maelle_marked: Whether the target is marked for Maelle.
        maelle_all_crits: Whether all relevant Maelle hits crit.
        monoco_turns: Burn turns elapsed for Monoco.
        monoco_mask: Whether Monoco's mask bonus is active.
        monoco_stunned: Whether the target is stunned for Monoco.
        monoco_marked: Whether the target is marked for Monoco.
        monoco_powerless: Whether the target is powerless.
        monoco_burning: Whether the target is burning.
        monoco_low_life: Whether the target is at low life.
        monoco_full_life: Whether the target is at full life.
        monoco_all_crits: Whether all relevant Monoco hits crit.
        sciel_foretell: Sciel's applied foretell count.
        sciel_twilight: Whether Twilight is active for Sciel.
        sciel_full_life: Whether Sciel is at full life.
        verso_rank: Verso's current rank.
        verso_shots: The number of stored shots for Follow Up.
        verso_uses: The use count for repeat-use Verso skills.
        verso_stunned: Whether Verso's target is stunned.
        verso_speed_bonus: Whether Verso has the full speed bonus active.
        verso_missing_health: Verso's missing HP percentage for Berserk Slash.

    Returns:
        A tuple containing:
        ``(compare_overview_style, compare_overview_body, primary_width,
        primary_result_body, primary_summary_body, compare_column_style,
        compare_result_body, compare_summary_body)``.
        When no compare skill is selected, the compare overview and compare
        column outputs are hidden and their bodies are empty.
    """

    selected_character = character or DEFAULT_CHARACTER
    available_skills = {option["value"] for option in skill_options_for(selected_character)}
    active_compare_skill = compare_skill if compare_skill in available_skills else None
    attack_value = parse_number(attack) or CALCULATOR_DATA[selected_character]["default_attack"]
    normalized_enemy_affinity = normalize_affinity(enemy_affinity)

    states = build_calculator_states(
        gustave_charges,
        lune_stains,
        lune_earth_stains,
        lune_fire_stains,
        lune_ice_stains,
        lune_lightning_stains,
        lune_light_stains,
        lune_turns,
        lune_all_crits,
        maelle_stance,
        maelle_burn_stacks,
        maelle_hits_taken,
        maelle_marked,
        maelle_all_crits,
        monoco_turns,
        monoco_mask,
        monoco_stunned,
        monoco_marked,
        monoco_powerless,
        monoco_burning,
        monoco_low_life,
        monoco_full_life,
        monoco_all_crits,
        sciel_foretell,
        sciel_twilight,
        sciel_full_life,
        verso_rank,
        verso_shots,
        verso_uses,
        verso_stunned,
        verso_speed_bonus,
        verso_missing_health,
    )

    def evaluate_skill_view(selected_skill: str | None) -> EvaluatedSkillView:
        """Evaluate one selected skill against the shared calculator state.

        Args:
            selected_skill: The skill to resolve for the active character.

        Returns:
            A fully evaluated payload containing the resolved row, affinity,
            summaries, result, current AP cost, and total multiplicative bonus.
        """

        row = get_row(selected_character, selected_skill)
        affinity = resolve_affinity(row, normalized_enemy_affinity)
        resolved_picto_attack_type = resolve_picto_attack_type(row, picto_attack_type)
        picto_state = build_picto_state(
            resolved_picto_attack_type,
            picto_below_10_health,
            picto_target_burning,
            picto_target_stunned,
            picto_exhausted,
            picto_full_health,
            picto_unhit,
            picto_inverted,
            picto_consume_ap,
            picto_shield_points,
            picto_fighting_alone,
            picto_all_allies_alive,
            picto_status_effects,
            picto_dodge_stacks,
            picto_parry_stacks,
            picto_warming_up_stacks,
            picto_first_hit,
        )
        weapon_state = build_weapon_state(
            resolved_picto_attack_type,
            picto_shield_points,
            weapon_unhit_turns,
            weapon_stain_consume_stacks,
            weapon_light_stains,
            weapon_dark_stains,
            weapon_self_burn_stacks,
            sciel_foretell,
            sciel_twilight,
            weapon_moon_charges,
            weapon_cursed,
            weapon_ap_consumed,
            weapon_critical_hit,
            weapon_monoco_mask_type,
            verso_rank,
        )

        picto_summary = evaluate_pictos(pictos, picto_state)
        weapon_summary = evaluate_weapon(selected_character, weapon, weapon_level, row, weapon_state)
        skill_result = calculate_skill_result(
            selected_character,
            row,
            states[selected_character],
            weapon_summary["suppress_verso_rank_bonus"],
        )
        skill_result = apply_weapon_bonus(skill_result, weapon_summary)
        skill_result = apply_picto_bonus(skill_result, picto_summary)
        current_cost = calculate_current_cost(selected_character, row, states[selected_character])

        return {
            "row": row,
            "affinity": affinity,
            "picto_summary": picto_summary,
            "weapon_summary": weapon_summary,
            "skill_result": skill_result,
            "current_cost": current_cost,
            "total_bonus_factor": picto_summary["total_factor"] * weapon_summary["total_factor"],
        }

    primary_view = evaluate_skill_view(skill)
    primary_result_body = build_result_body(
        selected_character,
        primary_view["row"],
        attack_value,
        primary_view["current_cost"],
        primary_view["skill_result"],
        primary_view["picto_summary"],
        primary_view["weapon_summary"],
        primary_view["affinity"],
    )
    primary_summary_body = build_summary_body(
        primary_view["row"],
        attack_value,
        primary_view["total_bonus_factor"],
        primary_view["affinity"],
    )

    if not active_compare_skill:
        return (
            HIDDEN_STYLE,
            [],
            12,
            primary_result_body,
            primary_summary_body,
            HIDDEN_STYLE,
            [],
            [],
        )

    compare_view = evaluate_skill_view(active_compare_skill)
    compare_result_body = build_result_body(
        selected_character,
        compare_view["row"],
        attack_value,
        compare_view["current_cost"],
        compare_view["skill_result"],
        compare_view["picto_summary"],
        compare_view["weapon_summary"],
        compare_view["affinity"],
    )
    compare_summary_body = build_summary_body(
        compare_view["row"],
        attack_value,
        compare_view["total_bonus_factor"],
        compare_view["affinity"],
    )

    return (
        VISIBLE_STYLE,
        build_comparison_overview(
            primary_view["row"],
            attack_value,
            primary_view["current_cost"],
            primary_view["skill_result"],
            primary_view["affinity"],
            compare_view["row"],
            attack_value,
            compare_view["current_cost"],
            compare_view["skill_result"],
            compare_view["affinity"],
        ),
        6,
        primary_result_body,
        primary_summary_body,
        VISIBLE_STYLE,
        compare_result_body,
        compare_summary_body,
    )
