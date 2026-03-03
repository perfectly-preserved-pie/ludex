from __future__ import annotations
from dash import dcc, html
from typing import Any
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from games.expedition33.calculator.core import (
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
    skill_options_for,
)
from games.expedition33.helpers import build_title_card, format_value
from games.expedition33.calculator.pictos import PICTO_OPTIONS, PictoSummary


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


def build_result_body(
    character: str,
    row: CalculatorRow,
    attack: float | None,
    current_cost: str,
    skill_result: CalculationResult,
    picto_summary: PictoSummary,
) -> ComponentChildren:
    """Build the main result card body for the selected state.

    Args:
        character: The calculator character id.
        row: The selected skill row.
        attack: The effective attack power used for damage estimation.
        current_cost: The AP cost string after state-based adjustments.
        skill_result: The calculated result for the selected skill state.
        picto_summary: The evaluated Picto summary for the selected state.

    Returns:
        The list of Dash children rendered inside the primary result card.
    """

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
            build_picto_section(picto_summary),
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


def build_summary_body(row: CalculatorRow, attack: float | None, picto_factor: float) -> ComponentChildren:
    """Build the spreadsheet breakpoint summary table.

    Args:
        row: The selected skill row.
        attack: The effective attack power used for the displayed damage values.
        picto_factor: The combined Picto multiplier applied to the summary rows.

    Returns:
        The list of Dash children rendered inside the summary card body.
    """

    rows = build_sheet_rows(row)
    header_attack = format_value(attack) if attack is not None else "-"

    table_rows = [
        html.Tr(
            [
                html.Td(entry["label"]),
                html.Td(format_multiplier(entry["value"])),
                html.Td(format_multiplier(round(entry["value"] * picto_factor, 2))),
                html.Td(format_value(calculate_damage(attack, entry["value"] * picto_factor))),
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
                            html.Th(f"Damage @ {header_attack} Attack Power"),
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

attack_input = dmc.NumberInput(
    id="exp33-calculator-attack",
    label="Attack Power",
    value=CALCULATOR_DATA[DEFAULT_CHARACTER]["default_attack"],
    min=1,
    step=1,
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

picto_controls = dbc.Collapse(
    dbc.Card(
        [
            dbc.CardHeader("Pictos Setup"),
            dbc.CardBody(
                dmc.Stack(
                    [
                        html.Div(
                            dmc.Select(
                                id="exp33-calculator-picto-attack-type",
                                label="Attack type",
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
                            dmc.Text(
                                "Selected Pictos do not need extra setup.",
                                c="dimmed",
                                size="sm",
                            ),
                            id="exp33-calculator-picto-empty",
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

title_card = build_title_card("Skill Damage Calculator")

layout = dbc.Container(
    [
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
                            "Pictos data courtesy of ",
                            html.A(
                                "ErikLeb and Blueye95",
                                href="https://docs.google.com/spreadsheets/d/1-d2ybbBy94JiVF6Mo_0-jmICTueH4oyN2q9_Va2gXbw/edit?gid=1062723312#gid=1062723312",
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
            "The result card shows the applied breakpoint or derived formula and estimates damage from your current Attack Power."
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
