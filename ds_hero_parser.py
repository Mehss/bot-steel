import json
import math
import re
import pandas as pd


_CHAR_ABBR = {
    "Might": "M", "Agility": "A", "Reason": "R",
    "Intuition": "I", "Presence": "P",
}
_ABBR_TO_FULL = {v: k for k, v in _CHAR_ABBR.items()}


def _sub_chars(text, characteristics):
    """
    - MARIP substitution (chains, standalone, arithmetic) only in the damage segment
      (everything up to and including the word 'damage').
    - [strong/average/weak] resolved across the whole string.
    - MARIP outside the damage segment (e.g. potency 'R < 0') is left as a letter.
    """
    def _val(abbr):
        return characteristics.get(_ABBR_TO_FULL.get(abbr, ""), 0)

    def _replace_chain(match):
        letters = re.findall(r'[MARIP]', match.group(0))
        return str(max(_val(l) for l in letters))

    def _eval_add(match):
        return str(int(match.group(1)) + int(match.group(2)))

    def _process_damage_segment(part):
        part = re.sub(r'\b[MARIP](?:(?:\s*,\s*|\s+)(?:or\s+)?[MARIP])+\b', _replace_chain, part)
        part = re.sub(r'\b([MARIP])\b', lambda m: str(_val(m.group(0))), part)
        part = re.sub(r'(-?\d+)\s*\+\s*(-?\d+)', _eval_add, part)
        return part

    # Apply substitution only to the segment up to (and including) 'damage'
    text = re.sub(
        r'^(.*?\b[Dd]amage\b)',
        lambda m: _process_damage_segment(m.group(1)),
        text, count=1, flags=re.DOTALL,
    )

    # Resolve potency tier brackets across the whole string
    strong = max(characteristics.values(), default=0)
    text = text.replace('[strong]', str(strong))
    text = text.replace('[average]', str(strong - 1))
    text = text.replace('[weak]', str(strong - 2))
    return text


def parse_ds_hero(data: bytes):
    """
    Parse a .ds-hero file (bytes) and return (name, actions_df, counters_df, data_df).
    """
    hero = json.loads(data)
    cls = hero.get("class", {})
    level = cls.get("level", 1)
    characteristics = {
        c["characteristic"]: c["value"]
        for c in cls.get("characteristics", [])
    }

    abilities = _collect_abilities(cls, level)
    melee_bonus, ranged_bonus = _collect_kit_bonuses(cls, level)
    ability_dmg_bonuses = _collect_ability_damage_bonuses(cls, level) + _collect_inventory_ability_damage_bonuses(hero, level)
    resource_name = _heroic_resource_name(cls, level)
    actions_df = _build_actions_df(abilities, characteristics, melee_bonus, ranged_bonus, ability_dmg_bonuses, resource_name)
    counters_df = _build_counters_df(hero, cls, level)
    data_df = _build_data_df(hero, cls, level, characteristics)
    name = hero.get("name", "Unknown")

    return name, actions_df, counters_df, data_df


# ---------------------------------------------------------------------------
# Ability collection
# ---------------------------------------------------------------------------

def _collect_abilities(cls, level):
    def _scan_source(source, ability_pool):
        abilities = []
        selected_ids = set()

        def _scan(features):
            for f in features:
                ftype = f.get("type")
                data = f.get("data") or {}
                if ftype == "Kit":
                    for kit in data.get("selected", []):
                        _scan(kit.get("features", []))
                elif ftype == "Ability":
                    abilities.append(data["ability"])
                elif ftype == "Multiple Features":
                    _scan(data.get("features", []))
                elif ftype == "Class Ability":
                    selected_ids.update(data.get("selectedIDs", []))
                elif ftype == "Choice":
                    for sel in data.get("selected", []):
                        if sel.get("type") == "Ability":
                            abilities.append(sel["data"]["ability"])
                        elif sel.get("type") == "Multiple Features":
                            _scan((sel.get("data") or {}).get("features", []))

        for level_data in source.get("featuresByLevel", []):
            if level_data["level"] > level:
                break
            _scan(level_data.get("features", []))

        pool = {a["id"]: a for a in ability_pool}
        abilities += [pool[aid] for aid in selected_ids if aid in pool]
        return abilities

    result = _scan_source(cls, cls.get("abilities", []))
    for sub in cls.get("subclasses", []):
        if sub.get("selected", False):
            result += _scan_source(sub, sub.get("abilities", []))
    return result


# ---------------------------------------------------------------------------
# Kit damage bonuses
# ---------------------------------------------------------------------------

def _collect_ability_damage_bonuses(cls, level):
    """
    Return list of {"keywords": [...], "value": N} dicts from all Ability Damage
    features up to level cap (class + selected subclasses).
    """
    bonuses = []

    def _scan(features):
        for f in features:
            ftype = f.get("type")
            data = f.get("data") or {}
            if ftype == "Ability Damage":
                bonuses.append({"keywords": data.get("keywords", []), "value": data.get("value", 0)})
            elif ftype == "Multiple Features":
                _scan(data.get("features", []))
            elif ftype == "Kit":
                for kit in data.get("selected", []):
                    _scan(kit.get("features", []))
            elif ftype == "Choice":
                for sel in data.get("selected", []):
                    sel_type = sel.get("type")
                    sel_data = sel.get("data") or {}
                    if sel_type == "Ability Damage":
                        bonuses.append({"keywords": sel_data.get("keywords", []), "value": sel_data.get("value", 0)})
                    elif sel_type == "Multiple Features":
                        _scan(sel_data.get("features", []))

    def _scan_source(source):
        for level_data in source.get("featuresByLevel", []):
            if level_data["level"] > level:
                break
            _scan(level_data.get("features", []))

    _scan_source(cls)
    for sub in cls.get("subclasses", []):
        if sub.get("selected", False):
            _scan_source(sub)

    return bonuses


def _collect_inventory_ability_damage_bonuses(hero, level):
    """
    Return ability damage bonus dicts from inventory items.
    - Imbued Weapon: +1 Weapon per imbuement tier present (level 1/5/9)
    - Imbued Implement: +1 Magic and +1 Psionic per imbuement tier present
    - Any imbuement.feature of type Ability Damage
    - Leveled Weapon / Leveled Implement / Leveled Item: Ability Damage features
      from featuresByLevel up to hero level
    """
    bonuses = []
    for item in hero.get("state", {}).get("inventory", []):
        itype = item.get("type", "")
        imbuement_levels = {imb["level"] for imb in item.get("imbuements", [])}

        if itype == "Imbued Weapon":
            for lvl in (1, 5, 9):
                if lvl in imbuement_levels:
                    bonuses.append({"keywords": ["Weapon"], "value": 1})

        elif itype == "Imbued Implement":
            for lvl in (1, 5, 9):
                if lvl in imbuement_levels:
                    bonuses.append({"keywords": ["Magic"], "value": 1})
                    bonuses.append({"keywords": ["Psionic"], "value": 1})

        # Explicit Ability Damage features on imbuements (e.g. Enchantment of Destruction)
        for imb in item.get("imbuements", []):
            feat = imb.get("feature") or {}
            if feat.get("type") == "Ability Damage":
                d = feat.get("data") or {}
                bonuses.append({"keywords": d.get("keywords", []), "value": d.get("value", 0)})

        # Leveled Weapon / Implement / Item: Ability Damage features in featuresByLevel
        if itype in ("Leveled Weapon", "Leveled Implement", "Leveled Item"):
            for lvl_entry in item.get("featuresByLevel", []):
                if lvl_entry["level"] > level:
                    break
                for feat in lvl_entry.get("features", []):
                    if feat.get("type") == "Ability Damage":
                        d = feat.get("data") or {}
                        bonuses.append({"keywords": d.get("keywords", []), "value": d.get("value", 0)})

    return bonuses


def _collect_kit_bonuses(cls, level):
    """
    Return (melee_per_kit, ranged_per_kit) as lists of (t1, t2, t3) tuples, one entry per kit.
    Kits with no bonus for that damage type are excluded.
    """
    melee = []
    ranged = []
    for level_data in cls.get("featuresByLevel", []):
        if level_data["level"] > level:
            break
        for feature in level_data.get("features", []):
            if feature["type"] != "Kit":
                continue
            for kit in feature["data"].get("selected", []):
                md = kit.get("meleeDamage")
                if md and any(md.get(f"tier{i}", 0) for i in (1, 2, 3)):
                    melee.append((md.get("tier1", 0), md.get("tier2", 0), md.get("tier3", 0)))
                rd = kit.get("rangedDamage")
                if rd and any(rd.get(f"tier{i}", 0) for i in (1, 2, 3)):
                    ranged.append((rd.get("tier1", 0), rd.get("tier2", 0), rd.get("tier3", 0)))
    return melee, ranged


def apply_tier_bonuses(tier_str, flat_bonus, kit_bonuses, tier_idx):
    """Apply flat and per-kit damage bonuses to a tier string at display time.

    kit_bonuses is a list of (t1, t2, t3) tuples, one per kit.
    '3 + M damage', flat=1, kits=[(2,2,2),(1,1,1)], idx=0 → '7/6 + M damage'
    """
    def _replace(match):
        base = int(match.group(1)) + flat_bonus
        vals = [b[tier_idx] for b in kit_bonuses if b[tier_idx]]
        if vals:
            return "/".join(str(base + v) for v in vals) + match.group(2)
        return str(base) + match.group(2)

    if not flat_bonus and not any(b[tier_idx] for b in kit_bonuses):
        return tier_str
    return re.sub(r'^(\d+)(.*?\bdamage\b)', _replace, tier_str, count=1)


# ---------------------------------------------------------------------------
# Actions DataFrame
# ---------------------------------------------------------------------------

def _format_distance(distances):
    parts = []
    for d in distances:
        dtype = d.get("type", "")
        value = d.get("value", 0)
        if dtype == "Self":
            parts.append("Self")
        elif dtype == "Special":
            parts.append(d.get("special", "Special"))
        elif value:
            parts.append(f"{dtype} {value}")
        else:
            parts.append(dtype)
    return " / ".join(parts)


def _ability_to_row(ability, characteristics, melee_bonus, ranged_bonus, ability_dmg_bonuses, resource_name):
    name = ability.get("name", "")
    description = ability.get("description", "")
    action_type = ability.get("type", {})
    usage = action_type.get("usage", "")
    trigger = action_type.get("trigger", "")

    cost_raw = ability.get("cost", 0)
    if cost_raw == "signature" or cost_raw == 0:
        cost = ""
    else:
        cost = f"{cost_raw} {resource_name}"

    range_str = _format_distance(ability.get("distance", []))
    target = ability.get("target", "")

    roll_section = None
    text_parts = []
    field_parts = []

    for section in ability.get("sections", []):
        stype = section.get("type")
        if stype == "roll":
            roll_section = section.get("roll", {})
        elif stype == "text":
            text = section.get("text", "").strip()
            if text:
                text_parts.append(text)
        elif stype == "field":
            n = section.get("name", "")
            v = section.get("value", "")
            eff = section.get("effect", "")
            field_parts.append(f"**{n}** ({v} {resource_name}): {eff}" if v and str(v) != "0" else f"**{n}**: {eff}")

    keywords = ability.get("keywords", [])
    is_weapon_strike = "Weapon" in keywords and "Strike" in keywords
    is_melee = "Melee" in keywords
    is_ranged = "Ranged" in keywords

    ability_keywords = set(keywords)
    flat_dmg_bonus = sum(
        b["value"] for b in ability_dmg_bonuses
        if all(kw in ability_keywords for kw in b["keywords"])
    )

    # Pick per-kit bonus list that applies to this ability
    if is_weapon_strike and (is_melee or is_ranged):
        if is_melee and is_ranged:
            kit_per_kit = melee_bonus if melee_bonus else ranged_bonus
        elif is_melee:
            kit_per_kit = melee_bonus
        else:
            kit_per_kit = ranged_bonus
    else:
        kit_per_kit = []

    is_roll = "TRUE" if roll_section else "FALSE"
    t1 = t2 = t3 = bonus = ""

    if roll_section:
        t1 = _sub_chars(roll_section.get("tier1", ""), characteristics)
        t2 = _sub_chars(roll_section.get("tier2", ""), characteristics)
        t3 = _sub_chars(roll_section.get("tier3", ""), characteristics)
        chars = roll_section.get("characteristic", [])
        char_val = max((characteristics.get(c, 0) for c in chars), default=0)
        b_num = roll_section.get("bonus", 0)
        bonus = str(char_val + b_num)

    effect = "\n".join(text_parts + field_parts)

    return {
        "Name": name,
        "Action": usage,
        "Cost": cost,
        "ShortDesc": description,
        "Effect": effect,
        "IsRoll": is_roll,
        "Bonus": bonus,
        "Image": "",
        "T1": t1,
        "T2": t2,
        "T3": t3,
        "Target": target,
        "Range": range_str,
        "Trigger": trigger,
        "FlatDmgBonus": flat_dmg_bonus,
        "KitDmgBonus": json.dumps(kit_per_kit),
    }


def _build_actions_df(abilities, characteristics, melee_bonus, ranged_bonus, ability_dmg_bonuses, resource_name):
    rows = [_ability_to_row(a, characteristics, melee_bonus, ranged_bonus, ability_dmg_bonuses, resource_name) for a in abilities]
    if not rows:
        return pd.DataFrame(columns=[
            "Name", "Action", "Cost", "ShortDesc", "Effect", "IsRoll",
            "Bonus", "Image", "T1", "T2", "T3", "Target", "Range", "Trigger",
            "FlatDmgBonus", "KitDmgBonus",
        ])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Counters DataFrame
# ;;a deducts the heroic resource using resources.iloc[3], so it must be at index 3.
# ---------------------------------------------------------------------------

def _heroic_resource_info(cls, level):
    """Return (name, description) for the heroic resource from the ds-hero JSON."""
    for level_data in cls.get("featuresByLevel", []):
        if level_data["level"] > level:
            break
        for feature in level_data.get("features", []):
            if feature.get("type") == "Heroic Resource":
                name = feature.get("name", "Focus")
                gains = feature.get("data", {}).get("gains", [])
                if gains:
                    lines = ["Resource Gains:"]
                    for g in gains:
                        lines.append(f"• {g['value']}: {g['trigger']}")
                    desc = "\n".join(lines)
                else:
                    desc = ""
                return name, desc
    return "Focus", ""


def _heroic_resource_name(cls, level):
    return _heroic_resource_info(cls, level)[0]

def _echelon(level):
    return math.ceil(level / 3)


def _bonus_value(d, level):
    echelon = _echelon(level)
    return (
        d.get("value", 0)
        + d.get("valuePerLevel", 0) * (level - 1)
        + d.get("valuePerEchelon", 0) * echelon
    )


def _scan_bonus_field(features, field, level, kit_field=None):
    """
    Recursively sum Bonus features matching `field` across
    Bonus / Kit / Multiple Features / Choice nodes.
    `kit_field` is an optional direct kit attribute to sum (e.g. "stamina").
    """
    total = 0
    for f in features:
        ftype = f.get("type")
        data = f.get("data") or {}
        if ftype == "Bonus" and data.get("field") == field:
            total += _bonus_value(data, level)
        elif ftype == "Kit":
            for kit in data.get("selected", []):
                if kit_field:
                    total += kit.get(kit_field, 0)
                total += _scan_bonus_field(kit.get("features", []), field, level, kit_field)
        elif ftype == "Multiple Features":
            total += _scan_bonus_field(data.get("features", []), field, level, kit_field)
        elif ftype == "Choice":
            for sel in data.get("selected", []):
                sdata = sel.get("data") or {}
                if sel.get("type") == "Bonus" and sdata.get("field") == field:
                    total += _bonus_value(sdata, level)
                elif sel.get("type") == "Multiple Features":
                    total += _scan_bonus_field(sdata.get("features", []), field, level, kit_field)
    return total


def _compute_stamina(hero, cls, level, items):
    stamina = 0

    for level_data in cls.get("featuresByLevel", []):
        if level_data["level"] > level:
            break
        stamina += _scan_bonus_field(level_data.get("features", []), "Stamina", level, kit_field="stamina")

    stamina += _scan_bonus_field(hero.get("ancestry", {}).get("features", []), "Stamina", level)

    for item in items:
        for lvl in item.get("featuresByLevel", []):
            if lvl["level"] > level:
                break
            stamina += _scan_bonus_field(lvl.get("features", []), "Stamina", level)
        if item.get("type") == "Imbued Armor":
            imbuement_levels = {imb["level"] for imb in item.get("imbuements", [])}
            if 1 in imbuement_levels:
                stamina += 6
            if 5 in imbuement_levels:
                stamina += 6
            if 9 in imbuement_levels:
                stamina += 9

    return stamina


def _compute_recoveries(hero, cls, level):
    total = _scan_bonus_field(
        [f for lvl in cls.get("featuresByLevel", []) if lvl["level"] <= level
         for f in lvl.get("features", [])],
        "Recoveries", level,
    )
    total += _scan_bonus_field(hero.get("ancestry", {}).get("features", []), "Recoveries", level)
    return total or 10


def _collect_skills(hero, cls, level):
    """Return list of skill names from class, career, ancestry, and culture."""
    skills = []

    def _process_skill_choice(data):
        for skill in data.get("selected", []):
            if skill:
                skills.append(skill)

    def _scan(features):
        for f in features:
            ftype = f.get("type")
            data = f.get("data") or {}
            if ftype == "Skill Choice":
                _process_skill_choice(data)
            elif ftype == "Kit":
                for kit in data.get("selected", []):
                    _scan(kit.get("features", []))
            elif ftype == "Multiple Features":
                _scan(data.get("features", []))
            elif ftype == "Choice":
                for sel in data.get("selected", []):
                    sdata = sel.get("data") or {}
                    if sel.get("type") == "Skill Choice":
                        _process_skill_choice(sdata)
                    elif sel.get("type") == "Multiple Features":
                        _scan(sdata.get("features", []))

    for lvl in cls.get("featuresByLevel", []):
        if lvl["level"] > level:
            break
        _scan(lvl.get("features", []))

    _scan(hero.get("career", {}).get("features", []))
    _scan(hero.get("ancestry", {}).get("features", []))

    culture = hero.get("culture", {})
    for section_key in ("environment", "organization", "upbringing"):
        section = culture.get(section_key, {})
        if section.get("type") == "Skill Choice":
            _process_skill_choice(section.get("data") or {})

    return skills


def _build_data_df(hero, cls, level, characteristics):
    name = hero.get("name", "Unknown")
    ancestry_name = hero.get("ancestry", {}).get("name", "")
    description = f"Level {level} {ancestry_name} {cls.get('name', '')}".strip()
    picture = hero.get("picture") or ""

    rows = [
        {"category": "Special", "field_name": "Title",       "value": name,        "is_rollable": "FALSE"},
        {"category": "Special", "field_name": "Name",        "value": name,        "is_rollable": "FALSE"},
        {"category": "Special", "field_name": "Description", "value": description, "is_rollable": "FALSE"},
        {"category": "Special", "field_name": "Thumbnail",   "value": picture,     "is_rollable": "FALSE"},
        {"category": "Special", "field_name": "Image",       "value": "",          "is_rollable": "FALSE"},
    ]
    for char_name, val in characteristics.items():
        rows.append({"category": "STAT", "field_name": char_name, "value": val, "is_rollable": "TRUE"})
    for skill_name in _collect_skills(hero, cls, level):
        rows.append({"category": "SKILL", "field_name": skill_name, "value": "", "is_rollable": "FALSE"})

    return pd.DataFrame(rows)


def _build_counters_df(hero, cls, level):
    stamina_max = _compute_stamina(hero, cls, level, hero.get("state", {}).get("inventory", []))
    recoveries_max = _compute_recoveries(hero, cls, level)
    state = hero.get("state", {})
    heroic_name, heroic_desc = _heroic_resource_info(cls, level)

    rows = [
        {"Name": "Stamina",    "Count": stamina_max,    "Max": stamina_max,    "ResetOnRespite": "TRUE",  "Description": f"Winded at {stamina_max // 2} Stamina"},
        {"Name": "Recoveries", "Count": recoveries_max, "Max": recoveries_max, "ResetOnRespite": "TRUE",  "Description": f"Recover {math.ceil(stamina_max / 3)} Stamina"},
        {"Name": "Victories",  "Count": state.get("victories", 0), "Max": 0,   "ResetOnRespite": "FALSE", "Description": f"Gain 1 {heroic_name} for each Victory at the start of an encounter"},
        {"Name": heroic_name,  "Count": 0,              "Max": 0,              "ResetOnRespite": "FALSE", "Description": heroic_desc},
    ]
    return pd.DataFrame(rows)


