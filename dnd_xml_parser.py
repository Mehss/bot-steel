import xml.etree.ElementTree as ET
import json
import pandas as pd
import io


class RacialTrait():
    def __init__(self, internal_id, traitName, race, shortdescription):
        self.internal_id = internal_id
        self.traitName = traitName
        self.race = race
        self.shortdescription = shortdescription
        self.fullDescription = ""


class ClassFeature():
    def __init__(self, featureName, shortdescription, level):
        self.featureName = featureName
        self.shortdescription = shortdescription
        self.level = level

        self.fullDescription = ""


class Feat():
    def __init__(
            self,
            featName,
            prerequisites,
            featDescription,
            tier,
            special,
            type,
            shortdescription,
            associatedPowerInfo,
            associatedPowers
    ):
        self.featName = featName
        self.prerequisites = prerequisites
        self.featDescription = featDescription
        self.tier = tier
        self.special = special
        self.type = type
        self.shortdescription = shortdescription
        self.associatedPowerInfo = associatedPowerInfo
        self.associatedPowers = associatedPowers
        self.fullDescription = ""


class InventoryItem():
    def __init__(self, itemName, count, carried, showonminisheet, weight):
        self.itemName = itemName
        self.count = count
        self.carried = carried
        self.location = ""
        self.showonminisheet = showonminisheet
        self.weight = weight
        self.itemClass = ""
        self.damage = ""
        self.flavor = ""
        self.itemGroup = ""
        self.isIdentified = None
        self.isLocked = None
        self.mitype = None
        self.proficiencyBonus = None
        self.properties = None
        self.subclass = None
        self.range = None


class Power():
    def __init__(
            self, powerName, action, keywords, prepared,
            powerRange, recharge, shortdescription, source,
            weapons, flavor):
        self.powerName = powerName
        self.action = action
        self.keywords = keywords
        self.prepared = prepared
        self.powerRange = powerRange
        self.recharge = recharge
        self.shortdescription = shortdescription
        self.source = source
        self.weapons = weapons
        self.flavor = flavor


class Skill():
    def __init__(
            self, skillName, skillMiscBonus, skillAbility, abilityBonus,
            totalBonus, trained, hasArmorPenalty, armorPenalty):
        self.skillName = skillName
        self.skillMiscBonus = skillMiscBonus
        self.skillAbility = skillAbility
        self.abilityBonus = abilityBonus
        self.totalBonus = totalBonus
        self.trained = trained
        self.hasArmorPenalty = hasArmorPenalty
        self.armorPenalty = armorPenalty


class Weapon():
    def __init__(
            self, name, attack_bonus, damage, defense,
            hit_components, damage_components
    ):
        self.name = name
        self.attack_bonus = attack_bonus
        self.damage = damage
        self.defense = defense
        self.hit_components = hit_components
        self.damage_components = damage_components


class Character():
    def __init__(
            self, characterName=None, className=None, level=None,
            levelBonus=None, player=None, height=None, weight=None,
            gender=None, age=None, alignment=None, company=None,
            portrait=None, experience=None, experienceNeeded=None,
            carriedMoney=None, storedMoney=None, traits=None, appearance=None,
            companions=None, notes=None, strength=None, dexterity=None,
            constitution=None, wisdom=None, intelligence=None, charisma=None,
            strengthModifier=None, dexterityModifier=None,
            constitutionModifier=None, wisdomModifier=None,
            intelligenceModifier=None, charismaModifier=None):
        self.characterName = characterName
        self.className = className
        self.level = level
        self.levelBonus = levelBonus
        self.player = player
        self.height = height
        self.weight = weight
        self.gender = gender
        self.age = age
        self.alignment = alignment
        self.company = company
        self.portrait = portrait
        self.experience = experience
        self.experienceNeeded = experienceNeeded
        self.carriedMoney = carriedMoney
        self.storedMoney = storedMoney
        self.traits = traits
        self.appearance = appearance
        self.companions = companions
        self.notes = notes
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.wisdom = wisdom
        self.intelligence = intelligence
        self.charisma = charisma
        self.strengthModifier = strengthModifier
        self.dexterityModifier = dexterityModifier
        self.constitutionModifier = constitutionModifier
        self.wisdomModifier = wisdomModifier
        self.intelligenceModifier = intelligenceModifier
        self.charismaModifier = charismaModifier
        self.isHeavyArmorEquipped = False
        self.isLightArmorEquipped = False
        self.defenseAC = 0
        self.armor = 0
        self.armorCheckPenalty = 0
        self.armorSpeedPenalty = 0
        self.defenseFortitude = 0
        self.defenseReflex = 0
        self.defenseWill = 0
        self.deity = ""
        self.currentCarriedWeight = 0
        self.maxHp = 0
        self.maxSurges = 0
        self.initiative = 0
        self.initiativeMiscBonus = 0
        self.race = ""
        self.size = ""
        self.baseSpeed = 0
        self.totalSpeed = 0
        self.featsListRulesElements = []
        self.languageRulesElements = []
        self.armorProficiencyElements = []
        self.weaponProficiencyElements = []
        self.inventoryList = []
        self.powerList = []
        self.skillList = []
        self.featList = []
        self.classFeatureList = []
        self.racialTraitList = []

    def appendInventory(self, value):
        self.inventoryList.append(value)

    def appendPower(self, value):
        self.powerList.append(value)

    def appendSkill(self, value):
        self.skillList.append(value)

    def appendFeat(self, value):
        self.featList.append(value)

    def appendClassFeature(self, value):
        self.classFeatureList.append(value)

    def appendRacialTrait(self, value):
        self.racialTraitList.append(value)


# Reading from .dnd4e file
def readCBLoaderCharacterFile(file):
    tree = ET.parse(file)
    root = tree.getroot()
    charactersheetSection = root[0]

    # Character Sheet Sections
    detailSection = charactersheetSection[0]
    statBlocksSection = charactersheetSection[2]
    rulesElementTallySection = charactersheetSection[3]
    lootTallySection = charactersheetSection[4]
    powersStatsSection = charactersheetSection[5]

    # Other Top Level Sections
    levelSection = root[2]
    levelRulesOneElementSection = levelSection[0]

    character = Character(detailSection.find(".//name").text.strip())

    # Reading Character Sheet > Details
    character.characterName = detailSection.find(".//name").text.strip()
    character.level = detailSection.find(".//Level").text.strip()
    character.levelBonus = int(character.level)//2
    character.player = detailSection.find(".//Player").text.strip()
    character.height = detailSection.find(".//Height").text.strip()
    character.weight = detailSection.find(".//Weight").text.strip()
    # This doesn't work. Have to get the gender from a different section
    # character.gender = detailSection.find(".//Gender").text.strip()
    character.age = detailSection.find(".//Age").text.strip()
    # This doesn't work. Have to get the alignnment from a different section.
    # character.alignment = detailSection.find(".//Alignment").text.strip()
    character.comapany = detailSection.find(".//Company").text.strip()
    character.portrait = detailSection.find(".//Portrait").text.strip()
    character.experience = detailSection.find(".//Experience").text.strip()
    character.carriedMoney = detailSection.find(".//CarriedMoney").text.strip()
    character.storedMoney = detailSection.find(".//StoredMoney").text.strip()
    character.traits = detailSection.find(".//Traits").text.strip()
    character.appearance = detailSection.find(".//Appearance").text.strip()
    character.companions = detailSection.find(".//Companions").text.strip()
    character.notes = detailSection.find(".//Notes").text.strip()

    # Class
    classElement = rulesElementTallySection.find(
        ".//RulesElement[@type='Class']")
    if classElement is not None:
        character.className = classElement.get("name")

    # Reading Ability Scores
    for stat in statBlocksSection.findall("Stat"):
        alias = stat.find("alias")
        if alias is not None and alias.get("name") == "Strength":
            character.strength = stat.get("value")
            character.strengthModifier = (int(character.strength)-10)//2
        elif alias is not None and alias.get("name") == "Constitution":
            character.constitution = stat.get("value")
            character.constitutionModifier = (
                int(character.constitution)-10)//2
        elif alias is not None and alias.get("name") == "Dexterity":
            character.dexterity = stat.get("value")
            character.dexterityModifier = (int(character.dexterity)-10)//2
        elif alias is not None and alias.get("name") == "Intelligence":
            character.intelligence = stat.get("value")
            character.intelligenceModifier = (
                int(character.intelligence)-10)//2
        elif alias is not None and alias.get("name") == "Wisdom":
            character.wisdom = stat.get("value")
            character.wisdomModifier = (int(character.wisdom)-10)//2
        elif alias is not None and alias.get("name") == "Charisma":
            character.charisma = stat.get("value")
            character.charismaModifier = (int(character.charisma)-10)//2

    # Read Defenses
    # Determine Light or Heavy Armor because it determines some defense stats
    for loot in lootTallySection.findall(".//loot[@equip-count='1']"):
        rulesElement = loot.find(".//RulesElement[@type='Armor']")
        if rulesElement is not None:
            equippedArmor = rulesElement.get("name")
            if equippedArmor in ["Cloth Armor", "Leather Armor", "Hide Armor"]:
                character.isLightArmorEquipped = True
            elif equippedArmor in ["Chainmail", "Scale Armor", "Plate Armor"]:
                character.isHeavyArmorEquipped = True

    # AC/Fort/Ref/Will
    for stat in statBlocksSection.findall("Stat"):
        alias = stat.find("alias")
        if alias is not None and alias.get("name") == "AC":
            character.defenseAC = stat.get("value")
            armorElement = stat.find(".//statadd[@type='Armor']")
            if (
                armorElement is not None and
                armorElement.get("value") is not None
            ):
                character.armor = armorElement.get("value")
        elif alias is not None and alias.get("name") == "Fortitude Defense":
            character.defenseFortitude = stat.get("value")
        elif alias is not None and alias.get("name") == "Reflex Defense":
            character.defenseReflex = stat.get("value")
        elif alias is not None and alias.get("name") == "Will Defense":
            character.defenseWill = stat.get("value")

    # Deity
    deityElement = rulesElementTallySection.find(
        ".//RulesElement[@type='Deity']"
    )
    if deityElement is not None:
        character.deity = deityElement.get("name")

    # Encumbrance Stats
    for stat in statBlocksSection.findall("Stat"):
        alias = stat.find("alias")
        if alias is not None:
            if alias.get("name") == "Armor Penalty":
                character.armorCheckPenalty = stat.get("value")
            elif alias.get("name") == "Weight":
                character.currentCarriedWeight = stat.get("value")

    # Experience Needed
    for stat in statBlocksSection.findall("Stat"):
        alias = stat.find("alias")
        if alias is not None and alias.get("name") == "XP Needed":
            character.experienceNeeded = stat.get("value")

    # Feats
    character.featsListRulesElements = rulesElementTallySection.findall(
        ".//RulesElement[@type='Feat']"
    )

    # Gender
    genderRulesElement = rulesElementTallySection.find(
        ".//RulesElement[@type='Gender']"
    )
    if genderRulesElement is not None:
        character.gender = genderRulesElement.get("name")

    # Alignment
    alignmentElement = rulesElementTallySection.find(
        ".//RulesElement[@type='Alignment']"
    )
    if alignmentElement is not None:
        character.alignment = alignmentElement.get("name")

    # HP
    for stat in statBlocksSection.findall("Stat"):
        alias = stat.find("alias")
        if alias is not None:
            if alias.get("name") == "Hit Points":
                character.maxHp = stat.get("value")
            elif alias.get("name") == "Healing Surges":
                character.maxSurges = stat.get("value")

    # Initiative
    for stat in statBlocksSection.findall("Stat"):
        alias = stat.find("alias")
        if alias is not None:
            if alias.get("name") == "Initiative":
                character.initiative = stat.get("value")
            elif alias.get("name") == "Initiative Misc":
                character.initiativeMiscBonus = stat.get("value")

    # Inventory List
    for inventoryElement in lootTallySection:
        itemName = inventoryElement[0].get("name")
        count = inventoryElement.get("count")
        carried = "1" if count != "0" else "0"
        showonminisheet = 1
        weight = 0
        inventoryitem = InventoryItem(
            itemName, count, carried, showonminisheet, weight
        )
        character.appendInventory(inventoryitem)

    # Languages
    character.languageRulesElements = rulesElementTallySection.findall(
        ".//RulesElement[@type='Language']"
    )

    # Powers
    for powerElement in powersStatsSection.findall("Power"):
        powerName = powerElement.get("name")
        powerAction = ""
        powerActionTypeElement = powerElement.find(
            ".//specific[@name='Action Type']"
        )
        if powerActionTypeElement is not None:
            powerAction = powerActionTypeElement.text.strip()
        powerPrepared = "1"
        powerRecharge = ""
        powerUsageElement = powerElement.find(
            ".//specific[@name='Power Usage']"
        )
        if powerUsageElement is not None:
            powerRecharge = powerUsageElement.text.strip()
        power = Power(
            powerName, powerAction, "", powerPrepared,
            "", powerRecharge, "", "", [], ""
        )
        for weaponElement in powerElement.findall(".//Weapon"):
            weaponName = weaponElement.get("name", "")

            attackBonusEl = weaponElement.find("AttackBonus")
            attackBonus = (
                attackBonusEl.text.strip()
                if attackBonusEl is not None else "0"
            )

            damageEl = weaponElement.find("Damage")
            damage = damageEl.text.strip() if damageEl is not None else ""

            defenseEl = weaponElement.find("Defense")
            defense = defenseEl.text.strip() if defenseEl is not None else ""

            hitComponentsEl = weaponElement.find("HitComponents")
            hitComponents = (
                hitComponentsEl.text.strip()
                if hitComponentsEl is not None else ""
            )

            damageComponentsEl = weaponElement.find("DamageComponents")
            damageComponents = (
                damageComponentsEl.text.strip()
                if damageComponentsEl is not None else ""
            )

            weapon = Weapon(
                weaponName, attackBonus, damage, defense,
                hitComponents, damageComponents
            )
            power.weapons.append(weapon)
        character.appendPower(power)

    # Armor Proficiencies
    character.armorProficiencyElements = []
    for armorProficiencyElementRead in rulesElementTallySection.findall(
        ".//RulesElement[@type='Proficiency']"
    ):
        if "Armor Proficiency" in armorProficiencyElementRead.get("name"):
            character.armorProficiencyElements.append(
                armorProficiencyElementRead)

    # Weapon Proficiencies
    character.weaponProficiencyElements = []
    for weaponProficiencyElementRead in rulesElementTallySection.findall(
        ".//RulesElement[@type='Proficiency']"
    ):
        if "Weapon Proficiency" in weaponProficiencyElementRead.get("name"):
            character.weaponProficiencyElements.append(
                weaponProficiencyElementRead
            )

    # Race
    raceElement = rulesElementTallySection.find(
        ".//RulesElement[@type='Race']"
    )
    if raceElement is not None:
        character.race = raceElement.get("name")

    # Size
    sizeElement = rulesElementTallySection.find(
        ".//RulesElement[@type='Size']"
    )
    if sizeElement is not None:
        character.size = sizeElement.get("name")

    # Skills
    levelRulesOneSkillRulesElementSection = levelRulesOneElementSection[0]
    for skillRulesSection in levelRulesOneSkillRulesElementSection.findall(
        ".//RulesElement[@type='Skill']"
    ):
        skillName = skillRulesSection.get("name")
        totalBonus = ""
        skillAbility = ""
        isArmorPenalty = 0
        armorPenalty = 0
        trained = "0"
        skillMiscBonus = 0

        for stat in statBlocksSection.findall("Stat"):
            alias = stat.find("alias")
            if alias is not None and alias.get("name") == skillName:
                totalBonus = stat.get("value")
                abilityElem = stat.find(".//statadd[@type='Ability']")
                skillAbility = (
                    abilityElem.get(
                        "statlink") if abilityElem is not None else ""
                )
                armorPenaltyElem = stat.find(
                    ".//statadd[@type='Armor Penalty']"
                )
                isArmorPenalty = (
                    armorPenaltyElem.get("value")
                    if armorPenaltyElem is not None else 0
                )

        abilityModifier = eval(
            "character." + skillAbility.lower() + "Modifier")

        if isArmorPenalty == "1":
            for statArmorPenalty in statBlocksSection.findall("Stat"):
                armorPenaltyAlias = statArmorPenalty.find("alias")
                if (
                    armorPenaltyAlias is not None
                    and armorPenaltyAlias.get("name") == "Armor Penalty"
                ):
                    armorPenalty = statArmorPenalty.get("value")

        for statTrained in statBlocksSection.findall("Stat"):
            trainedStatAlias = statTrained.find("alias")
            if (
                trainedStatAlias is not None
                and trainedStatAlias.get("name") == skillName + " Trained"
            ):
                trainedBonus = statTrained.get("value")
                if int(trainedBonus) > 0:
                    trained = "1"

        for statMisc in statBlocksSection.findall("Stat"):
            miscStatAlias = statMisc.find("alias")
            if (
                miscStatAlias is not None
                and miscStatAlias.get("name") == skillName + " Misc"
            ):
                skillMiscBonus = int(statMisc.get("value"))

        skill = Skill(
            skillName, skillMiscBonus, skillAbility, abilityModifier,
            totalBonus, trained, isArmorPenalty, armorPenalty
        )
        character.appendSkill(skill)

    # Special Abilities - Class Features
    classFeatureElementSection = rulesElementTallySection.findall(
        ".//RulesElement[@type='Class Feature']"
    )
    for classFeatureElement in classFeatureElementSection:
        classFeatureName = classFeatureElement.get("name")
        classFeatureShortDescription = ""
        descElement = classFeatureElement.find(
            ".//specific[@name='Short Description']"
        )
        if descElement is not None:
            classFeatureShortDescription = (
                descElement.text.strip()
                if descElement.text is not None else ""
            )
        classFeature = ClassFeature(
            classFeatureName, classFeatureShortDescription, "1"
        )
        character.appendClassFeature(classFeature)

    # Racial Traits
    racialTraitElementSection = rulesElementTallySection.findall(
        ".//RulesElement[@type='Racial Trait']"
    )
    for racialTraitElement in racialTraitElementSection:
        racialTraitID = racialTraitElement.get("internal-id")
        racialTraitName = racialTraitElement.get("name")
        racialTraitShortDescription = ""
        descElement = racialTraitElement.find(
            ".//specific[@name='Short Description']"
        )
        if descElement is not None:
            racialTraitShortDescription = (
                descElement.text.strip()
                if descElement.text is not None else ""
            )
        racialTrait = RacialTrait(
            racialTraitID, racialTraitName, None, racialTraitShortDescription
        )
        character.appendRacialTrait(racialTrait)

    # Speed
    for stat in statBlocksSection.findall("Stat"):
        alias = stat.find("alias")
        if alias is not None and alias.get("name") == "Speed":
            character.armorSpeedPenalty = (
                stat.find(".//statadd[@type='Armor']").get("value")
                if stat.find(".//statadd[@type='Armor']") is not None else "0"
            )
            character.baseSpeed = (
                stat.find(".//statadd[@Level='1']").get("value")
                if stat.find(".//statadd[@Level='1']") is not None else "0"
            )
            character.totalSpeed = stat.get("value")

    return character


def _get_text(elem: ET.Element, path: str) -> str:
    """Return stripped text from the first subelement matching *path*."""
    sub = elem.find(path)
    return sub.text.strip() if sub is not None and sub.text else ""


# ---------------------------------------------------------------------------
# Main XML merge routine
# ---------------------------------------------------------------------------

def readCBLoaderMainFile(
    character: Character,
    merged_file_location: str = None,
):
    """Populate *character* with data from a merged CBLoader XML file.

    Parameters
    ----------
    character
        An instance that will be enriched with feats, inventory items, powers,
        class features, and racial traits.
    merged_file_location
        Path to the merged XML.  Falls back to the default combined file when
        *None*.
    """
    if merged_file_location is None:
        merged_file_location = (
            "static/characterBuilderLibraries/combined.dnd40.merged.xml"
        )

    tree = ET.parse(merged_file_location)
    root = tree.getroot()

    # ------------------------------------------------------------------ Feats
    for feat_elem in character.featsListRulesElements:
        name = feat_elem.get("name")
        feat_rules = root.find(
            f".//RulesElement[@name=\"{name}\"][@type='Feat']"
        )
        if feat_rules is None:
            continue

        feat = Feat(
            name,
            _get_text(feat_rules, ".//Prereqs"),
            "",  # description (tail, see below)
            _get_text(feat_rules, ".//specific[@name='Tier']"),
            _get_text(feat_rules, ".//specific[@name='Special']"),
            _get_text(feat_rules, ".//specific[@name='type']"),
            _get_text(
                feat_rules, ".//specific[@name='Short Description']"
            ),
            _get_text(
                feat_rules, ".//specific[@name='Associated Power Info']"
            ),
            _get_text(
                feat_rules, ".//specific[@name='Associated Powers']"
            ),
        )

        benefit = feat_rules[-1].tail.strip() if feat_rules[-1].tail else ""
        if benefit:
            feat.featDescription = benefit

        parts: list[str] = []
        if feat.tier:
            parts.append(f"Tier: {feat.tier}\\n")
        if feat.prerequisites:
            parts.append(f"Prerequisites: {feat.prerequisites}\\n\\n")
        if feat.type:
            parts.append(f"Type: {feat.type}\\n\\n")
        if benefit:
            parts.append(f"Benefit: {benefit}\\n")
        if feat.associatedPowerInfo:
            parts.append(
                f"Associated Power Info: {feat.associatedPowerInfo}\\n\\n"
            )
        if feat.associatedPowers:
            parts.append(f"Associated Powers: {feat.associatedPowers}\\n")
        if feat.special:
            parts.append(f"\\nSpecial: {feat.special}\\n")

        feat.fullDescription = "".join(parts)
        character.appendFeat(feat)

    # ------------------------------------------------------------ Inventory
    for inv in character.inventoryList:
        rules = root.find(f".//RulesElement[@name=\"{inv.itemName}\"]")
        if rules is None:
            continue

        inv.weight = _get_text(rules, ".//specific[@name='Weight']") or "0"
        inv.location = _get_text(rules, ".//specific[@name='Item Slot']")
        inv.itemClass = rules.get("type", "").strip()
        inv.itemDamage = _get_text(rules, ".//specific[@name='Damage']")
        inv.itemFlavor = _get_text(rules, ".//specific[@name='Flavor']")
        inv.itemGroup = _get_text(rules, ".//specific[@name='Group']")
        inv.mitype = _get_text(
            rules, ".//specific[@name='Magic Item Type']"
        )
        inv.proficiencyBonus = _get_text(
            rules, ".//specific[@name='Proficiency Bonus']"
        )
        inv.properties = _get_text(
            rules, ".//specific[@name='Properties']"
        )
        inv.subclass = _get_text(
            rules, ".//specific[@name='Weapon Category']"
        )
        inv.range = _get_text(rules, ".//specific[@name='Range']")

    # ---------------------------------------------------------------- Powers
    for power in character.powerList:
        power_rules_list = root.findall(
            f".//RulesElement[@name=\"{power.powerName}\"][@type='Power']"
        )
        if not power_rules_list:
            continue

        power_rules = power_rules_list[-1]  # assume last is latest

        power.keywords = _get_text(
            power_rules, ".//specific[@name='Keywords']"
        )
        power.powerRange = _get_text(
            power_rules, ".//specific[@name='Attack Type']"
        )
        power.flavor = _get_text(
            power_rules, "Flavor"
        )

        # Build description from arbitrary child elements
        description = ""
        for elem in power_rules.iter():
            name_attr = elem.attrib.get("name")
            skip = {
                None,
                "Power Usage",
                "Display",
                "Keywords",
                "Action Type",
                "Attack Type",
                "Class",
                "Level",
                "Power Type",
                "Powers",
            }
            if elem.tag.endswith("Category") or (name_attr in skip):
                continue
            if "_" in (name_attr or ""):
                continue

            if elem.text:
                description += f"{elem.text}\\n\\n"

        power.shortdescription = description
        power.source = _get_text(
            power_rules, ".//specific[@name='Display']"
        )

    # -------------------------------------------------- Class Features
    for feature in character.classFeatureList:
        rules = root.find(
            f".//RulesElement[@name=\"{feature.featureName}\"]"
            "[@type='Class Feature']"
        )
        if rules is None:
            continue

        if rules[-1].tail:
            feature.fullDescription += f"{rules[-1].tail.strip()}\\n\\n"

        sub_feats = _get_text(
            rules, ".//specific[@name='_PARSED_SUB_FEATURES']"
        )
        if sub_feats:
            for fid in sub_feats.split():
                sub = root.find(
                    f".//RulesElement[@internal-id=\"{fid.strip(',')}\"]"
                )
                if sub is None:
                    continue
                feature.fullDescription += f"{sub.attrib['name']}\\n"

                short_desc = _get_text(
                    sub, ".//specific[@name='Short Description']"
                )
                if short_desc:
                    feature.fullDescription += f"{short_desc}\\n\\n"

    # ---------------------------------------------------- Racial Traits
    for trait in character.racialTraitList:
        rules = root.find(
            f".//RulesElement[@name=\"{trait.traitName}\"]"
            "[@type='Racial Trait']"
        )
        if rules is None:
            continue

        if rules[-1].tail:
            trait.fullDescription += f"{rules[-1].tail.strip()}\\n\\n"

        sub_feats = _get_text(
            rules, ".//specific[@name='_PARSED_SUB_FEATURES']"
        )
        if sub_feats:
            for fid in sub_feats.split():
                sub = root.find(
                    f".//RulesElement[@internal-id=\"{fid.strip(',')}\"]"
                )
                if sub is None:
                    continue
                trait.fullDescription += f"{sub.attrib['name']}\\n"

                short_desc = _get_text(
                    sub, ".//specific[@name='Short Description']"
                )
                if short_desc:
                    trait.fullDescription += f"{short_desc}\\n\\n"

    return character


def clean_whitespace(text: str) -> str:
    text = text.encode('utf-8').decode('unicode_escape')
    lines = text.splitlines()
    non_blank_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(non_blank_lines)


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, '__dict__'):
            return o.__dict__
        return str(o)


async def read_character_file(
    data: bytes,
    merged_file_location: str = "dnd_4e/combined.dnd40.merged.xml"
) -> Character:
    """Read a character file and return a Character object."""
    buffer = io.BytesIO(data)
    character = readCBLoaderCharacterFile(file=buffer)
    character = readCBLoaderMainFile(character, merged_file_location)
    return character


async def character_to_excel(character: Character) -> bytes:
    data = [
        ["Special", "Title", character.characterName, False],
        ["Special", "Thumbnail", "", False],
        ["Special", "Image", "", False],
        ["Special", "Description", character.notes, False],
        ["🗒️ Basic", "Name", character.characterName, False],
        ["🗒️ Basic", "Level", character.level, False],
        ["🗒️ Basic", "Class", character.className, False],
        ["🗒️ Basic", "Race", character.race, False],
        ["🗒️ Basic", "Background", "", False],
        ["🗒️ Basic", "Theme", "", False],
        ["🗒️ Basic", "Campaign", "", False],
        ["👤 Stats", "Max HP", character.maxHp, False],
        ["👤 Stats", "HS Amt.", character.maxSurges, False],
        ["👤 Stats", "HS Value", (int(character.maxHp)//2)//2, False],
        ["👤 Stats", "AC", character.defenseAC, False],
        ["👤 Stats", "Fort", character.defenseFortitude, False],
        ["👤 Stats", "Reflex", character.defenseReflex, False],
        ["👤 Stats", "Will", character.defenseWill, False],
    ]

    for skill in character.skillList:
        data.append(
            ["✍️ Skill", f"{skill.skillName}", skill.totalBonus, True]
        )
    for ability in [
        "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom",
        "Charisma"
    ]:
        # data.append(
        #     ["✍️ Ability",
        #      f"{ability} Score",
        #      getattr(character, ability.lower()),
        #      False]
        # )
        data.append(
            [
                "✍️ Ability",
                f"{ability}",
                getattr(character, f"{ability.lower()}Modifier"),
                True
            ]
        )
    for inventory in character.inventoryList:
        if inventory.count == "0" or inventory.carried == "0":
            continue
        data.append(
            [
                "⚔️ Equipment",
                inventory.location,
                f"{inventory.itemName}",
                False
            ]
        )

    # Create the DataFrame
    dfData = pd.DataFrame(
        data,
        columns=["category", "field_name", "value", "is_rollable"]
    )

    actions = []
    for power in character.powerList:
        usages = "1"
        if power.recharge == "At-Will":
            usages = ""
        reset_on = ""
        if power.recharge == "Encounter":
            reset_on = "sr"
        elif power.recharge == "Daily":
            reset_on = "lr"
        effect = clean_whitespace(power.shortdescription)
        if not power.weapons:
            actions.append(
                [
                    f"{power.powerName}",
                    power.action, power.recharge, "", power.powerRange,
                    effect, power.flavor, "", usages, usages,
                    "", "", reset_on,
                    "", "",
                    "", ""
                ]
            )
            continue
        for weapon in power.weapons:
            if len(power.weapons) > 1 and weapon.name == "Unarmed":
                continue
            crit_die = "1d6"
            if weapon.damage == "":
                crit_die = ""
            actions.append(
                [
                    f"{power.powerName} ({weapon.name})",
                    power.action, power.recharge, "", power.powerRange,
                    effect, power.flavor, "", usages, usages,
                    f"1d20+{weapon.attack_bonus}", weapon.damage, reset_on,
                    weapon.defense, crit_die,
                    f"'{weapon.hit_components}", f"'{weapon.damage_components}"
                ]
            )

    # Define column names
    columns = [
        "Name", "Type1", "Type2", "ShortDesc", "Range", "Effect",
        "Flavor", "Image", "Usages", "MaxUsages", "To Hit", "Damage",
        "ResetOn", "DefTarget", "Critdie", "HitNotes", "DamageNotes"
    ]
    dfActions = pd.DataFrame(actions, columns=columns)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dfData.to_excel(writer, sheet_name="data", index=False)
        dfActions.to_excel(writer, sheet_name="actions", index=False)

    return buffer
