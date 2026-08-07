"""
Reward configuration and claiming forms for Daily Login plugin.
Handles money, item, and structure reward setup and claiming.
"""

from typing import TYPE_CHECKING
import json
from endstone import Player
from endstone.form import ActionForm, ModalForm, Toggle, TextInput, Dropdown, Slider, Label, Button
from endstone.inventory import ItemStack

from endstone_daily_login.utils import format_with_commas, get_current_time_ms
from endstone_daily_login.enchantment_data import can_enchant_item, get_enchantment

if TYPE_CHECKING:
    from endstone_daily_login.daily_login import DailyLoginPlugin


class RewardForms:
    """Forms for reward configuration and claiming."""
    
    def __init__(self, plugin: "DailyLoginPlugin"):
        self.plugin = plugin
        self.db = plugin.db
    
    # ========== Reward Settings Menu ==========
    
    def open_reward_settings(self, player: Player) -> None:
        """Open the reward settings menu."""
        def on_submit(p: Player, selection: int):
            if selection == 0:
                self.open_money_reward_setup(player)
            elif selection == 1:
                self.open_item_reward_setup(player)
            elif selection == 2:
                self.open_structure_reward_setup(player)
        
        form = ActionForm(
            title="Reward Settings",
            content="Select the type of reward to configure.",
            buttons=[
                Button(text="Money Reward Setup"),
                Button(text="Item Reward Setup"),
                Button(text="Structure File Reward Setup"),
            ],
            on_submit=on_submit
        )
        
        player.send_form(form)
    
    # ========== Money Reward Setup ==========
    
    def open_money_reward_setup(self, player: Player) -> None:
        """Open the money reward configuration form."""
        current_settings = self.db.get('moneyRewardSettings') or {
            'amounts': [1000],
            'randomize': False,
            'enabled': True
        }
        
        amounts = current_settings.get('amounts', [1000])
        
        controls = [
            Toggle(label="Enable Money Reward", default_value=current_settings.get('enabled', True)),
            Toggle(label="Randomize Money Reward", default_value=current_settings.get('randomize', False)),
        ]
        
        # Add text field for each existing amount
        for i, amount in enumerate(amounts):
            controls.append(TextInput(
                label=f"Day {i + 1} Amount",
                placeholder="e.g., 1000",
                default_value=str(amount)
            ))
        
        # Add empty field for new amount
        controls.append(TextInput(
            label=f"Day {len(amounts) + 1} Amount (leave empty to skip)",
            placeholder="e.g., 5000",
            default_value=""
        ))
        
        def on_submit(p: Player, response: str):
            try:
                values = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                player.send_message("§cError parsing form response.")
                return
            
            enabled = values[0] is True or values[0] == 1
            randomize = values[1] is True or values[1] == 1
            
            # Parse amounts from remaining values
            new_amounts = []
            for val in values[2:]:
                if val and str(val).strip():
                    try:
                        amount = float(str(val).strip())
                        if amount > 0:
                            new_amounts.append(amount)
                    except ValueError:
                        pass
            
            if not new_amounts:
                new_amounts = [1000]  # Default
            
            self.db.set('moneyRewardSettings', {
                'amounts': new_amounts,
                'randomize': randomize,
                'enabled': enabled
            })
            
            player.send_message("§aMoney reward settings updated.")
            # Reopen for more edits
            self.open_money_reward_setup(player)
        
        form = ModalForm(
            title="Money Reward Setup",
            controls=controls,
            submit_button="Save",
            on_submit=on_submit
        )
        
        player.send_form(form)
    
    # ========== Item Reward Setup ==========
    
    def open_item_reward_setup(self, player: Player) -> None:
        """Open the item reward configuration form."""
        current_settings = self.db.get('itemRewardSettings') or {
            'items': [],
            'randomize': False,
            'enabled': False
        }
        
        items = current_settings.get('items', [])
        
        controls = [
            Toggle(label="Enable Item Reward", default_value=current_settings.get('enabled', False)),
            Toggle(label="Randomize Item Reward", default_value=current_settings.get('randomize', False)),
        ]
        
        label_prefix = "Item" if current_settings.get('randomize') else "Day"
        
        # Add text field for each existing item
        for i, item in enumerate(items):
            # Handle both old format (string) and new format (dict with type and enchantments)
            if isinstance(item, dict):
                item_type = item.get('type', '')
            else:
                item_type = str(item)
            
            controls.append(TextInput(
                label=f"{label_prefix} {i + 1} Item ID",
                placeholder="e.g., minecraft:diamond_sword",
                default_value=item_type
            ))
        
        # Add empty field for new item
        controls.append(TextInput(
            label=f"{label_prefix} {len(items) + 1} Item ID (leave empty to skip)",
            placeholder="e.g., minecraft:apple",
            default_value=""
        ))
        
        def on_submit(p: Player, response: str):
            try:
                values = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                player.send_message("§cError parsing form response.")
                return
            
            enabled = values[0] is True or values[0] == 1
            randomize = values[1] is True or values[1] == 1
            
            # Parse items from remaining values
            new_items = []
            existing_items = current_settings.get('items', [])
            
            for idx, val in enumerate(values[2:]):
                item_type = str(val).strip() if val else ""
                
                if item_type.startswith("minecraft:"):
                    # Check if this is an existing item with enchantments
                    existing_enchants = {}
                    if idx < len(existing_items):
                        existing_item = existing_items[idx]
                        if isinstance(existing_item, dict):
                            existing_enchants = existing_item.get('enchantments', {})
                    
                    if can_enchant_item(item_type):
                        new_items.append({
                            'type': item_type,
                            'enchantments': existing_enchants
                        })
                    else:
                        new_items.append({'type': item_type})
            
            self.db.set('itemRewardSettings', {
                'items': new_items,
                'randomize': randomize,
                'enabled': enabled
            })
            
            player.send_message("§aItem reward settings updated.")
            
            # Check if any new enchantable items were added and offer to configure them
            self._offer_enchantment_config(player, new_items)
        
        form = ModalForm(
            title="Item Reward Setup",
            controls=controls,
            submit_button="Save",
            on_submit=on_submit
        )
        
        player.send_form(form)
    
    def _offer_enchantment_config(self, player: Player, items: list) -> None:
        """Offer to configure enchantments for enchantable items."""
        enchantable_items = []
        for i, item in enumerate(items):
            if isinstance(item, dict):
                item_type = item.get('type', '')
                if can_enchant_item(item_type):
                    enchantable_items.append((i, item_type, item.get('enchantments', {})))
        
        if not enchantable_items:
            self.open_item_reward_setup(player)
            return
        
        # Create menu to select which item to configure enchantments for
        buttons = []
        for idx, item_type, enchants in enchantable_items:
            enchant_count = len(enchants)
            label = f"{item_type.replace('minecraft:', '')} ({enchant_count} enchants)"
            buttons.append(Button(text=label))
        
        buttons.append(Button(text="§7Done - Back to Item Setup"))
        
        def on_submit(p: Player, selection: int):
            if selection < len(enchantable_items):
                idx, item_type, current_enchants = enchantable_items[selection]
                self._configure_item_enchantments(player, idx, item_type, current_enchants)
            else:
                self.open_item_reward_setup(player)
        
        form = ActionForm(
            title="Configure Enchantments",
            content="Select an item to configure its enchantments:",
            buttons=buttons,
            on_submit=on_submit,
            on_close=lambda p: self.open_item_reward_setup(player)
        )
        
        player.send_form(form)
    
    def _configure_item_enchantments(
        self, 
        player: Player, 
        item_index: int, 
        item_type: str, 
        current_enchants: dict
    ) -> None:
        """Configure enchantments for a specific item."""
        from endstone_daily_login.forms.enchant_forms import EnchantmentForms
        
        enchant_forms = EnchantmentForms(self.plugin)
        
        def on_complete(new_enchants: dict):
            # Update the item's enchantments in the database
            settings = self.db.get('itemRewardSettings') or {'items': [], 'enabled': False, 'randomize': False}
            items = settings.get('items', [])
            
            if item_index < len(items):
                if isinstance(items[item_index], dict):
                    items[item_index]['enchantments'] = new_enchants
                else:
                    items[item_index] = {
                        'type': items[item_index],
                        'enchantments': new_enchants
                    }
                
                settings['items'] = items
                self.db.set('itemRewardSettings', settings)
            
            # Go back to enchantment selection menu
            self._offer_enchantment_config(player, items)
        
        enchant_forms.open_enchantment_config(
            player, 
            item_type, 
            current_enchants, 
            on_complete
        )
    
    # ========== Structure Reward Setup ==========
    
    def open_structure_reward_setup(self, player: Player) -> None:
        """Open the structure reward configuration form."""
        current_settings = self.db.get('structureRewardSettings') or {
            'structures': [],
            'randomize': False,
            'enabled': False
        }
        
        structures = current_settings.get('structures', [])
        
        controls = [
            Toggle(label="Enable Structure Reward", default_value=current_settings.get('enabled', False)),
            Toggle(label="Randomize Structure Reward", default_value=current_settings.get('randomize', False)),
        ]
        
        label_prefix = "Structure File" if current_settings.get('randomize') else "Day"
        
        # Add text field for each existing structure
        for i, structure in enumerate(structures):
            controls.append(TextInput(
                label=f"{label_prefix} {i + 1} Structure File Name",
                placeholder="e.g., mystructure",
                default_value=str(structure)
            ))
        
        # Add empty field for new structure
        controls.append(TextInput(
            label=f"{label_prefix} {len(structures) + 1} Structure File Name",
            placeholder="e.g., mystructure",
            default_value=""
        ))
        
        def on_submit(p: Player, response: str):
            try:
                values = json.loads(response)
            except (json.JSONDecodeError, TypeError):
                player.send_message("§cError parsing form response.")
                return
            
            enabled = values[0] is True or values[0] == 1
            randomize = values[1] is True or values[1] == 1
            
            # Parse structures from remaining values
            new_structures = []
            for val in values[2:]:
                structure = str(val).strip() if val else ""
                if structure:
                    new_structures.append(structure)
            
            self.db.set('structureRewardSettings', {
                'structures': new_structures,
                'randomize': randomize,
                'enabled': enabled
            })
            
            player.send_message("§aStructure reward settings updated.")
            self.open_structure_reward_setup(player)
        
        form = ModalForm(
            title="Structure Reward Setup",
            controls=controls,
            submit_button="Save",
            on_submit=on_submit
        )
        
        player.send_form(form)
    
    # ========== Reward Claiming ==========
    
    def open_claim_form(self, player: Player, player_data: dict) -> None:
        """Open the reward claiming form for a player."""
        now = get_current_time_ms()
        current_streak_day = player_data.get('streak', 0) + 1
        last_claim = player_data.get('lastClaim', 0)
        next_claim_time = last_claim + (24 * 60 * 60 * 1000)  # 24 hours in ms
        
        # Check if player can claim
        if now < next_claim_time:
            from endstone_daily_login.utils import get_time_remaining_string
            remaining = get_time_remaining_string(next_claim_time)
            player.send_message(f"§cPlease wait {remaining} to claim a daily reward again!")
            return
        
        # Fetch reward settings
        money_settings = self.db.get('moneyRewardSettings') or {'amounts': [], 'enabled': False, 'randomize': False}
        item_settings = self.db.get('itemRewardSettings') or {'items': [], 'enabled': False, 'randomize': False}
        structure_settings = self.db.get('structureRewardSettings') or {'structures': [], 'enabled': False, 'randomize': False}
        
        buttons = []
        enabled_rewards = []
        
        # Money reward
        if money_settings.get('enabled') and money_settings.get('amounts'):
            amounts = money_settings['amounts']
            if money_settings.get('randomize'):
                min_money = min(amounts)
                max_money = max(amounts)
                label = f"Money Reward: {format_with_commas(min_money)} - {format_with_commas(max_money)}"
            elif current_streak_day <= len(amounts):
                amount = amounts[current_streak_day - 1]
                label = f"Money Reward: {format_with_commas(amount)}"
            else:
                label = f"No Money Reward for Day {current_streak_day}"
            buttons.append(Button(text=label))
            enabled_rewards.append('money')
        
        # Item reward
        if item_settings.get('enabled') and item_settings.get('items'):
            buttons.append(Button(text="Random Item Reward"))
            enabled_rewards.append('item')
        
        # Structure reward
        if structure_settings.get('enabled') and structure_settings.get('structures'):
            structures = structure_settings['structures']
            if structure_settings.get('randomize'):
                label = "Random Structure Reward"
            elif current_streak_day <= len(structures):
                label = f"Structure Reward: {structures[current_streak_day - 1]}"
            else:
                label = None
            
            if label:
                buttons.append(Button(text=label))
                enabled_rewards.append('structure')
        
        # No rewards available
        if not enabled_rewards:
            buttons.append(Button(text="No Rewards Available"))
            enabled_rewards.append('none')
        
        def on_submit(p: Player, selection: int):
            if selection >= len(enabled_rewards):
                return
            
            selected = enabled_rewards[selection]
            
            if selected == 'none':
                player.send_message("§cPlease contact your admin... no rewards available today.")
                return
            
            self._give_reward(player, player_data, selected, current_streak_day)
        
        def on_close(p: Player):
            player.send_message("§cYou have canceled the reward claim.")
        
        form = ActionForm(
            title="Choose Your Reward",
            content=f"Select Day {current_streak_day} Reward!",
            buttons=buttons,
            on_submit=on_submit,
            on_close=on_close
        )
        
        player.send_form(form)
    
    def _give_reward(self, player: Player, player_data: dict, reward_type: str, streak_day: int) -> None:
        """Give the selected reward to the player."""
        now = get_current_time_ms()
        
        if reward_type == 'money':
            self._give_money_reward(player, player_data, streak_day)
        elif reward_type == 'item':
            if not self._give_item_reward(player, player_data, streak_day):
                return  # Don't update claim if inventory was full
        elif reward_type == 'structure':
            self._give_structure_reward(player, player_data, streak_day)
        
        # Update player data
        player_data['lastClaim'] = now
        player_data['streak'] = player_data.get('streak', 0) + 1
        self.db.set(player.name, player_data)
    
    def _give_money_reward(self, player: Player, player_data: dict, streak_day: int) -> None:
        """Give money reward to player."""
        settings = self.db.get('moneyRewardSettings') or {}
        amounts = settings.get('amounts', [1000])
        
        if settings.get('randomize'):
            import random
            amount = random.choice(amounts)
        elif streak_day <= len(amounts):
            amount = amounts[streak_day - 1]
        else:
            amount = amounts[-1] if amounts else 1000
        
        amount = int(round(amount))
        
        # Get currency objective name
        reward_options = self.db.get('rewardOptions') or {}
        currency_obj = reward_options.get('currencyObj', 'money')
        
        # Add to scoreboard (quote player name for names with spaces)
        self.plugin.server.dispatch_command(
            self.plugin.server.command_sender,
            f'scoreboard players add "{player.name}" {currency_obj} {amount}'
        )
        
        player.send_message(f"§aYou received {format_with_commas(amount)} {currency_obj}.")
    
    def _give_item_reward(self, player: Player, player_data: dict, streak_day: int) -> bool:
        """Give item reward to player. Returns False if inventory is full."""
        settings = self.db.get('itemRewardSettings') or {}
        items = settings.get('items', [])
        
        if not items:
            player.send_message("§cNo items configured for rewards.")
            return False
        
        # Check for open inventory slot
        inventory = player.inventory
        if inventory.first_empty < 0:
            player.send_message("§cPlease make space in your inventory first. You have not claimed your reward yet.")
            return False
        
        # Select item
        if settings.get('randomize'):
            import random
            item_config = random.choice(items)
        elif streak_day <= len(items):
            item_config = items[streak_day - 1]
        else:
            item_config = items[-1] if items else {'type': 'minecraft:stick'}
        
        # Handle both old format (string) and new format (dict)
        if isinstance(item_config, dict):
            item_type = item_config.get('type', 'minecraft:stick')
            enchantments = item_config.get('enchantments', {})
        else:
            item_type = str(item_config)
            enchantments = {}
        
        # Create item stack
        item_stack = ItemStack(type=item_type, amount=1)
        
        # Apply enchantments
        if enchantments:
            self.plugin.logger.info(f"[DEBUG] Applying enchantments: {enchantments}")
            meta = item_stack.item_meta
            for enchant_id, level in enchantments.items():
                try:
                    # Try both formats - with and without minecraft: prefix
                    result = meta.add_enchant(enchant_id, int(level), True)
                    self.plugin.logger.info(f"[DEBUG] add_enchant({enchant_id}, {level}) = {result}")
                    
                    # If that failed, try without minecraft: prefix
                    if not result and enchant_id.startswith("minecraft:"):
                        short_id = enchant_id.replace("minecraft:", "")
                        result2 = meta.add_enchant(short_id, int(level), True)
                        self.plugin.logger.info(f"[DEBUG] add_enchant({short_id}, {level}) = {result2}")
                except Exception as e:
                    self.plugin.logger.error(f"[DEBUG] Failed to add enchant {enchant_id}: {e}")
            item_stack.set_item_meta(meta)
            self.plugin.logger.info(f"[DEBUG] set_item_meta called")
        
        # Add to inventory
        inventory.add_item(item_stack)
        
        # Build message
        display_name = item_type.replace("minecraft:", "").replace("_", " ").title()
        if enchantments:
            enchant_names = [f"{k.replace('minecraft:', '').replace('_', ' ').title()} {v}" 
                          for k, v in enchantments.items()]
            enchant_str = ", ".join(enchant_names)
            player.send_message(f"§aYou received: {display_name} with {enchant_str}.")
        else:
            player.send_message(f"§aYou received an item: {display_name}.")
        
        return True
    
    def _give_structure_reward(self, player: Player, player_data: dict, streak_day: int) -> None:
        """Give structure reward to player."""
        settings = self.db.get('structureRewardSettings') or {}
        structures = settings.get('structures', [])
        
        if not structures:
            player.send_message("§cNo structures configured for rewards.")
            return
        
        # Select structure
        if settings.get('randomize'):
            import random
            structure_file = random.choice(structures)
        elif streak_day <= len(structures):
            structure_file = structures[streak_day - 1]
        else:
            structure_file = structures[-1] if structures else None
        
        if not structure_file:
            player.send_message("§cNo structure available for this day.")
            return
        
        # Load structure at player location
        loc = player.location
        x, y, z = int(round(loc.x)), int(round(loc.y)), int(round(loc.z))
        
        self.plugin.server.dispatch_command(
            self.plugin.server.command_sender,
            f"structure load {structure_file} {x} {y} {z}"
        )
        
        player.send_message(f"§aYou have received a structure reward: {structure_file}.")
