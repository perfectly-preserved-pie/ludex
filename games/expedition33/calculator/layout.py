from __future__ import annotations
import math
from dash import dcc, html
from typing import Any
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from games.expedition33.calculator.core import (
    AffinityDetails,
    build_sheet_rows,
    calculate_damage,
    CalculationResult,
    CALCULATOR_DATA,
    CalculatorRow,
    CHARACTER_META,
    clean_text,
    compact,
    ComponentChildren,
    DEFAULT_CHARACTER,
    DEFAULT_SKILLS,
    format_multiplier,
    HIDDEN_STYLE,
    parse_number,
    skill_element,
    skill_options_for,
)
from games.expedition33.helpers import build_title_card, format_value
from games.expedition33.calculator.pictos import PICTO_OPTIONS, PictoSummary
from games.expedition33.calculator.weapons import WEAPON_LEVEL_OPTIONS, weapon_options_for, WeaponSummary


def build_badges(character: str, row: CalculatorRow, current_cost: str) -> ComponentChildren:
    """Build metadata badges shown above the result cards.

    Args:
        character: The calculator character id.
        row: The selected skill row.
        current_cost: The AP cost string after state-based adjustments.

    Returns:
        A list of Mantine badge components describing the selected skill.
    """

    difficulty = clean_text(row.get("Game Description")).title()
    difficulty_color = {
        "Low": "green",
        "Medium": "yellow",
        "High": "orange",
        "Very High": "red",
        "Extreme": "pink",
    }.get(difficulty, "gray")

    target_value = clean_text(row.get("Target"))
    aoe_value = clean_text(row.get("AOE")).upper()
    target_label = {
        "AoE": "AOE",
        "Single": "Single Target",
    }.get(target_value, target_value or ("AOE" if aoe_value == "TRUE" else "Single Target"))

    badges = [
        dmc.Badge(CHARACTER_META[character]["label"], color="blue", variant="light"),
        dmc.Badge(f"Cost: {current_cost} AP", color="gray", variant="outline"),
        dmc.Badge(target_label, color="teal", variant="outline"),
    ]

    if difficulty:
        badges.append(dmc.Badge(difficulty, color=difficulty_color, variant="light"))

    for key in ("Stance", "Mask", "Lunar"):
        value = clean_text(row.get(key))
        if value:
            badges.append(dmc.Badge(value, color="indigo", variant="outline"))

    return badges


def build_picto_section(picto_summary: PictoSummary) -> Any | None:
    """Build the Picto summary section for the result card.

    Args:
        picto_summary: The evaluated Picto summary for the selected state.

    Returns:
        A Dash component describing active and inactive Pictos, or ``None`` when
        no Pictos are selected.
    """

    if not picto_summary["active"] and not picto_summary["inactive"]:
        return None

    details: ComponentChildren = [dmc.Text("Pictos", fw=600)]

    if picto_summary["active"]:
        details.append(
            html.Div(
                [
                    html.Strong("Active: "),
                    html.Span("; ".join(f"{item['detail']}: {item['effect']}" for item in picto_summary["active"])),
                ]
            )
        )

    if picto_summary["inactive"]:
        details.append(
            html.Div(
                [
                    html.Strong("Inactive: "),
                    html.Span("; ".join(f"{item['detail']}: {item['effect']}" for item in picto_summary["inactive"])),
                ],
                style={"color": "var(--mantine-color-dimmed)"},
            )
        )

    return dmc.Paper(details, withBorder=True, p="md", radius="md")


def build_weapon_section(weapon_summary: WeaponSummary) -> Any | None:
    """Build the weapon summary section for the result card.

    Args:
        weapon_summary: The evaluated weapon summary for the selected state.

    Returns:
        A Dash component describing active and inactive weapon passives, or
        ``None`` when no supported weapon is selected.
    """

    if not weapon_summary["active"] and not weapon_summary["inactive"]:
        return None

    details: ComponentChildren = [dmc.Text("Weapon", fw=600)]

    if weapon_summary["active"]:
        details.append(
            html.Div(
                [
                    html.Strong("Active: "),
                    html.Span("; ".join(f"{item['detail']}: {item['effect']}" for item in weapon_summary["active"])),
                ]
            )
        )

    if weapon_summary["inactive"]:
        details.append(
            html.Div(
                [
                    html.Strong("Inactive: "),
                    html.Span("; ".join(f"{item['detail']}: {item['effect']}" for item in weapon_summary["inactive"])),
                ],
                style={"color": "var(--mantine-color-dimmed)"},
            )
        )

    return dmc.Paper(details, withBorder=True, p="md", radius="md")


def build_result_body(
    character: str,
    row: CalculatorRow,
    attack: float | None,
    current_cost: str,
    skill_result: CalculationResult,
    picto_summary: PictoSummary,
    weapon_summary: WeaponSummary,
    affinity: AffinityDetails,
) -> ComponentChildren:
    """Build the main result card body for the selected state.

    Args:
        character: The calculator character id.
        row: The selected skill row.
        attack: The effective attack power used for damage estimation.
        current_cost: The AP cost string after state-based adjustments.
        skill_result: The calculated result for the selected skill state.
        picto_summary: The evaluated Picto summary for the selected state.
        weapon_summary: The evaluated weapon summary for the selected state.

    Returns:
        The list of Dash children rendered inside the primary result card.
    """

    multiplier = skill_result.get("multiplier")
    effective_multiplier = None
    if isinstance(multiplier, (int, float)):
        effective_multiplier = round(multiplier * affinity["factor"], 2)
    damage = calculate_damage(attack, effective_multiplier)
    notes = clean_text(row.get("Notes"))
    element = skill_element(row) or "None"
    affinity_label = (
        {
            "neutral": "Neutral",
            "weak": "Weakness",
            "resist": "Resistance",
        }[affinity["affinity"]]
        if affinity["applies"]
        else "Not applicable"
    )

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
                                dmc.Text(
                                    f"Element: {element} | Affinity: {affinity_label}",
                                    size="sm",
                                    style={"color": "var(--mantine-color-dimmed)"},
                                ),
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
                                html.H2(format_multiplier(effective_multiplier), className="mb-0"),
                                dmc.Text(
                                    (
                                        f"Base {format_multiplier(multiplier)} x affinity {affinity['factor']:g}"
                                        if isinstance(multiplier, (int, float)) and affinity["applies"]
                                        else f"Base {format_multiplier(multiplier)}"
                                        if isinstance(multiplier, (int, float))
                                        else "No direct damage multiplier"
                                    ),
                                    size="sm",
                                    style={"color": "var(--mantine-color-dimmed)"},
                                ),
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
            build_picto_section(picto_summary),
            build_weapon_section(weapon_summary),
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


def build_summary_body(
    row: CalculatorRow,
    attack: float | None,
    bonus_factor: float,
    affinity: AffinityDetails,
) -> ComponentChildren:
    """Build the spreadsheet breakpoint summary table.

    Args:
        row: The selected skill row.
        attack: The effective attack power used for the displayed damage values.
        bonus_factor: The combined Picto and weapon multiplier applied to the
            summary rows.

    Returns:
        The list of Dash children rendered inside the summary card body.
    """

    rows = build_sheet_rows(row)
    header_attack = format_value(attack) if attack is not None else "-"
    element = skill_element(row) or "None"
    affinity_suffix = ""
    if affinity["applies"]:
        affinity_suffix = f" | {element} {affinity['affinity'].title()} ({affinity['factor']:g}x)"

    table_rows = [
        html.Tr(
            [
                html.Td(entry["label"]),
                html.Td(format_multiplier(entry["value"])),
                html.Td(format_multiplier(round(entry["value"] * bonus_factor * affinity["factor"], 2))),
                html.Td(format_value(calculate_damage(attack, entry["value"] * bonus_factor * affinity["factor"]))),
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
                            html.Th("Sheet Multiplier"),
                            html.Th("Effective Multiplier"),
                            html.Th(f"Damage @ {header_attack} Attack Power{affinity_suffix}"),
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


def build_compare_metric_tile(label: str, value: str, hint: str) -> html.Div:
    """Build a compact comparison metric tile."""

    return html.Div(
        [
            html.Div(label, className="skill-compare-metric-label"),
            html.Div(value, className="skill-compare-metric-value"),
            html.Div(hint, className="skill-compare-metric-hint"),
        ],
        className="skill-compare-metric-tile",
    )


def build_result_metrics(
    row: CalculatorRow,
    attack: float | None,
    current_cost: str,
    skill_result: CalculationResult,
    affinity: AffinityDetails,
) -> dict[str, Any]:
    """Derive high-level metrics used by the calculator comparison overview."""

    multiplier = skill_result.get("multiplier")
    effective_multiplier = None
    if isinstance(multiplier, (int, float)):
        effective_multiplier = round(multiplier * affinity["factor"], 2)

    damage = calculate_damage(attack, effective_multiplier)
    cost_value = parse_number(current_cost)
    damage_per_ap = None
    if damage is not None and cost_value not in (None, 0):
        damage_per_ap = round(damage / cost_value, 2)

    affinity_label = (
        {
            "neutral": "Neutral",
            "weak": "Weakness",
            "resist": "Resistance",
        }[affinity["affinity"]]
        if affinity["applies"]
        else "No affinity modifier"
    )

    return {
        "skill": clean_text(row.get("Skill")),
        "damage": damage,
        "effective_multiplier": effective_multiplier,
        "cost_label": current_cost or "-",
        "cost_value": cost_value,
        "damage_per_ap": damage_per_ap,
        "meta": " | ".join(
            part
            for part in (
                skill_element(row) or "None",
                affinity_label,
            )
            if part
        ),
        "scenario": clean_text(skill_result.get("scenario")),
        "source": clean_text(skill_result.get("source")),
    }


def build_compare_summary_card(slot_label: str, metrics: dict[str, Any], accent_class: str) -> dbc.Card:
    """Build one side of the calculator comparison overview."""

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(slot_label, className="skill-compare-slot-label"),
                html.H4(metrics["skill"], className="mb-1"),
                html.P(metrics["meta"], className="skill-compare-meta mb-3"),
                html.Div(
                    [
                        build_compare_metric_tile(
                            "Estimated Damage",
                            format_value(metrics["damage"]),
                            "Current setup and affinity applied",
                        ),
                        build_compare_metric_tile(
                            "Applied Multiplier",
                            format_multiplier(metrics["effective_multiplier"]),
                            "After Picto, weapon, and affinity effects",
                        ),
                        build_compare_metric_tile(
                            "AP Cost",
                            metrics["cost_label"],
                            "State-adjusted current cost",
                        ),
                        build_compare_metric_tile(
                            "Damage / AP",
                            format_value(metrics["damage_per_ap"]),
                            "Estimated efficiency per AP",
                        ),
                    ],
                    className="skill-compare-metrics",
                ),
                html.Div(
                    [
                        html.Div("Scenario", className="skill-compare-detail-label"),
                        html.Div(metrics["scenario"] or "Base value", className="skill-compare-detail-value"),
                        html.Div(
                            f"Source: {metrics['source']}" if metrics["source"] else "Source unavailable",
                            className="skill-compare-metric-hint",
                        ),
                    ],
                    className="skill-compare-detail-block",
                ),
            ]
        ),
        className=f"h-100 skill-compare-card {accent_class}",
    )


def build_compare_advantage_item(
    label: str,
    left_label: str,
    left_value: float | None,
    right_label: str,
    right_value: float | None,
    value_formatter,
    higher_is_better: bool = True,
) -> html.Div:
    """Describe which side leads for a single calculated metric."""

    if left_value is None or right_value is None:
        detail = "Not comparable"
    elif math.isclose(left_value, right_value):
        detail = "Tie"
    else:
        left_wins = left_value > right_value if higher_is_better else left_value < right_value
        winner = left_label if left_wins else right_label
        detail = f"{winner} by {value_formatter(abs(left_value - right_value))}"

    return html.Div(
        [
            html.Div(label, className="skill-compare-advantage-label"),
            html.Div(detail, className="skill-compare-advantage-value"),
        ],
        className="skill-compare-advantage-item",
    )


def build_comparison_overview(
    left_row: CalculatorRow,
    left_attack: float | None,
    left_cost: str,
    left_result: CalculationResult,
    left_affinity: AffinityDetails,
    right_row: CalculatorRow,
    right_attack: float | None,
    right_cost: str,
    right_result: CalculationResult,
    right_affinity: AffinityDetails,
) -> html.Div:
    """Build the calculator comparison overview shown above the result cards."""

    left_metrics = build_result_metrics(left_row, left_attack, left_cost, left_result, left_affinity)
    right_metrics = build_result_metrics(right_row, right_attack, right_cost, right_result, right_affinity)

    return html.Div(
        dbc.Row(
            [
                dbc.Col(
                    build_compare_summary_card("Skill A", left_metrics, "skill-compare-card-a"),
                    lg=4,
                    className="mb-3",
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div("Comparison", className="skill-compare-slot-label"),
                                html.H4("Same setup, side by side", className="mb-3"),
                                html.Div(
                                    [
                                        build_compare_advantage_item(
                                            "Estimated damage",
                                            left_metrics["skill"],
                                            left_metrics["damage"],
                                            right_metrics["skill"],
                                            right_metrics["damage"],
                                            format_value,
                                        ),
                                        build_compare_advantage_item(
                                            "Applied multiplier",
                                            left_metrics["skill"],
                                            left_metrics["effective_multiplier"],
                                            right_metrics["skill"],
                                            right_metrics["effective_multiplier"],
                                            format_multiplier,
                                        ),
                                        build_compare_advantage_item(
                                            "AP cost",
                                            left_metrics["skill"],
                                            left_metrics["cost_value"],
                                            right_metrics["skill"],
                                            right_metrics["cost_value"],
                                            format_value,
                                            higher_is_better=False,
                                        ),
                                        build_compare_advantage_item(
                                            "Damage / AP",
                                            left_metrics["skill"],
                                            left_metrics["damage_per_ap"],
                                            right_metrics["skill"],
                                            right_metrics["damage_per_ap"],
                                            format_value,
                                        ),
                                    ],
                                    className="skill-compare-advantage-list",
                                ),
                            ]
                        ),
                        className="h-100 skill-compare-card skill-compare-card-delta",
                    ),
                    lg=4,
                    className="mb-3",
                ),
                dbc.Col(
                    build_compare_summary_card("Skill B", right_metrics, "skill-compare-card-b"),
                    lg=4,
                    className="mb-3",
                ),
            ],
            className="g-3",
        )
    )


def build_empty_control_notice(character: str) -> html.Div:
    """Build the placeholder shown when a skill has no extra inputs.

    Args:
        character: The calculator character id.

    Returns:
        A hidden placeholder div that is revealed when no controls are needed
        for the selected skill.
    """

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
    allowDeselect=False,
)

skill_dropdown = dcc.Dropdown(
    id="exp33-calculator-skill",
    options=skill_options_for(DEFAULT_CHARACTER),
    value=DEFAULT_SKILLS[DEFAULT_CHARACTER],
    clearable=False,
)

compare_skill_dropdown = dcc.Dropdown(
    id="exp33-calculator-compare-skill",
    options=skill_options_for(DEFAULT_CHARACTER),
    value=None,
    clearable=True,
    placeholder="Optional second skill for comparison",
)

save_upload = dcc.Upload(
    id="exp33-calculator-save-upload",
    children=dmc.Button("Import .sav", variant="light"),
    accept=".sav,.SAV",
    multiple=False,
)

save_import_store = dcc.Store(id="exp33-calculator-save-import-store")

attack_input = dmc.NumberInput(
    id="exp33-calculator-attack",
    label="Attack Power",
    value=CALCULATOR_DATA[DEFAULT_CHARACTER]["default_attack"],
    min=1,
    step=1,
)

enemy_affinity_select = dmc.Select(
    id="exp33-calculator-enemy-affinity",
    label="Enemy affinity",
    value="neutral",
    data=[
        {"label": "Neutral", "value": "neutral"},
        {"label": "Weakness", "value": "weak"},
        {"label": "Resistance", "value": "resist"},
    ],
    clearable=False,
    allowDeselect=False,
    description="Only affects elemental skills. Weakness = 1.5x, Resistance = 0.5x.",
)

pictos_select = dmc.MultiSelect(
    id="exp33-calculator-pictos",
    label="Pictos/Lumina",
    data=PICTO_OPTIONS,
    value=[],
    searchable=True,
    clearable=True,
    placeholder="Select supported damage Pictos/Lumina",
    description="Only directly calculable damage Pictos/Lumina from the sheet are listed here.",
)

weapon_select = dmc.Select(
    id="exp33-calculator-weapon",
    label="Weapon",
    data=weapon_options_for(DEFAULT_CHARACTER),
    value=None,
    searchable=True,
    clearable=True,
    placeholder="Select a supported damage-modifying weapon",
    description="Only weapon passives with direct damage effects the calculator can model are listed here.",
)

weapon_level_select = html.Div(
    dmc.Select(
        id="exp33-calculator-weapon-level",
        label="Weapon level",
        value="20",
        data=WEAPON_LEVEL_OPTIONS,
        clearable=False,
    ),
    id="exp33-calculator-control-weapon-level",
    style=HIDDEN_STYLE,
)

picto_controls = dbc.Collapse(
    dbc.Card(
        [
            dbc.CardHeader("Bonus Setup"),
            dbc.CardBody(
                dmc.Stack(
                    [
                        html.Div(
                            dmc.Select(
                                id="exp33-calculator-picto-attack-type",
                                label="Attack type override",
                                value="Auto",
                                data=[
                                    {"label": "Auto detect", "value": "Auto"},
                                    {"label": "Skill", "value": "Skill"},
                                    {"label": "Base Attack", "value": "Base Attack"},
                                    {"label": "Counterattack", "value": "Counterattack"},
                                    {"label": "Free Aim", "value": "Free Aim"},
                                    {"label": "Gradient Attack", "value": "Gradient Attack"},
                                ],
                                clearable=False,
                            ),
                            id="exp33-calculator-picto-control-attack-type",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-below-10-health", label="Health below 10%"),
                            id="exp33-calculator-picto-control-below-10-health",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-target-burning", label="Target is burning"),
                            id="exp33-calculator-picto-control-target-burning",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-target-stunned", label="Target is stunned"),
                            id="exp33-calculator-picto-control-target-stunned",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-exhausted", label="Character is Exhausted"),
                            id="exp33-calculator-picto-control-exhausted",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-full-health", label="Character is at full Health"),
                            id="exp33-calculator-picto-control-full-health",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-unhit", label="No hit received yet"),
                            id="exp33-calculator-picto-control-unhit",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-inverted", label="Character is Inverted"),
                            id="exp33-calculator-picto-control-inverted",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-consume-ap", label="Powered Attack consumed 1 AP"),
                            id="exp33-calculator-picto-control-consume-ap",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-picto-shield-points",
                                label="Shield Points",
                                value=0,
                                min=0,
                                step=1,
                            ),
                            id="exp33-calculator-picto-control-shield-points",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-fighting-alone", label="Character is fighting alone"),
                            id="exp33-calculator-picto-control-fighting-alone",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-all-allies-alive", label="All allies are alive"),
                            id="exp33-calculator-picto-control-all-allies-alive",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-picto-status-effects",
                                label="Status Effects on self",
                                value=0,
                                min=0,
                                step=1,
                            ),
                            id="exp33-calculator-picto-control-status-effects",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-picto-dodge-stacks",
                                label="Empowering Dodge stacks",
                                value=0,
                                min=0,
                                max=10,
                                step=1,
                            ),
                            id="exp33-calculator-picto-control-dodge-stacks",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-picto-parry-stacks",
                                label="Empowering Parry stacks",
                                value=0,
                                min=0,
                                step=1,
                            ),
                            id="exp33-calculator-picto-control-parry-stacks",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-picto-warming-up-stacks",
                                label="Warming Up stacks",
                                value=0,
                                min=0,
                                max=5,
                                step=1,
                            ),
                            id="exp33-calculator-picto-control-warming-up-stacks",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-picto-first-hit", label="This is the first hit"),
                            id="exp33-calculator-picto-control-first-hit",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-weapon-unhit-turns",
                                label="No-hit stacks / turns",
                                value=0,
                                min=0,
                                max=5,
                                step=1,
                            ),
                            id="exp33-calculator-weapon-control-unhit-turns",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-weapon-stain-consume-stacks",
                                label="Stain-consume stacks",
                                value=0,
                                min=0,
                                max=5,
                                step=1,
                            ),
                            id="exp33-calculator-weapon-control-stain-consume-stacks",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-weapon-light-stains",
                                label="Active Light Stains",
                                value=0,
                                min=0,
                                max=4,
                                step=1,
                            ),
                            id="exp33-calculator-weapon-control-light-stains",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-weapon-dark-stains",
                                label="Active Dark Stains",
                                value=0,
                                min=0,
                                max=4,
                                step=1,
                            ),
                            id="exp33-calculator-weapon-control-dark-stains",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-weapon-self-burn-stacks",
                                label="Self Burn stacks",
                                value=0,
                                min=0,
                                step=1,
                            ),
                            id="exp33-calculator-weapon-control-self-burn-stacks",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-weapon-moon-charges",
                                label="Moon charges",
                                value=0,
                                min=0,
                                step=1,
                            ),
                            id="exp33-calculator-weapon-control-moon-charges",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-weapon-cursed", label="Character is Cursed"),
                            id="exp33-calculator-weapon-control-cursed",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.NumberInput(
                                id="exp33-calculator-weapon-ap-consumed",
                                label="AP consumed by attack",
                                value=0,
                                min=0,
                                step=1,
                            ),
                            id="exp33-calculator-weapon-control-ap-consumed",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Switch(id="exp33-calculator-weapon-critical-hit", label="Current hit crits"),
                            id="exp33-calculator-weapon-control-critical-hit",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Select(
                                id="exp33-calculator-weapon-monoco-mask-type",
                                label="Current Monoco mask",
                                value="Balanced",
                                data=["Balanced", "Agile", "Caster", "Heavy", "Almighty"],
                                clearable=False,
                            ),
                            id="exp33-calculator-weapon-control-monoco-mask-type",
                            style=HIDDEN_STYLE,
                        ),
                        html.Div(
                            dmc.Text(
                                "Selected Pictos and weapon passives do not need extra setup.",
                                c="dimmed",
                                size="sm",
                            ),
                            id="exp33-calculator-bonus-empty",
                            style=HIDDEN_STYLE,
                        ),
                    ],
                    gap="sm",
                )
            ),
        ],
        className="mt-3",
    ),
    id="exp33-calculator-pictos-collapse",
    is_open=False,
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
                            label="Total stains",
                            value=0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-stains",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-earth-stains",
                            label="Earth stains",
                            value=0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-earth-stains",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-fire-stains",
                            label="Fire stains",
                            value=0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-fire-stains",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-ice-stains",
                            label="Ice stains",
                            value=0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-ice-stains",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-lightning-stains",
                            label="Lightning stains",
                            value=0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-lightning-stains",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-light-stains",
                            label="Light stains",
                            value=0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        id="exp33-calculator-control-lune-light-stains",
                    ),
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-lune-turns",
                            label="Turns / procs / burn ticks",
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
                    html.Div(
                        dmc.NumberInput(
                            id="exp33-calculator-verso-missing-health",
                            label="Missing HP %",
                            value=0,
                            min=0,
                            max=99,
                            step=1,
                        ),
                        id="exp33-calculator-control-verso-missing-health",
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

title_card = build_title_card("Skill Damage Calculator")

layout = dbc.Container(
    [
        save_import_store,
        title_card,
        dbc.Alert(
            html.Div(
                [
                    html.Span(
                        [
                            "Skill data courtesy of ",
                            html.A(
                                "JohnnyDamajer",
                                href="https://docs.google.com/spreadsheets/d/1hU299Jof7Ygtg1JmbITeBxFXh5iHtOIBPB1gVCRil6o/",
                                target="_blank",
                                rel="noopener noreferrer",
                            ),
                        ]
                    ),
                    html.Span(
                        [
                            "Pictos, weapon, and damage scaling data courtesy of ",
                            html.A(
                                "ErikLeb and Blueye95",
                                href="https://docs.google.com/spreadsheets/d/1-d2ybbBy94JiVF6Mo_0-jmICTueH4oyN2q9_Va2gXbw/",
                                target="_blank",
                                rel="noopener noreferrer",
                            ),
                        ],
                        className="d-block mt-1",
                    ),
                ]
            ),
            color="info",
            className="mt-2",
        ),
        #dbc.Alert(
        #    html.Span(
        #        [
        #            "Spreadsheet damage values are used as reference points. When the notes clearly state the formula, the calculator fills in the values between them.",
        #        ]
        #    ),
        #    color="info",
        #    className="mt-2",
       # ),
        dcc.Markdown(
            "Choose a character, pick a skill, then adjust the relevant combat state. "
            "The result card shows the applied breakpoint or derived formula and estimates damage from your current Attack Power, weapon passives, and Pictos."
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
                                        html.Div(
                                            [
                                                dmc.Group(
                                                    [
                                                        save_upload,
                                                        dmc.Text(
                                                            "Import a Clair Obscur: Expedition 33 `.sav` to prefill character, weapon, skill, and lumina selections.",
                                                            c="dimmed",
                                                            size="sm",
                                                        ),
                                                    ],
                                                    gap="sm",
                                                    align="center",
                                                ),
                                                dbc.Alert(
                                                    [
                                                        html.P(
                                                            [
                                                                "Save filename pattern: ",
                                                                html.Code("EXPEDITION_0_<save date>.sav"),
                                                            ],
                                                            className="mb-1",
                                                        ),
                                                        html.P(
                                                            [
                                                                "Linux: ",
                                                                html.Code(
                                                                    "/steamuser/AppData/Local/Sandfall/Saved/SaveGames/<profile>/Backup/"
                                                                ),
                                                            ],
                                                            className="mb-1",
                                                        ),
                                                        html.P(
                                                            [
                                                                "Windows: ",
                                                                html.Code(
                                                                    "C:\\Users\\<Your User Name>\\AppData\\Local\\Sandfall\\Saved\\SaveGames\\<some number>"
                                                                ),
                                                            ],
                                                            className="mb-1",
                                                        ),
                                                        html.P(
                                                            [
                                                                "Game Pass: ",
                                                                html.Code(
                                                                    r"C:\Users\<Your User Name>\AppData\Local\Packages\KeplerInteractive.Expedition33_<some id>\SystemAppData\wgs\<numbered folders>"
                                                                ),
                                                            ],
                                                            className="mb-1",
                                                        ),
                                                        dmc.Text(
                                                            "If AppData is not visible in File Explorer, turn on hidden files.",
                                                            c="dimmed",
                                                            size="sm",
                                                        ),
                                                    ],
                                                    color="secondary",
                                                    className="mt-2 mb-0 py-2",
                                                ),
                                                dbc.Alert(
                                                    id="exp33-calculator-save-import-status",
                                                    is_open=False,
                                                    color="info",
                                                    className="mt-2 mb-0",
                                                ),
                                                dbc.Card(
                                                    [
                                                        dbc.CardHeader("Imported Build"),
                                                        dbc.CardBody(id="exp33-calculator-save-summary-body"),
                                                    ],
                                                    id="exp33-calculator-save-summary-card",
                                                    className="mt-2",
                                                    style=HIDDEN_STYLE,
                                                ),
                                            ]
                                        ),
                                        character_select,
                                        html.Div(
                                            [
                                                html.Label("Skill", className="form-label"),
                                                skill_dropdown,
                                            ]
                                        ),
                                        html.Div(
                                            [
                                                html.Label("Compare Against", className="form-label"),
                                                compare_skill_dropdown,
                                                html.Div(
                                                    "Uses the same character, setup, weapon, Pictos, and enemy affinity.",
                                                    className="form-text",
                                                ),
                                            ]
                                        ),
                                        attack_input,
                                        enemy_affinity_select,
                                        weapon_select,
                                        weapon_level_select,
                                        pictos_select,
                                        picto_controls,
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
                                dbc.CardHeader("Comparison"),
                                dbc.CardBody(id="exp33-calculator-compare-overview-body"),
                            ],
                            id="exp33-calculator-compare-overview-card",
                            className="mb-3 skill-compare-shell",
                            style=HIDDEN_STYLE,
                        ),
                        dbc.Row(
                            [
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
                                    id="exp33-calculator-primary-column",
                                    lg=12,
                                    className="mb-4",
                                ),
                                dbc.Col(
                                    [
                                        dbc.Card(
                                            [
                                                dbc.CardHeader("Compare Result"),
                                                dbc.CardBody(id="exp33-calculator-compare-result-body"),
                                            ],
                                            className="mb-3",
                                        ),
                                        dbc.Card(
                                            [
                                                dbc.CardHeader("Compare Sheet Summary"),
                                                dbc.CardBody(id="exp33-calculator-compare-summary-body"),
                                            ]
                                        ),
                                    ],
                                    id="exp33-calculator-compare-column",
                                    lg=6,
                                    className="mb-4",
                                    style=HIDDEN_STYLE,
                                ),
                            ],
                            className="g-4",
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
