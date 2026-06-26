# DS Hero Parser

Parses `.ds-hero` files exported from the Draw Steel Character Builder and updates an existing character's abilities and counters in the bot.

## Usage

Requires an existing sheet entry (created via `;;cb_generate`). Attach a `.ds-hero` file and run:

```
;;addhere
```

or the alias:

```
;;add_hero_sheet
```

The command overwrites `actions` and `counters` for the current guild+user, leaving `data` and `sheet_url` unchanged.

---

## Parsing Logic

### Entry point — `parse_ds_hero(data: bytes)`

```
bytes
  └─ json.loads()
       ├─ hero["class"]            → cls
       ├─ cls["level"]             → level  (caps all feature collection)
       ├─ cls["characteristics"]   → {Might: 2, Agility: -1, …}
       │
       ├─ _collect_abilities(cls, level)              → abilities[]
       ├─ _collect_kit_bonuses(cls, level)            → melee_per_kit, ranged_per_kit
       ├─ _build_actions_df(abilities, chars, …)      → actions_df
       └─ _build_counters_df(hero, cls, level)        → counters_df

Returns: (name, actions_df, counters_df)
```

---

### Ability collection — `_collect_abilities`

Uses a nested `_scan_source(source, ability_pool)` closure that processes one source (class or selected subclass) at a time. Inside, `_scan(features)` recurses over a feature list:

| Feature type | Action |
|---|---|
| `Kit` | Recurse into each selected kit's `features[]` |
| `Ability` | Append `data["ability"]` directly |
| `Multiple Features` | Recurse into `data["features"]` |
| `Class Ability` | Add `data["selectedIDs"]` to deferred lookup set |
| `Choice` | Walk `data["selected"]`: append `Ability` entries; recurse into `Multiple Features` entries |

After the loop, deferred IDs are resolved against `ability_pool` and appended.

`_scan_source` is called for both `cls` (against `cls["abilities"]`) and each selected subclass (against `sub["abilities"]`).

**Ability order in output:**
1. Kit signature abilities
2. Directly-embedded level feature abilities (Mark, Strike Now!, etc.)
3. Selected class heroic abilities (3pt, 5pt, …)
4. Selected subclass doctrine abilities

---

### Kit damage bonuses — `_collect_kit_bonuses`

Scans `featuresByLevel` up to `level` for `Kit` features. For each selected kit, collects `meleeDamage` and `rangedDamage` as `(tier1, tier2, tier3)` tuples — one entry per kit that has a non-zero bonus.

Returns `(melee_per_kit, ranged_per_kit)` as lists of tuples.

**Applied in `_ability_to_row`:** if the ability has keywords `Weapon` + `Strike`, the relevant list is selected (melee, ranged, or the higher of both for dual-type abilities). `_apply_kit_bonuses` then replaces the base damage number in each tier string with per-kit totals:

| Tier string after `_sub_chars` | melee_per_kit | Result |
|---|---|---|
| `"5 damage"` | `[(2,2,2), (1,1,1)]` | `"7/6 damage"` |
| `"5 damage; vertical pull 1"` | `[(2,2,2), (1,1,1)]` | `"7/6 damage; vertical pull 1"` |
| `"Each target gains 1 surge."` | `[(2,2,2)]` | `"Each target gains 1 surge."` (no match) |

---

### Ability → row — `_ability_to_row`

Each ability object maps to one row in `actions_df`.

**Cost**
```python
if cost_raw == "signature" or cost_raw == 0:
    cost = "0"
else:
    cost = f"{cost_raw} Focus"   # e.g. "3 Focus", "5 Focus"
```
`;;a` splits on the first space to read the number: `cost.split(' ')[0]`.

**Range** — `_format_distance`

| `type` | Output |
|---|---|
| `"Self"` | `"Self"` |
| `"Special"` | value of `d["special"]` |
| any other + `value > 0` | `"Melee 1"`, `"Ranged 10"`, etc. |

Multiple distances are joined with `" / "`.

**Sections** — `ability["sections"]` is a mixed list:

| Section type | Handling |
|---|---|
| `roll` | Sets `is_roll = "TRUE"`; extracts `tier1/2/3` and `characteristic[]` for Bonus |
| `text` | Appended to `text_parts[]` |
| `field` | Formatted as `**Name** (N Focus): effect` and appended to `field_parts[]` |

`Effect = "\n".join(text_parts + field_parts)`

**Tier substitution** — `_sub_chars(text, characteristics)`

Applied to T1, T2, T3 in three passes before kit bonuses:

1. **Resolve characteristic chains** — `M or A`, `M or A or R`, `M, A, or R`, `M, A or R` → `max(values)`
2. **Replace standalone letters** — any remaining `M/A/R/I/P` → numeric value
3. **Evaluate arithmetic** — `N + N` (including `N + -N`) → single number
4. **Resolve potency tiers** — `[strong]` = highest char, `[average]` = strong−1, `[weak]` = strong−2

| Raw | Haruhiro (M=+2, A=−1, R=+2, highest=2) |
|---|---|
| `"3 + M or A damage"` | `"5 damage"` |
| `"5 + M, A, or R damage"` | `"7 damage"` |
| `"3 + A damage"` | `"2 damage"` |
| `"R < [weak], frightened"` | `"2 < 0, frightened"` |
| `"1 < [average], dazed"` | `"1 < 1, dazed"` |
| `"1 < [strong], dazed"` | `"1 < 2, dazed"` |

Does not apply to the `Effect` column.

**Bonus column** — resolved numeric value of the roll's characteristic(s) plus any flat bonus:

```python
char_val = max(characteristics.get(c, 0) for c in roll["characteristic"])
bonus = str(char_val + roll.get("bonus", 0))
# ["Might", "Agility"] with M=2, A=-1 → "2"
# ["Reason"] with R=2, bonus=1      → "3"
```

---

### Counters — `_build_counters_df`

`;;a` deducts the heroic resource using `resources.iloc[3]` (hardcoded index). Counter order is fixed:

| index | Name | Count | Max | ResetOnRespite |
|---|---|---|---|---|
| 0 | Stamina | = Max | computed | `"TRUE"` |
| 1 | Recoveries | = Max | computed | `"TRUE"` |
| 2 | Victories | from `state.victories` | 0 (unlimited) | `"FALSE"` |
| 3 | Heroic resource | 0 | 0 (unlimited) | `"FALSE"` |

`ResetOnRespite = "FALSE"` → resets on `;;reset` (encounter end).  
`ResetOnRespite = "TRUE"` → only resets on `;;respite`.

**Stamina** — `_compute_stamina`

```
Stamina = class_base + (class_per_level × (level − 1)) + sum(kit.stamina)
```

Example — Haruhiro Aizou (Level 2 Tactician, Shining Armor + Whirlwind):
```
21 + (9 × 1) + 12 + 0 = 42
```

**Recoveries** — `_compute_recoveries`: first `Bonus` feature with `field == "Recoveries"`, default `10`.

**Heroic resource name** — first `Heroic Resource` feature up to `level`, default `"Focus"`.

---

## What Gets Parsed

| Source | Output |
|---|---|
| `class.level` | Level cap for all feature collection |
| `class.characteristics` | Characteristic values for substitution and Bonus column |
| `featuresByLevel[].Bonus (Stamina)` | Stamina base + per-level scaling |
| `featuresByLevel[].Bonus (Recoveries)` | Max Recoveries |
| `featuresByLevel[].Kit.selected` | Stamina bonus; melee/ranged damage per tier; signature abilities |
| `featuresByLevel[].Ability` | Embedded level feature abilities |
| `featuresByLevel[].Multiple Features` | Ability bundles |
| `featuresByLevel[].Class Ability.selectedIDs` | Chosen heroic abilities |
| `featuresByLevel[].Heroic Resource` | Heroic resource name |
| `subclasses[selected].featuresByLevel` | Subclass abilities and doctrine picks |

---

## Output DataFrames

### `actions_df` — used by `;;a`

| column | source |
|---|---|
| Name | `ability.name` |
| Action | `ability.type.usage` |
| Cost | `"0"` for signature / `"N Focus"` for heroic |
| ShortDesc | `ability.description` |
| IsRoll | `"TRUE"` if ability has a roll section |
| Bonus | Max characteristic value + flat bonus (number string) |
| T1 / T2 / T3 | Tier strings after char substitution and kit damage |
| Effect | Concatenated text + field sections |
| Target | `ability.target` |
| Range | Formatted from `ability.distance[]` |
| Trigger | `ability.type.trigger` |

### `counters_df` — used by `;;r`

Index order is fixed — `;;a` deducts Focus by hardcoded `resources.iloc[3]`.

| index | Name | Reset on |
|---|---|---|
| 0 | Stamina | Respite |
| 1 | Recoveries | Respite |
| 2 | Victories | Encounter end |
| 3 | Focus *(or class heroic resource)* | Encounter end |

---

## Limitations

- `;;i join` (initiative tracker) is not supported — the system expects D&D 4e fields not present in `.ds-hero` files.
- `;;addhere` requires an existing sheet entry; use `;;cb_generate` first.
- Reloading a character resets all counter values to max.
