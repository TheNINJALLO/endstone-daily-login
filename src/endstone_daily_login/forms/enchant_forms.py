"""
Enchantment selection forms for Daily Login plugin.
Provides UI for operators to select enchantments for tool/armor rewards.
"""

from typing import TYPE_CHECKING, Callable, Any
from endstone import Player
from endstone.form import ModalForm, Toggle, Slider, Label

from endstone_daily_login.enchantment_data import (
    get_compatible_enchantments,
    get_enchantment_display_name,
    can_enchant_item,
)

if TYPE_CHECKING:
    from endstone_daily_login.daily_login import DailyLoginPlugin


class EnchantmentForms:
    """Forms for configuring enchantments on item rewards."""
    
    def __init__(self, plugin: "DailyLoginPlugin"):
        self.plugin = plugin
        self.db = plugin.db
    
    def open_enchantment_config(
        self, 
        player: Player, 
        item_type: str,
        current_enchantments: dict[str, int] | None = None,
        on_complete: Callable[[dict[str, int]], None] | None = None
    ) -> None:
        """
        Open the enchantment configuration form for an item.
        
        Args:
            player: The player to show the form to
            item_type: Minecraft item type (e.g., "minecraft:diamond_sword")
            current_enchantments: Currently configured enchantments {id: level}
            on_complete: Callback when configuration is complete
        """
        if not can_enchant_item(item_type):
            player.send_message("§cThis item cannot be enchanted.")
            if on_complete:
                on_complete({})
            return
        
        compatible = get_compatible_enchantments(item_type)
        if not compatible:
            player.send_message("§cNo compatible enchantments found for this item.")
            if on_complete:
                on_complete({})
            return
        
        current_enchantments = current_enchantments or {}
        
        # Build form controls
        controls = [Label(text=f"Configure enchantments for {item_type}")]
        
        # For each enchantment, add a toggle and slider
        enchant_order = []  # Track order for parsing response
        for enchant_id in compatible:
            display_name = get_enchantment_display_name(enchant_id)
            is_enabled = enchant_id in current_enchantments
            current_level = current_enchantments.get(enchant_id, 1)
            
            # Toggle to enable/disable this enchantment
            controls.append(Toggle(
                label=display_name,
                default_value=is_enabled
            ))
            
            # Slider for level (1-10 as requested by user)
            controls.append(Slider(
                label=f"{display_name} Level",
                min=1,
                max=10,
                step=1,
                default_value=float(current_level)
            ))
            
            enchant_order.append(enchant_id)
        
        def on_submit(p: Player, response: str):
            import json
            try:
                values = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                player.send_message("§cError parsing form response.")
                if on_complete:
                    on_complete(current_enchantments)
                return
            
            # Parse the response
            # First value is label (ignored in response)
            # Then pairs of (toggle, slider) for each enchantment
            new_enchantments = {}
            value_index = 0  # Skip label
            
            for enchant_id in enchant_order:
                if value_index >= len(values):
                    break
                    
                # Get toggle value (bool or 0/1)
                toggle_val = values[value_index]
                is_enabled = toggle_val is True or toggle_val == 1 or toggle_val == "true"
                value_index += 1
                
                # Get slider value
                if value_index < len(values):
                    level = int(float(values[value_index]))
                    value_index += 1
                else:
                    level = 1
                
                if is_enabled:
                    new_enchantments[enchant_id] = level
            
            player.send_message(f"§aConfigured {len(new_enchantments)} enchantment(s).")
            
            if on_complete:
                on_complete(new_enchantments)
        
        def on_close(p: Player):
            player.send_message("§eEnchantment configuration cancelled.")
            if on_complete:
                on_complete(current_enchantments)
        
        form = ModalForm(
            title="Configure Enchantments",
            controls=controls,
            submit_button="Save Enchantments",
            on_submit=on_submit,
            on_close=on_close
        )
        
        player.send_form(form)
    
    def show_enchantment_summary(self, player: Player, enchantments: dict[str, int]) -> None:
        """
        Show a summary of configured enchantments to the player.
        
        Args:
            player: The player to show the summary to
            enchantments: Dictionary of enchantment IDs to levels
        """
        if not enchantments:
            player.send_message("§7No enchantments configured.")
            return
        
        lines = ["§aConfigured Enchantments:"]
        for enchant_id, level in enchantments.items():
            display_name = get_enchantment_display_name(enchant_id)
            lines.append(f"§7- {display_name} {level}")
        
        player.send_message("\n".join(lines))
