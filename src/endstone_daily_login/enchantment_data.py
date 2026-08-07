"""
Enchantment compatibility data for Daily Login plugin.
Defines which enchantments are compatible with each tool and armor type.
Uses string IDs for lazy loading to avoid import errors.
"""

# Enchantment IDs as strings (these will be resolved at runtime)
PROTECTION = "minecraft:protection"
FIRE_PROTECTION = "minecraft:fire_protection"
FEATHER_FALLING = "minecraft:feather_falling"
BLAST_PROTECTION = "minecraft:blast_protection"
PROJECTILE_PROTECTION = "minecraft:projectile_protection"
RESPIRATION = "minecraft:respiration"
AQUA_AFFINITY = "minecraft:aqua_affinity"
THORNS = "minecraft:thorns"
DEPTH_STRIDER = "minecraft:depth_strider"
FROST_WALKER = "minecraft:frost_walker"
SOUL_SPEED = "minecraft:soul_speed"
SWIFT_SNEAK = "minecraft:swift_sneak"

SHARPNESS = "minecraft:sharpness"
SMITE = "minecraft:smite"
BANE_OF_ARTHROPODS = "minecraft:bane_of_arthropods"
KNOCKBACK = "minecraft:knockback"
FIRE_ASPECT = "minecraft:fire_aspect"
LOOTING = "minecraft:looting"

EFFICIENCY = "minecraft:efficiency"
SILK_TOUCH = "minecraft:silk_touch"
FORTUNE = "minecraft:fortune"

POWER = "minecraft:power"
PUNCH = "minecraft:punch"
FLAME = "minecraft:flame"
INFINITY = "minecraft:infinity"

LUCK_OF_THE_SEA = "minecraft:luck_of_the_sea"
LURE = "minecraft:lure"

LOYALTY = "minecraft:loyalty"
IMPALING = "minecraft:impaling"
RIPTIDE = "minecraft:riptide"
CHANNELING = "minecraft:channeling"

MULTISHOT = "minecraft:multishot"
QUICK_CHARGE = "minecraft:quick_charge"
PIERCING = "minecraft:piercing"

MENDING = "minecraft:mending"
UNBREAKING = "minecraft:unbreaking"
CURSE_OF_BINDING = "minecraft:binding"
CURSE_OF_VANISHING = "minecraft:vanishing"

BREACH = "minecraft:breach"
DENSITY = "minecraft:density"
WIND_BURST = "minecraft:wind_burst"

# Common enchantment groups
COMMON_ARMOR = [PROTECTION, FIRE_PROTECTION, BLAST_PROTECTION, PROJECTILE_PROTECTION, 
                THORNS, UNBREAKING, MENDING, CURSE_OF_BINDING, CURSE_OF_VANISHING]

HELMET_ENCHANTS = COMMON_ARMOR + [RESPIRATION, AQUA_AFFINITY]
CHESTPLATE_ENCHANTS = COMMON_ARMOR.copy()
LEGGINGS_ENCHANTS = COMMON_ARMOR + [SWIFT_SNEAK]
BOOTS_ENCHANTS = COMMON_ARMOR + [FEATHER_FALLING, DEPTH_STRIDER, FROST_WALKER, SOUL_SPEED]

SWORD_ENCHANTS = [SHARPNESS, SMITE, BANE_OF_ARTHROPODS, KNOCKBACK, FIRE_ASPECT, 
                  LOOTING, UNBREAKING, MENDING, CURSE_OF_VANISHING]

PICKAXE_ENCHANTS = [EFFICIENCY, SILK_TOUCH, FORTUNE, UNBREAKING, MENDING, CURSE_OF_VANISHING]
AXE_ENCHANTS = [SHARPNESS, SMITE, BANE_OF_ARTHROPODS, EFFICIENCY, SILK_TOUCH, 
                FORTUNE, UNBREAKING, MENDING, CURSE_OF_VANISHING]
SHOVEL_ENCHANTS = [EFFICIENCY, SILK_TOUCH, FORTUNE, UNBREAKING, MENDING, CURSE_OF_VANISHING]
HOE_ENCHANTS = [EFFICIENCY, SILK_TOUCH, FORTUNE, UNBREAKING, MENDING, CURSE_OF_VANISHING]

BOW_ENCHANTS = [POWER, PUNCH, FLAME, INFINITY, UNBREAKING, MENDING, CURSE_OF_VANISHING]
CROSSBOW_ENCHANTS = [MULTISHOT, QUICK_CHARGE, PIERCING, UNBREAKING, MENDING, CURSE_OF_VANISHING]
TRIDENT_ENCHANTS = [LOYALTY, IMPALING, RIPTIDE, CHANNELING, UNBREAKING, MENDING, CURSE_OF_VANISHING]
FISHING_ROD_ENCHANTS = [LUCK_OF_THE_SEA, LURE, UNBREAKING, MENDING, CURSE_OF_VANISHING]

SHIELD_ENCHANTS = [UNBREAKING, MENDING, CURSE_OF_VANISHING]
ELYTRA_ENCHANTS = [UNBREAKING, MENDING, CURSE_OF_BINDING, CURSE_OF_VANISHING]

MACE_ENCHANTS = [SMITE, BANE_OF_ARTHROPODS, FIRE_ASPECT, DENSITY, BREACH, 
                 WIND_BURST, UNBREAKING, MENDING, CURSE_OF_VANISHING]

# Material types for iteration
ARMOR_MATERIALS = ["leather", "chainmail", "iron", "golden", "diamond", "netherite"]
TOOL_MATERIALS = ["wooden", "stone", "iron", "golden", "diamond", "netherite"]

# Build the full compatibility dictionary
ENCHANTMENT_COMPATIBILITY: dict[str, list[str]] = {}

# Helmets
for mat in ARMOR_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_helmet"] = HELMET_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:turtle_helmet"] = HELMET_ENCHANTS.copy()

# Chestplates
for mat in ARMOR_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_chestplate"] = CHESTPLATE_ENCHANTS.copy()

# Leggings
for mat in ARMOR_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_leggings"] = LEGGINGS_ENCHANTS.copy()

# Boots
for mat in ARMOR_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_boots"] = BOOTS_ENCHANTS.copy()

# Swords
for mat in TOOL_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_sword"] = SWORD_ENCHANTS.copy()

# Pickaxes
for mat in TOOL_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_pickaxe"] = PICKAXE_ENCHANTS.copy()

# Axes
for mat in TOOL_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_axe"] = AXE_ENCHANTS.copy()

# Shovels
for mat in TOOL_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_shovel"] = SHOVEL_ENCHANTS.copy()

# Hoes
for mat in TOOL_MATERIALS:
    ENCHANTMENT_COMPATIBILITY[f"minecraft:{mat}_hoe"] = HOE_ENCHANTS.copy()

# Special items
ENCHANTMENT_COMPATIBILITY["minecraft:bow"] = BOW_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:crossbow"] = CROSSBOW_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:trident"] = TRIDENT_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:fishing_rod"] = FISHING_ROD_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:shield"] = SHIELD_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:elytra"] = ELYTRA_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:mace"] = MACE_ENCHANTS.copy()
ENCHANTMENT_COMPATIBILITY["minecraft:shears"] = [EFFICIENCY, UNBREAKING, MENDING, CURSE_OF_VANISHING]
ENCHANTMENT_COMPATIBILITY["minecraft:flint_and_steel"] = [UNBREAKING, MENDING, CURSE_OF_VANISHING]
ENCHANTMENT_COMPATIBILITY["minecraft:carrot_on_a_stick"] = [UNBREAKING, MENDING, CURSE_OF_VANISHING]
ENCHANTMENT_COMPATIBILITY["minecraft:warped_fungus_on_a_stick"] = [UNBREAKING, MENDING, CURSE_OF_VANISHING]
ENCHANTMENT_COMPATIBILITY["minecraft:brush"] = [UNBREAKING, MENDING, CURSE_OF_VANISHING]


def get_compatible_enchantments(item_type: str) -> list[str]:
    """
    Get the list of compatible enchantment IDs for an item type.
    
    Args:
        item_type: Minecraft item type string (e.g., "minecraft:diamond_sword")
        
    Returns:
        List of enchantment ID strings, or empty list if item can't be enchanted
    """
    return ENCHANTMENT_COMPATIBILITY.get(item_type, [])


def get_enchantment_display_name(enchantment_id: str) -> str:
    """
    Get a human-readable display name for an enchantment.
    
    Args:
        enchantment_id: Enchantment ID (e.g., "minecraft:sharpness")
        
    Returns:
        Display name (e.g., "Sharpness")
    """
    # Remove minecraft: prefix and format
    name = enchantment_id.replace("minecraft:", "")
    # Convert underscores to spaces and title case
    return name.replace("_", " ").title()


def can_enchant_item(item_type: str) -> bool:
    """
    Check if an item type can be enchanted.
    
    Args:
        item_type: Minecraft item type string
        
    Returns:
        True if the item can have enchantments
    """
    return item_type in ENCHANTMENT_COMPATIBILITY


def get_enchantment(enchant_id: str):
    """
    Get an Enchantment object from its string ID.
    Uses lazy loading to avoid import errors.
    
    Args:
        enchant_id: Enchantment ID string (e.g., "minecraft:sharpness")
        
    Returns:
        Enchantment object or None if not found
    """
    try:
        from endstone.enchantments import Enchantment
        return Enchantment.get(enchant_id)
    except Exception:
        return None
