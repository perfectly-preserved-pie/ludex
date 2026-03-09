from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import html

from games.expedition33.calculator.core import HIDDEN_STYLE


def _hidden_control(component: Any, wrapper_id: str) -> html.Div:
    """Wrap a bonus control in its hidden-by-default container."""

    return html.Div(component, id=wrapper_id, style=HIDDEN_STYLE)


def _hidden_switch(control_id: str, wrapper_id: str, label: str) -> html.Div:
    return _hidden_control(dmc.Switch(id=control_id, label=label), wrapper_id)


def _hidden_number_input(
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
    return _hidden_control(dmc.NumberInput(**kwargs), wrapper_id)


def _hidden_select(
    control_id: str,
    wrapper_id: str,
    label: str,
    value: str,
    data: list[dict[str, str]] | list[str],
) -> html.Div:
    return _hidden_control(
        dmc.Select(
            id=control_id,
            label=label,
            value=value,
            data=data,
            clearable=False,
        ),
        wrapper_id,
    )


bonus_controls = dbc.Collapse(
    dbc.Card(
        [
            dbc.CardHeader("Bonus Setup"),
            dbc.CardBody(
                dmc.Stack(
                    [
                        _hidden_select(
                            "exp33-calculator-picto-attack-type",
                            "exp33-calculator-picto-control-attack-type",
                            "Attack type override",
                            "Auto",
                            [
                                {"label": "Auto detect", "value": "Auto"},
                                {"label": "Skill", "value": "Skill"},
                                {"label": "Base Attack", "value": "Base Attack"},
                                {"label": "Counterattack", "value": "Counterattack"},
                                {"label": "Free Aim", "value": "Free Aim"},
                                {"label": "Gradient Attack", "value": "Gradient Attack"},
                            ],
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-below-10-health",
                            "exp33-calculator-picto-control-below-10-health",
                            "Health below 10%",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-target-burning",
                            "exp33-calculator-picto-control-target-burning",
                            "Target is burning",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-target-stunned",
                            "exp33-calculator-picto-control-target-stunned",
                            "Target is stunned",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-exhausted",
                            "exp33-calculator-picto-control-exhausted",
                            "Character is Exhausted",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-full-health",
                            "exp33-calculator-picto-control-full-health",
                            "Character is at full Health",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-unhit",
                            "exp33-calculator-picto-control-unhit",
                            "No hit received yet",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-inverted",
                            "exp33-calculator-picto-control-inverted",
                            "Character is Inverted",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-consume-ap",
                            "exp33-calculator-picto-control-consume-ap",
                            "Powered Attack consumed 1 AP",
                        ),
                        _hidden_number_input(
                            "exp33-calculator-picto-shield-points",
                            "exp33-calculator-picto-control-shield-points",
                            "Shield Points",
                            0,
                            min=0,
                            step=1,
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-fighting-alone",
                            "exp33-calculator-picto-control-fighting-alone",
                            "Character is fighting alone",
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-all-allies-alive",
                            "exp33-calculator-picto-control-all-allies-alive",
                            "All allies are alive",
                        ),
                        _hidden_number_input(
                            "exp33-calculator-picto-status-effects",
                            "exp33-calculator-picto-control-status-effects",
                            "Status Effects on self",
                            0,
                            min=0,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-picto-dodge-stacks",
                            "exp33-calculator-picto-control-dodge-stacks",
                            "Empowering Dodge stacks",
                            0,
                            min=0,
                            max=10,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-picto-parry-stacks",
                            "exp33-calculator-picto-control-parry-stacks",
                            "Empowering Parry stacks",
                            0,
                            min=0,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-picto-warming-up-stacks",
                            "exp33-calculator-picto-control-warming-up-stacks",
                            "Warming Up stacks",
                            0,
                            min=0,
                            max=5,
                            step=1,
                        ),
                        _hidden_switch(
                            "exp33-calculator-picto-first-hit",
                            "exp33-calculator-picto-control-first-hit",
                            "This is the first hit",
                        ),
                        _hidden_number_input(
                            "exp33-calculator-weapon-unhit-turns",
                            "exp33-calculator-weapon-control-unhit-turns",
                            "No-hit stacks / turns",
                            0,
                            min=0,
                            max=5,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-weapon-stain-consume-stacks",
                            "exp33-calculator-weapon-control-stain-consume-stacks",
                            "Stain-consume stacks",
                            0,
                            min=0,
                            max=5,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-weapon-light-stains",
                            "exp33-calculator-weapon-control-light-stains",
                            "Active Light Stains",
                            0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-weapon-dark-stains",
                            "exp33-calculator-weapon-control-dark-stains",
                            "Active Dark Stains",
                            0,
                            min=0,
                            max=4,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-weapon-self-burn-stacks",
                            "exp33-calculator-weapon-control-self-burn-stacks",
                            "Self Burn stacks",
                            0,
                            min=0,
                            step=1,
                        ),
                        _hidden_number_input(
                            "exp33-calculator-weapon-moon-charges",
                            "exp33-calculator-weapon-control-moon-charges",
                            "Moon charges",
                            0,
                            min=0,
                            step=1,
                        ),
                        _hidden_switch(
                            "exp33-calculator-weapon-cursed",
                            "exp33-calculator-weapon-control-cursed",
                            "Character is Cursed",
                        ),
                        _hidden_number_input(
                            "exp33-calculator-weapon-ap-consumed",
                            "exp33-calculator-weapon-control-ap-consumed",
                            "AP consumed by attack",
                            0,
                            min=0,
                            step=1,
                        ),
                        _hidden_switch(
                            "exp33-calculator-weapon-critical-hit",
                            "exp33-calculator-weapon-control-critical-hit",
                            "Current hit crits",
                        ),
                        _hidden_select(
                            "exp33-calculator-weapon-monoco-mask-type",
                            "exp33-calculator-weapon-control-monoco-mask-type",
                            "Current Monoco mask",
                            "Balanced",
                            ["Balanced", "Agile", "Caster", "Heavy", "Almighty"],
                        ),
                        _hidden_control(
                            dmc.Text(
                                "Selected Pictos and weapon passives do not need extra setup.",
                                c="dimmed",
                                size="sm",
                            ),
                            "exp33-calculator-bonus-empty",
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
