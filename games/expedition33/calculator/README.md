# Expedition 33 Skill Damage Calculator
_For those who come after._

I made this calculator to help myself and others understand the complex damage formulas in Expedition 33. 

None of this would be possible without the incredible work of [JohnnyDamajer, whose spreadsheet](https://docs.google.com/spreadsheets/d/1hU299Jof7Ygtg1JmbITeBxFXh5iHtOIBPB1gVCRil6o) provided the base skill data and [ErikLeb & Blueye95's work](https://docs.google.com/spreadsheets/d/1-d2ybbBy94JiVF6Mo_0-jmICTueH4oyN2q9_Va2gXbw) on the Pictos, weapon, and damage scaling data. I stand on the shoulders of giants.

Using their data, I built a custom calculator that models the various branching conditions, bonus layers, and interactions for each character’s skills. 

## What It Does

The calculator helps answer complex questions like:
- How much damage does Lune’s `Thunderfall` do with 3 light stains when I have `Empowering Dodge` Picto equipped, have successfully dodged 6 attacks, and the `Coralim` weapon rank 10 passive bonus unlocked?
- How much does Maelle’s `Combustion` benefit from `Offensive Stance' and how does that change when I have 7 burn stacks on the target?
- How much does Verso’s `Berserk Slash` benefit from rank vs missing health? Is it better to use it when my health is low or to get to S-rank for the stronger multiplier?

But it can also be used for simpler questions like:
- How much damage does Gustave’s `Overcharge` do at 4 charges?
- How much damage does Sciel’s `Firing Shadow` do with 10 Foretells?
- How much damage does Lune's `Lightning Dance` do when the enemy is weak to Lightning damage?

The UI lets the user choose:

- Character and skill
- Attack value
- Enemy affinity (`neutral`, `weak`, `resist`)
- Skill-specific setup values such as charges, stains, stance, Foretell, rank, or burn stacks
- Optional Pictos
- Optional weapon passives and unlock level

The result card shows the final damage estimate, the applied multiplier, the scenario that was matched, and any warnings for partially modeled skills. The summary card shows the raw spreadsheet breakpoints for the skill and what they become after the selected bonus layers are applied.

## Data Sources

### Skill data

The skill rows come from the CSV files in [assets/expedition33/clair_skill_damage](../../../assets/expedition33/clair_skill_damage):

- [gustave.csv](../../../assets/expedition33/clair_skill_damage/gustave.csv)
- [lune.csv](../../../assets/expedition33/clair_skill_damage/lune.csv)
- [maelle.csv](../../../assets/expedition33/clair_skill_damage/maelle.csv)
- [monoco.csv](../../../assets/expedition33/clair_skill_damage/monoco.csv)
- [sciel.csv](../../../assets/expedition33/clair_skill_damage/sciel.csv)
- [verso.csv](../../../assets/expedition33/clair_skill_damage/verso.csv)

Those files are credited to JohnnyDamajer’s spreadsheet in [skill_damage.py](../skill_damage.py). 

I did a little work to integrate some of the character skill damage scaling data from ErikLeb & Blueye95’s spreadsheet as well.

### Data cleaning

[helpers.py](../helpers.py) normalizes spreadsheet exports before they are displayed or consumed:

- Empty header names are replaced with stable `Extra N` names.
- Fully empty columns and rows are dropped.
- Known junk columns such as `Extra*`, `Test*`, `Base Attack`, `T2`, and `T3` are removed.

[core.py](./core.py) then loads the per-character CSVs into `CALCULATOR_DATA`, filters out empty and tier-list rows, and builds skill lookups by name.

### Default attack values

When the user does not provide an attack value, the calculator falls back to the first usable test/basic-attack column it finds in the loaded CSV row set:

- `Test Basic Attack Dmg`
- `Base Attack`
- `Test Basic Attack`

If none are present, it falls back to `1000`.

### Picto and weapon sources

Picto and weapon bonuses are not loaded from the CSV exports. They are modeled directly in code:

- [pictos.py](./pictos.py)
- [weapons.py](./weapons.py)

These files act as the current source of truth for bonus definitions, conditions, unlock levels, and multiplicative factors.

Pictos data provided by ErikLeb & Blueye95.

## Code Layout

- [core.py](./core.py): shared parsing, CSV loading, affinity handling, breakpoint extraction, and general helpers
- [logic.py](./logic.py): character-specific multiplier logic plus Picto/weapon bonus application
- [callbacks.py](./callbacks.py): Dash callback layer that gathers UI state and rebuilds the result panels
- [layout.py](./layout.py): calculator UI and result rendering
- [pictos.py](./pictos.py): Picto definitions and evaluation
- [weapons.py](./weapons.py): weapon passive definitions and evaluation

## Calculation Flow

The main calculation path lives in the large result callback in [callbacks.py](./callbacks.py).

The flow is:

1. Resolve the selected character and skill row with `get_row`.
2. Parse the attack input or use the character’s default attack from `CALCULATOR_DATA`.
3. Resolve the enemy affinity with `resolve_affinity`.
4. Normalize all raw UI inputs into character state, Picto state, and weapon state.
5. Evaluate selected Pictos with `evaluate_pictos`.
6. Evaluate the selected weapon with `evaluate_weapon`.
7. Compute the skill’s base or conditional multiplier with `calculate_skill_result`.
8. Apply weapon bonuses with `apply_weapon_bonus`.
9. Apply Picto bonuses with `apply_picto_bonus`.
10. Apply elemental affinity when building the displayed final multiplier and estimated damage.

The final estimated damage is:

```text
damage = attack * skill_multiplier * weapon_factor * picto_factor * affinity_factor
```

Not every skill uses every layer. Utility skills can intentionally return no direct damage multiplier.

## Character Logic

Each character has a dedicated calculator in [logic.py](./logic.py).

### Gustave

- Mostly uses the sheet’s base multiplier directly.
- `Overcharge` scales from `Damage Multi` with `+20%` per stored charge.

### Lune

Lune by far has the heaviest sheet-driven branching and is the trickiest to model. The calculator uses `Lune Mode` plus related columns such as `Condition 1`, `Dmg Con1`, `Dmg Max`, `All Crit Dmg`, `Required Stains`, and `Consume Stains`.

Handled cases include:

- skills that require stains before they deal damage
- skills that consume stains for stronger values
- all-crit variants
- burn tick totals
- turn-duration skills
- consume-all scaling
- some explicit special cases such as `Fire Rage` and `Storm Caller`

Light stains are treated as wildcard substitutes when checking elemental stain requirements.

### Maelle

Maelle’s logic combines sheet breakpoints with stance math:

- `Offensive` stance multiplies eligible damage by `1.5`
- `Virtuoso` stance multiplies eligible damage by `3.0`
- some skills derive scaling from burn stacks or hits taken
- marked-target and all-crit branches use `DmMax` when the condition is met

Burn-over-time rows are summed separately from stance-sensitive direct hits.

### Monoco

Monoco’s logic models:

- explicit mask breakpoints from the sheet
- target-state conditions such as stunned, marked, burning, powerless, full-life, and low-life
- burn-duration rows
- a fallback generic mask bonus when the sheet implies a mask type but does not provide a dedicated mask breakpoint

The generic fallback is `3x` for most masks and `5x` for `Almighty Mask`.

### Sciel

Sciel’s logic is driven by Foretell and Twilight:

- some skills scale per Foretell at skill-specific rates
- Twilight doubles effective Foretell for those formulas
- Twilight can also add an extra `1.5x` multiplier where the notes imply it
- specific sheet columns such as `ConDmg` and `TwilightDmg` are used when the spreadsheet provides breakpoint values directly

`Our Sacrifice` and `Firing Shadow` also have custom formulas.

### Verso

Verso’s logic combines rank, use count, shots, stun state, speed bonus, and missing health.

It supports:

- exact-rank conditional rows
- generic rank bonuses
- S-rank maximum branches
- custom formulas for skills like `Follow Up`, `Ascending Assault`, and `Berserk Slash`

Some weapons can suppress Verso’s normal rank bonus. That suppression is passed into `calculate_skill_result` from the weapon evaluation result.

## Affinity, Pictos, and Weapons

### Enemy affinity

[core.py](./core.py) applies affinity only to elemental skills. Non-elemental and physical skills ignore the affinity selector.

The supported factors are:

- `neutral`: `1.0x`
- `weak`: `1.5x`
- `resist`: `0.5x`

### Pictos

[pictos.py](./pictos.py) defines each supported Picto as:

- always active
- boolean-gated
- stack-based
- positive-numeric
- attack-type-specific

`evaluate_pictos` returns:

- a combined multiplicative factor
- a list of active Picto statuses
- a list of inactive Picto statuses with the reason they did not apply

### Weapons

[weapons.py](./weapons.py) works the same way for supported weapon passives.

Each effect can be:

- a fixed multiplier
- a stack-based multiplier
- a Verso-rank suppression effect

Weapon passives can also require:

- a minimum weapon unlock tier
- a matching attack type
- a matching row property such as `Lunar`
- boolean or numeric setup state
- a specific mask or Verso rank

## Summary Table vs Result Card

The calculator intentionally shows two views of the same skill:

- The result card shows the single scenario selected by the current setup.
- The summary table shows the spreadsheet breakpoints collected from the row through `build_sheet_rows`.

The summary table is useful when the current setup is only one of several possible branches for the same skill.

## Known Modeling Limits

Some rows are only partially modeled. When that happens, the calculator surfaces a warning in the result card instead of silently pretending the model is exact. 

That being said, I may have made a mistake in the logic somewhere so if something looks off, please let me know!

Current examples in the code include:

- Lune utility skills that do not deal direct damage
- Lune extra-turn or reactive effects that are not folded into direct damage
- Lune `Fire Rage` stacking ambiguity
- Scenarios where the sheet provides incomplete information and the code uses note-derived formulas instead

## Contact
If you have questions, find a bug, or want to suggest improvements, please reach out! The best way to contact me is via email at xxxxxxxxxx. Alternatively, submit a GitHub issue or open a pull request.

_Tomorrow comes._
