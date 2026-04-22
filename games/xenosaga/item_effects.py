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

EPISODE3_ITEM_EFFECTS: dict[str, str] = {
    _normalize_item_name("AF-Stealth II"): "E.S. Asher armor: Max HP 47,610",
    _normalize_item_name("All Repair"): "Recover all HP for all E.S. allies",
    _normalize_item_name("Andvari"): "Small G gain boost, small rare-item boost",
    _normalize_item_name("Anti-Crystal"): "Cures Crystallize",
    _normalize_item_name("Antidote"): "Cures Poison",
    _normalize_item_name("Blue Star"): "EP +100",
    _normalize_item_name("C-US10"): "E.S. CPU: Max slots 10",
    _normalize_item_name("Cleanser"): "Cures most status effects except Crystallize",
    _normalize_item_name("Coral Stone"): "Null Rasp",
    _normalize_item_name("Crescent Moon"): "Small SP gain boost",
    _normalize_item_name("Crystal of Spite"): "Sell-only barter item",
    _normalize_item_name("D-Anima"): "E.S. disk: Increase Anima Gauge rate",
    _normalize_item_name("D-Counter"): "E.S. disk: Short Counter",
    _normalize_item_name("D-EN I"): "E.S. disk: EN +50",
    _normalize_item_name("D-EN III"): "E.S. disk: EN +200",
    _normalize_item_name("D-EXP II"): "E.S. disk: Large EXP gain boost",
    _normalize_item_name("D-Half Physical"): "E.S. disk: 1/2 Physical",
    _normalize_item_name("D-Nullify Evade"): "E.S. disk: Null E-Evade",
    _normalize_item_name("D-SP II"): "E.S. disk: Large SP gain boost",
    _normalize_item_name("D-Type M"): "E.S. disk: Type M Critical",
    _normalize_item_name("DEX Upgrade"): "Increase maximum Dexterity by 2",
    _normalize_item_name("DF-XX"): "E.S. Dinah armor: Max HP 41,260",
    _normalize_item_name("Decoder 6"): "Opens Segment Address Door 6",
    _normalize_item_name("Decoder 9"): "Opens Segment Address Door 9",
    _normalize_item_name("Decoder 11"): "Opens Segment Address Door 11",
    _normalize_item_name("Dog Tag"): "Break Limit +150",
    _normalize_item_name("Double Vestment"): "Strength +6, Evade +5",
    _normalize_item_name("Down Repair"): "Cures E.S. stat-down effects and F Mine",
    _normalize_item_name("EATK Upgrade"): "Increase maximum Ether Attack by 2",
    _normalize_item_name("EVA Upgrade"): "Increase maximum Evade by 2",
    _normalize_item_name("Ether Core"): "Sell-only barter item",
    _normalize_item_name("Ether Pack L"): "Recover all EP",
    _normalize_item_name("Ether Pack M"): "Recover medium amount of EP",
    _normalize_item_name("Ether Pack S"): "Recover small amount of EP",
    _normalize_item_name("Evangelist"): "Max Boost +3, large EXP gain boost, large SP gain boost",
    _normalize_item_name("General's Bracelet"): "1/2 Fire, 1/2 Ice, 1/2 Lightning",
    _normalize_item_name("God Circle"): "Null Misty",
    _normalize_item_name("God's Experience"): "Large EXP gain boost",
    _normalize_item_name("Grand Design"): "Null status effects",
    _normalize_item_name("Green Oasis"): "HP +300",
    _normalize_item_name("Gustav Ring"): "HP +1500",
    _normalize_item_name("Gustav Wrist"): "2x defense vs. biological, mechanical, and gnosis enemies",
    _normalize_item_name("HP Upgrade"): "Increase maximum HP by 25",
    _normalize_item_name("Half Repair"): "Recover medium HP for all E.S. allies",
    _normalize_item_name("I.D. Plate"): "Sell-only barter item",
    _normalize_item_name("Imperial"): "Null Lock",
    _normalize_item_name("Junked Circuit"): "Sell-only barter item",
    _normalize_item_name("KAP-VEL"): "Agility +10, Break Limit +100",
    _normalize_item_name("Kajic Neck"): "Recovery Ether+",
    _normalize_item_name("Kajic Ring"): "EP +300",
    _normalize_item_name("Kajic Wrist"): "2x defense vs. mechanical enemies, 1/2 Fire, 1/2 Guard",
    _normalize_item_name("Life Demon"): "HP Drain, EP +100, Break Limit +100",
    _normalize_item_name("Med Kit"): "Recover small amount of HP",
    _normalize_item_name("Med Kit DX"): "Recover all HP for all allies",
    _normalize_item_name("Med Kit L"): "Recover all HP",
    _normalize_item_name("Med Kit M"): "Recover medium amount of HP",
    _normalize_item_name("Med Kit S"): "Recover small amount of HP",
    _normalize_item_name("Nano Repair DX"): "Recover all HP for one E.S. ally",
    _normalize_item_name("Nano Repair M"): "Recover medium HP for one E.S. ally",
    _normalize_item_name("Nullifier"): "Removes an enemy's active status support",
    _normalize_item_name("Power Leech"): "HP Drain, Increase Counter, Increase Double",
    _normalize_item_name("RF-Acala"): "E.S. Reuben armor: Max HP 43,160",
    _normalize_item_name("Rank Badge"): "Sell-only barter item",
    _normalize_item_name("Rejuvenator DX"): "Recover all HP and EP for all allies",
    _normalize_item_name("Rejuvenator L"): "Recover all HP and EP",
    _normalize_item_name("Rejuvenator M"): "Recover medium amount of HP and EP",
    _normalize_item_name("Remover"): "Cures stat-down effects",
    _normalize_item_name("Research Uniform"): "Agility +30",
    _normalize_item_name("Revive M"): "Revive and recover medium amount of HP",
    _normalize_item_name("Shock Absorbant Shirt"): "Break Limit +60",
    _normalize_item_name("STR Upgrade"): "Increase maximum Strength by 2",
    _normalize_item_name("Salt Pillar"): "Sell-only barter item",
    _normalize_item_name("Scrap Iron"): "Sell-only barter item",
    _normalize_item_name("Sephirotic Cane"): "Sell-only barter item",
    _normalize_item_name("Skill Upgrade A"): "Increase skill points by 10",
    _normalize_item_name("Skill Upgrade B"): "Increase skill points by 50",
    _normalize_item_name("Skill Upgrade C"): "Increase skill points by 100",
    _normalize_item_name("Soul Collector"): "Null Curse",
    _normalize_item_name("Union Neck"): "Max Boost +1",
    _normalize_item_name("Union Ring"): "Null E-Guard and E-Evade",
    _normalize_item_name("Union Wrist"): "2x defense vs. gnosis enemies, 1/2 Ice, 1/2 Guard",
    _normalize_item_name("Unknown Bracelet"): "Null Accuracy/Evade Down",
    _normalize_item_name("Velvet Breath"): "2x defense vs. biological enemies, 1/2 Lightning, 1/2 Guard",
    _normalize_item_name("Velvet Pannier"): "Luck +10, Break Limit +80",
    _normalize_item_name("Venom Ring"): "Adds Poison, EP +50",
    _normalize_item_name("Weapon Development Area Key"): (
        "Permits access to the Omega Universitas simulation room"
    ),
    _normalize_item_name("White Fragment"): "Sell-only barter item",
    _normalize_item_name("White Shirt"): "Luck +60",
    _normalize_item_name("ZF-Rybeus"): "E.S. Zebulun armor: Max HP boost",
}

EPISODE3_ITEM_ALIASES: dict[str, str] = {
    _normalize_item_name("AF-Stealth III"): _normalize_item_name("AF-Stealth II"),
    _normalize_item_name("D-SPII"): _normalize_item_name("D-SP II"),
    _normalize_item_name("Decoder 06"): _normalize_item_name("Decoder 6"),
    _normalize_item_name("Decoder 09"): _normalize_item_name("Decoder 9"),
    _normalize_item_name("Gustav's Ring"): _normalize_item_name("Gustav Ring"),
    _normalize_item_name("I.D Plate"): _normalize_item_name("I.D. Plate"),
    _normalize_item_name("Junked Curcuit"): _normalize_item_name("Junked Circuit"),
    _normalize_item_name("Nano Repar DX"): _normalize_item_name("Nano Repair DX"),
    _normalize_item_name("Rivive M"): _normalize_item_name("Revive M"),
    _normalize_item_name("Sephiratic Cane"): _normalize_item_name("Sephirotic Cane"),
    _normalize_item_name("Seraphatic Cane"): _normalize_item_name("Sephirotic Cane"),
    _normalize_item_name("Soul Collecter"): _normalize_item_name("Soul Collector"),
    _normalize_item_name("S. Absorbent Shirt"): _normalize_item_name("Shock Absorbant Shirt"),
    _normalize_item_name("W.D.A Key"): _normalize_item_name("Weapon Development Area Key"),
    _normalize_item_name("White Fragmant"): _normalize_item_name("White Fragment"),
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


def get_episode3_item_effect(item_name: Any) -> str | None:
    """Return a short XS3 item description for display, if one is known."""

    if item_name is None:
        return None

    raw_name = str(item_name).strip()
    if raw_name == "" or raw_name == "N/A":
        return None

    normalized_name = _normalize_item_name(raw_name)
    normalized_name = EPISODE3_ITEM_ALIASES.get(normalized_name, normalized_name)
    return EPISODE3_ITEM_EFFECTS.get(normalized_name)
