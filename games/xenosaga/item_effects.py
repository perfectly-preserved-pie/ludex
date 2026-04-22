from __future__ import annotations

import re
from typing import Any


def _normalize_item_name(item_name: str) -> str:
    """Normalize item names so minor punctuation differences still match."""

    return re.sub(r"[^a-z0-9]+", " ", item_name.lower()).strip()


EPISODE1_ITEM_EFFECTS: dict[str, str] = {
    _normalize_item_name("Anti-Beam Armor"): "A.G.W.S. accessory: 25% reduction in beam damage",
    _normalize_item_name("Antidote"): "Clears physical status effects",
    _normalize_item_name("B-Max Circuit"): "A.G.W.S. accessory: enables boost use",
    _normalize_item_name("Boost Pack"): "Boost +1 at the start of battle",
    _normalize_item_name("Booster Pack"): "Boost +1",
    _normalize_item_name("Commander's Crest"): "AP +1 each turn",
    _normalize_item_name("Craft Apron"): "25% increase in skill points earned",
    _normalize_item_name("Cure-All"): "Clears all status effects",
    _normalize_item_name("Escape Pack"): "Escape from battle",
    _normalize_item_name("Ether Pack"): "Low EP recovery",
    _normalize_item_name("Ether Pack DX"): "High EP recovery",
    _normalize_item_name("Ether Pack S"): "Medium EP recovery",
    _normalize_item_name("Ether Upgrade A"): "10 ether points for one character",
    _normalize_item_name("Ether Upgrade S"): "50 ether points for one character",
    _normalize_item_name("Ether Upgrade Z"): "100 ether points for one character",
    _normalize_item_name("Fast Circuit 25"): "A.G.W.S. accessory: 25% increase in speed",
    _normalize_item_name("Fast Circuit 50"): "A.G.W.S. accessory: 50% increase in speed",
    _normalize_item_name("Frame Repair A"): "Restores 25% of an A.G.W.S. Frame's HP",
    _normalize_item_name("Frame Repair S"): "Restores a small amount of an A.G.W.S. Frame's HP",
    _normalize_item_name("Frame Repair Z"): "Restores 50% of an A.G.W.S. Frame's HP",
    _normalize_item_name("Gemini Clock"): "Status effects last 2x longer",
    _normalize_item_name("Hemlock"): "Reduces HP to 1",
    _normalize_item_name("Junked Circuit A"): "Sell-only barter item",
    _normalize_item_name("Junked Circuit B"): "Sell-only barter item",
    _normalize_item_name("Kobold Blade"): "Sell-only barter item",
    _normalize_item_name("Master's Pendant"): "25% increase in experience points earned",
    _normalize_item_name("Med Kit"): "Low HP recovery",
    _normalize_item_name("Med Kit DX"): "High HP recovery",
    _normalize_item_name("Med Kit S"): "Medium HP recovery",
    _normalize_item_name("Neuro Stim"): "Clears psychological status effects",
    _normalize_item_name("Penguin Rod"): (
        'Rod that can inflict "Slow" against biological and gnosis enemies'
    ),
    _normalize_item_name("Precious Stone"): "Sell-only barter item",
    _normalize_item_name("Purple Ring"): "Ether Attack +2",
    _normalize_item_name("Red Ring"): "Physical Attack +2",
    _normalize_item_name("Rejuvenator"): "Fully restores HP and EP",
    _normalize_item_name("Revenge Power"): 'Auto-boost when attacked; requires "Counter +10"',
    _normalize_item_name("Revive"): "Revives a character with low HP recovery",
    _normalize_item_name("Revive DX"): "Revives a character with full HP recovery",
    _normalize_item_name("SMG99AG"): "A.G.W.S. submachine gun for single-target attacks",
    _normalize_item_name("Samurai Heart"): "Increases counter rate by 10%",
    _normalize_item_name("Scrap Iron"): "Sell-only barter item",
    _normalize_item_name("Shield Armor"): "Guards against all status effects",
    _normalize_item_name("Silver Crown"): "Max EP +15%",
    _normalize_item_name("Skill Upgrade A"): "10 skill points for one character",
    _normalize_item_name("Skill Upgrade S"): "50 skill points for one character",
    _normalize_item_name("Skill Upgrade Z"): "100 skill points for one character",
    _normalize_item_name("Soul"): "Physical defense increases each time an ally is KO'd",
    _normalize_item_name("Spirit"): "Ether defense increases each time an ally is KO'd",
    _normalize_item_name("Swimsuit"): "25% increase in tech points earned",
    _normalize_item_name("Tech Upgrade A"): "10 tech points for one character",
    _normalize_item_name("Tech Upgrade S"): "50 tech points for one character",
    _normalize_item_name("Tech Upgrade Z"): "100 tech points for one character",
    _normalize_item_name("Unicorn Horn"): "Sell-only item",
    _normalize_item_name("Veil"): "25% decrease in ether effects",
}

EPISODE1_ITEM_ALIASES: dict[str, str] = {
    _normalize_item_name("B-MAX Circuit"): _normalize_item_name("B-Max Circuit"),
    _normalize_item_name("Cure All"): _normalize_item_name("Cure-All"),
    _normalize_item_name("Junk Circuit A"): _normalize_item_name("Junked Circuit A"),
}

EPISODE2_ITEM_EFFECTS: dict[str, str] = {
    _normalize_item_name("Anti-Beam Armor"): "Lower beam damage 25%",
    _normalize_item_name("Anti-Fire Armor"): "Lower fire damage 25%",
    _normalize_item_name("Anti-Ice Armor"): "Lower ice damage 25%",
    _normalize_item_name("Anti-Thunder Armor"): "Lower thunder damage 25%",
    _normalize_item_name("Antidote H"): "Heal H-type status effects",
    _normalize_item_name("Antidote L"): "Heal L-type status effects",
    _normalize_item_name("Auto Recover"): "Recover 50% HP when incapacitated (once)",
    _normalize_item_name("Auxiliary Armor A"): "ARM +30",
    _normalize_item_name("Auxiliary Armor B"): "ARM +40",
    _normalize_item_name("Awakening I"): "Gains Double Attack Silver Duel",
    _normalize_item_name("Awakening II"): "Gains Double Attack Gravity Bomb",
    _normalize_item_name("Awakening III"): "Gains Double Attack Phoenix Blade",
    _normalize_item_name("Awakening IV"): "Gains Blessed Miracle",
    _normalize_item_name("Bio Sphere"): "Recover all HP and EP (entire party)",
    _normalize_item_name("Charge Boost"): "Increase charge 25% by using the Stock command",
    _normalize_item_name("Charge Clean"): "Clear all status effects by using the Stock command",
    _normalize_item_name("Class Upgrade A"): "Class Points +10",
    _normalize_item_name("Class Upgrade B"): "Class Points +50",
    _normalize_item_name("EF Circuit A"): "EDEF +20",
    _normalize_item_name("EF Circuit B"): "EDEF +30",
    _normalize_item_name("EMAX300"): "Make maximum charge 300",
    _normalize_item_name("Ether Core"): "Sell-only item",
    _normalize_item_name("Ether Pack DX"): "Recovers all EP",
    _normalize_item_name("Ether Pack M"): "Restores 50% of Max EP",
    _normalize_item_name("Ether Pack S"): "Restores 25% of Max EP",
    _normalize_item_name("G Blind Guard"): "Blind resistance +25%",
    _normalize_item_name("G Boost Guard"): "Boost Lock resistance +25%",
    _normalize_item_name("G Energy Guard"): "Charge Down resistance +25%",
    _normalize_item_name("G Ether DD Guard"): "Ether DD resistance +25%",
    _normalize_item_name("G Heavy Guard"): "Heavy resistance +25%",
    _normalize_item_name("G Power Charge"): "Resistance to all status effects +25%",
    _normalize_item_name("G ST Double"): "Double duration of status effects",
    _normalize_item_name("G Stun Guard"): "Stun resistance +25%",
    _normalize_item_name("G Weak Guard"): "Weak resistance +25%",
    _normalize_item_name("Junked Circuit"): "Sell-only item",
    _normalize_item_name("Med Kit L"): "Restores 75% of Max HP",
    _normalize_item_name("Med Kit M"): "Restores 50% of Max HP",
    _normalize_item_name("Med Kit S"): "Restores 25% of Max HP",
    _normalize_item_name("Nano Repair A"): "Recover 25% of Max HP and EP (E.S. only)",
    _normalize_item_name("Rejuvenator M"): "Recovers 50% of Max HP and EP",
    _normalize_item_name("Revive DX"): "Revive and recover all HP",
    _normalize_item_name("Revive S"): "Revive and recover 25% of Max HP",
    _normalize_item_name("Scrap Iron"): "Sell-only item",
    _normalize_item_name("Skill Upgrade A"): "Skill Points +10",
    _normalize_item_name("Skill Upgrade B"): "Skill Points +30",
    _normalize_item_name("Skill Upgrade C"): "Skill Points +50",
    _normalize_item_name("Skill Upgrade D"): "Skill Points +100",
    _normalize_item_name("Skill Upgrade E"): "Skill Points +500",
    _normalize_item_name("Tuned Circuit"): "Agility +1",
}

EPISODE2_ITEM_ALIASES: dict[str, str] = {
    _normalize_item_name("Charge Boots"): _normalize_item_name("Charge Boost"),
    _normalize_item_name("Junked Circuits"): _normalize_item_name("Junked Circuit"),
}


def get_episode1_item_effect(item_name: Any) -> str | None:
    """Return a short XS1 item description for display, if one is known."""

    if item_name is None:
        return None

    raw_name = str(item_name).strip()
    if raw_name == "" or raw_name == "N/A":
        return None

    normalized_name = _normalize_item_name(raw_name)
    normalized_name = EPISODE1_ITEM_ALIASES.get(normalized_name, normalized_name)
    return EPISODE1_ITEM_EFFECTS.get(normalized_name)


def get_episode2_item_effect(item_name: Any) -> str | None:
    """Return a short XS2 item description for display, if one is known."""

    if item_name is None:
        return None

    raw_name = str(item_name).strip()
    if raw_name == "" or raw_name == "N/A":
        return None

    raw_name = re.sub(r"\s*\([^)]*%\)$", "", raw_name).strip()
    normalized_name = _normalize_item_name(raw_name)
    normalized_name = EPISODE2_ITEM_ALIASES.get(normalized_name, normalized_name)
    return EPISODE2_ITEM_EFFECTS.get(normalized_name)
