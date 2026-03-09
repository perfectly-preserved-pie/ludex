from __future__ import annotations

import math
from typing import Any

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html

from games.expedition33.calculator.core import (
    AffinityDetails,
    build_sheet_rows,
    calculate_damage,
    CalculationResult,
    CalculatorRow,
    CHARACTER_META,
    clean_text,
    compact,
    ComponentChildren,
    format_multiplier,
    parse_number,
    skill_element,
)
from games.expedition33.calculator.pictos import PictoSummary
from games.expedition33.calculator.weapons import WeaponSummary
from games.expedition33.helpers import format_value


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
    """Build the Picto summary section for the result card."""

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
    """Build the weapon summary section for the result card."""

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
    """Build the main result card body for the selected state."""

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
    """Build the spreadsheet breakpoint summary table."""

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
