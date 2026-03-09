from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html

from games.expedition33.calculator.core import CHARACTER_META, HIDDEN_STYLE


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


def _control_wrapper(component: Any, wrapper_id: str, *, hidden: bool = False) -> html.Div:
    kwargs = {"id": wrapper_id}
    if hidden:
        kwargs["style"] = HIDDEN_STYLE
    return html.Div(component, **kwargs)


def _number_input_control(
    control_id: str,
    wrapper_id: str,
    label: str,
    value: int,
    *,
    min: int,
    step: int,
    max: int | None = None,
) -> html.Div:
    kwargs: dict[str, Any] = {
        "id": control_id,
        "label": label,
        "value": value,
        "min": min,
        "step": step,
    }
    if max is not None:
        kwargs["max"] = max
    return _control_wrapper(dmc.NumberInput(**kwargs), wrapper_id)


def _switch_control(control_id: str, wrapper_id: str, label: str) -> html.Div:
    return _control_wrapper(dmc.Switch(id=control_id, label=label), wrapper_id)


def _select_control(
    control_id: str,
    wrapper_id: str,
    label: str,
    value: str,
    data: list[str],
) -> html.Div:
    return _control_wrapper(
        dmc.Select(
            id=control_id,
            label=label,
            value=value,
            data=data,
            clearable=False,
        ),
        wrapper_id,
    )


def _character_item(
    character: str,
    title: str,
    controls: list[Any],
    *,
    hidden: bool = False,
) -> dbc.AccordionItem:
    item_kwargs = {
        "id": f"exp33-calculator-item-{character}",
        "item_id": f"setup-{character}",
        "title": title,
    }
    if hidden:
        item_kwargs["style"] = HIDDEN_STYLE
    return dbc.AccordionItem(
        dmc.Stack([*controls, build_empty_control_notice(character)], gap="sm"),
        **item_kwargs,
    )


calculator_controls = dbc.Accordion(
    [
        _character_item(
            "gustave",
            "Gustave Controls",
            [
                _number_input_control(
                    "exp33-calculator-gustave-charges",
                    "exp33-calculator-control-gustave-charges",
                    "Charges",
                    0,
                    min=0,
                    max=10,
                    step=1,
                )
            ],
            hidden=True,
        ),
        _character_item(
            "lune",
            "Lune Controls",
            [
                _number_input_control(
                    "exp33-calculator-lune-stains",
                    "exp33-calculator-control-lune-stains",
                    "Total stains",
                    0,
                    min=0,
                    max=4,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-lune-earth-stains",
                    "exp33-calculator-control-lune-earth-stains",
                    "Earth stains",
                    0,
                    min=0,
                    max=4,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-lune-fire-stains",
                    "exp33-calculator-control-lune-fire-stains",
                    "Fire stains",
                    0,
                    min=0,
                    max=4,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-lune-ice-stains",
                    "exp33-calculator-control-lune-ice-stains",
                    "Ice stains",
                    0,
                    min=0,
                    max=4,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-lune-lightning-stains",
                    "exp33-calculator-control-lune-lightning-stains",
                    "Lightning stains",
                    0,
                    min=0,
                    max=4,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-lune-light-stains",
                    "exp33-calculator-control-lune-light-stains",
                    "Light stains",
                    0,
                    min=0,
                    max=4,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-lune-turns",
                    "exp33-calculator-control-lune-turns",
                    "Turns / procs / burn ticks",
                    1,
                    min=1,
                    max=5,
                    step=1,
                ),
                _switch_control(
                    "exp33-calculator-lune-all-crits",
                    "exp33-calculator-control-lune-all-crits",
                    "All hits crit",
                ),
            ],
        ),
        _character_item(
            "maelle",
            "Maelle Controls",
            [
                _select_control(
                    "exp33-calculator-maelle-stance",
                    "exp33-calculator-control-maelle-stance",
                    "Current stance",
                    "Offensive",
                    ["Offensive", "Defensive", "Virtuoso", "Stanceless"],
                ),
                _number_input_control(
                    "exp33-calculator-maelle-burn-stacks",
                    "exp33-calculator-control-maelle-burn-stacks",
                    "Burn stacks",
                    0,
                    min=0,
                    max=100,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-maelle-hits-taken",
                    "exp33-calculator-control-maelle-hits-taken",
                    "Hits taken last round",
                    0,
                    min=0,
                    max=5,
                    step=1,
                ),
                _switch_control(
                    "exp33-calculator-maelle-marked",
                    "exp33-calculator-control-maelle-marked",
                    "Target is marked",
                ),
                _switch_control(
                    "exp33-calculator-maelle-all-crits",
                    "exp33-calculator-control-maelle-all-crits",
                    "All hits crit",
                ),
            ],
            hidden=True,
        ),
        _character_item(
            "monoco",
            "Monoco Controls",
            [
                _number_input_control(
                    "exp33-calculator-monoco-turns",
                    "exp33-calculator-control-monoco-turns",
                    "Burn / setup turns",
                    1,
                    min=1,
                    max=3,
                    step=1,
                ),
                _switch_control(
                    "exp33-calculator-monoco-mask",
                    "exp33-calculator-control-monoco-mask",
                    "Mask active",
                ),
                _switch_control(
                    "exp33-calculator-monoco-stunned",
                    "exp33-calculator-control-monoco-stunned",
                    "Target is stunned",
                ),
                _switch_control(
                    "exp33-calculator-monoco-marked",
                    "exp33-calculator-control-monoco-marked",
                    "Target is marked",
                ),
                _switch_control(
                    "exp33-calculator-monoco-powerless",
                    "exp33-calculator-control-monoco-powerless",
                    "Target is powerless",
                ),
                _switch_control(
                    "exp33-calculator-monoco-burning",
                    "exp33-calculator-control-monoco-burning",
                    "Target is burning",
                ),
                _switch_control(
                    "exp33-calculator-monoco-low-life",
                    "exp33-calculator-control-monoco-low-life",
                    "Monoco is low life",
                ),
                _switch_control(
                    "exp33-calculator-monoco-full-life",
                    "exp33-calculator-control-monoco-full-life",
                    "Monoco is full life",
                ),
                _switch_control(
                    "exp33-calculator-monoco-all-crits",
                    "exp33-calculator-control-monoco-all-crits",
                    "All hits crit",
                ),
            ],
            hidden=True,
        ),
        _character_item(
            "sciel",
            "Sciel Controls",
            [
                _number_input_control(
                    "exp33-calculator-sciel-foretell",
                    "exp33-calculator-control-sciel-foretell",
                    "Foretell",
                    0,
                    min=0,
                    step=1,
                ),
                _switch_control(
                    "exp33-calculator-sciel-twilight",
                    "exp33-calculator-control-sciel-twilight",
                    "Twilight active",
                ),
                _switch_control(
                    "exp33-calculator-sciel-full-life",
                    "exp33-calculator-control-sciel-full-life",
                    "Allies at full life",
                ),
            ],
            hidden=True,
        ),
        _character_item(
            "verso",
            "Verso Controls",
            [
                _select_control(
                    "exp33-calculator-verso-rank",
                    "exp33-calculator-control-verso-rank",
                    "Current rank",
                    "D",
                    ["D", "C", "B", "A", "S"],
                ),
                _number_input_control(
                    "exp33-calculator-verso-shots",
                    "exp33-calculator-control-verso-shots",
                    "Ranged shots this turn",
                    0,
                    min=0,
                    max=10,
                    step=1,
                ),
                _number_input_control(
                    "exp33-calculator-verso-uses",
                    "exp33-calculator-control-verso-uses",
                    "Uses / setup turns",
                    1,
                    min=1,
                    max=6,
                    step=1,
                ),
                _switch_control(
                    "exp33-calculator-verso-stunned",
                    "exp33-calculator-control-verso-stunned",
                    "Target is stunned",
                ),
                _switch_control(
                    "exp33-calculator-verso-speed-bonus",
                    "exp33-calculator-control-verso-speed-bonus",
                    "Max speed bonus active",
                ),
                _number_input_control(
                    "exp33-calculator-verso-missing-health",
                    "exp33-calculator-control-verso-missing-health",
                    "Missing HP %",
                    0,
                    min=0,
                    max=99,
                    step=1,
                ),
            ],
            hidden=True,
        ),
    ],
    id="exp33-calculator-character-accordion",
    active_item=["setup-lune"],
    always_open=True,
    start_collapsed=True,
    flush=True,
)
