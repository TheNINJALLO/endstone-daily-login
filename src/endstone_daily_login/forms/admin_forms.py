"""
Admin panel forms for Daily Login plugin.
Provides administrator interface for managing the plugin.
"""

from typing import TYPE_CHECKING
import json
from datetime import datetime, timezone, timedelta
from endstone import Player
from endstone.form import ActionForm, ModalForm, Toggle, TextInput, Dropdown, Slider, Label, Button

from endstone_daily_login.utils import (
    format_duration,
    format_time_for_timezone,
    get_current_time_ms,
    format_with_commas,
    get_display_text,
)

if TYPE_CHECKING:
    from endstone_daily_login.daily_login import DailyLoginPlugin


class AdminForms:
    """Admin panel forms for plugin configuration."""
    
    def __init__(self, plugin: "DailyLoginPlugin"):
        self.plugin = plugin
        self.db = plugin.db
    
    # ========== Main Admin Panel ==========
    
    def open_admin_panel(self, player: Player) -> None:
        """Open the main admin panel."""
        # Get admin's timezone for display
        admin_data = self.db.get(player.name) or {}
        admin_offset = admin_data.get('timezoneOffset', 0)
        
        # Calculate current time in admin's timezone
        now = datetime.now(timezone.utc)
        adjusted = now + timedelta(hours=admin_offset)
        formatted_time = adjusted.strftime("%H:%M")
        
        timezone_label = f"Set Timezone (Current Time: {formatted_time})"
        
        def on_submit(p: Player, selection: int):
            if selection == 0:
                self.show_players_list(player)
            elif selection == 1:
                from endstone_daily_login.forms.reward_forms import RewardForms
                RewardForms(self.plugin).open_reward_settings(player)
            elif selection == 2:
                self.open_timezone_settings(player)
            elif selection == 3:
                self.open_forms_config(player)
            elif selection == 4:
                self.open_money_objective_config(player)
        
        form = ActionForm(
            title="Daily Login - Admin Panel",
            content="Manage Daily Login",
            buttons=[
                Button(text="Manage Players"),
                Button(text="Reward Settings"),
                Button(text=timezone_label),
                Button(text="Set Item/Entity Config"),
                Button(text="Money Objective"),
            ],
            on_submit=on_submit
        )
        
        player.send_form(form)
    
    # ========== Player Management ==========
    
    def show_players_list(self, player: Player) -> None:
        """Show a list of online players to manage."""
        online_players = list(self.plugin.server.online_players)
        
        if not online_players:
            player.send_message("§cNo players online.")
            self.open_admin_panel(player)
            return
        
        player_names = [p.name for p in online_players]
        
        controls = [
            Dropdown(label="Select Player", options=player_names)
        ]
        
        def on_submit(p: Player, response: str):
            try:
                values = json.loads(response)
                selected_index = int(values[0])
                selected_name = player_names[selected_index]
                self.show_player_stats(player, selected_name)
            except (json.JSONDecodeError, TypeError, IndexError, ValueError):
                player.send_message("§cError selecting player.")
                self.open_admin_panel(player)
        
        form = ModalForm(
            title="Manage Players",
            controls=controls,
            submit_button="View Stats",
            on_submit=on_submit,
            on_close=lambda p: self.open_admin_panel(player)
        )
        
        player.send_form(form)
    
    def show_player_stats(self, admin: Player, target_name: str) -> None:
        """Show stats for a specific player."""
        player_data = self.db.get(target_name)
        
        if not player_data:
            admin.send_message(f"§cNo data found for {target_name}.")
            self.show_players_list(admin)
            return
        
        # Get admin's timezone offset
        admin_data = self.db.get(admin.name) or {}
        admin_offset = admin_data.get('timezoneOffset', 0)
        
        # Format stats
        streak = player_data.get('streak', 0)
        longest_streak = get_display_text(player_data.get('longestStreak'), "still calculating...")
        avg_session = get_display_text(
            player_data.get('averageSessionDuration'), 
            "still calculating...",
            format_duration
        )
        
        last_login = player_data.get('lastLogin')
        last_login_str = format_time_for_timezone(last_login, admin_offset) if last_login else "N/A"
        
        last_logout = player_data.get('lastLogout')
        last_login_time = player_data.get('lastLogin', 0)
        
        # Check if player is online (lastLogout < lastLogin means they haven't logged out since)
        is_online = last_logout and last_login_time and last_logout < last_login_time
        
        if is_online:
            now = get_current_time_ms()
            session_duration = format_duration(now - last_login_time)
            last_logout_str = f"§aOnline§f (Active {session_duration})"
        else:
            last_logout_str = format_time_for_timezone(last_logout, admin_offset) if last_logout else "N/A"
        
        # Format logout location
        logout_loc = player_data.get('lastLogoutLocation')
        if logout_loc:
            loc_str = f"X: {logout_loc.get('x', 0)}, Y: {logout_loc.get('y', 0)}, Z: {logout_loc.get('z', 0)}"
        else:
            loc_str = "N/A"
        
        stats_body = (
            f"Current Login Streak: {streak}\n"
            f"Longest Streak: {longest_streak}\n"
            f"Average Session: {avg_session}\n"
            f"Last Login: {last_login_str}\n"
            f"Last Log: {last_logout_str}\n"
            f"Last Log Loc: {loc_str}"
        )
        
        def on_submit(p: Player, selection: int):
            if selection == 0:
                self.show_players_list(admin)
            elif selection == 1:
                self._reset_player_claim(admin, target_name)
            elif selection == 2:
                self._reset_player_streak(admin, target_name)
            elif selection == 3:
                self._simulate_missed_day(admin, target_name)
        
        form = ActionForm(
            title=f"{target_name} Stats",
            content=stats_body,
            buttons=[
                Button(text="Back"),
                Button(text="Allow to claim daily again"),
                Button(text="Reset Streak"),
                Button(text="Simulate Missed Day"),
            ],
            on_submit=on_submit,
            on_close=lambda p: self.show_players_list(admin)
        )
        
        admin.send_form(form)
    
    def _reset_player_claim(self, admin: Player, target_name: str) -> None:
        """Reset a player's last claim time."""
        player_data = self.db.get(target_name)
        if player_data:
            player_data['lastClaim'] = 0
            self.db.set(target_name, player_data)
            admin.send_message(f"§aReset daily claim for {target_name}.")
        else:
            admin.send_message(f"§cNo data found for {target_name}.")
        
        self.show_player_stats(admin, target_name)
    
    def _reset_player_streak(self, admin: Player, target_name: str) -> None:
        """Reset a player's streak."""
        player_data = self.db.get(target_name)
        if player_data:
            player_data['streak'] = 0
            self.db.set(target_name, player_data)
            admin.send_message(f"§aReset streak for {target_name}.")
        else:
            admin.send_message(f"§cNo data found for {target_name}.")
        
        self.show_player_stats(admin, target_name)
    
    def _simulate_missed_day(self, admin: Player, target_name: str) -> None:
        """Simulate a missed day for a player."""
        player_data = self.db.get(target_name)
        if player_data:
            now = get_current_time_ms()
            player_data['lastLogin'] = now - (25 * 60 * 60 * 1000)  # 25 hours ago
            player_data['streak'] = 0
            self.db.set(target_name, player_data)
            admin.send_message(f"§aSimulated missed day for {target_name}.")
        else:
            admin.send_message(f"§cNo data found for {target_name}.")
        
        self.show_player_stats(admin, target_name)
    
    # ========== Timezone Settings ==========
    
    def open_timezone_settings(self, player: Player) -> None:
        """Open timezone settings form."""
        player_data = self.db.get(player.name) or {}
        current_offset = player_data.get('timezoneOffset', 0)
        
        controls = [
            Slider(
                label="Select Your Timezone Offset (UTC)",
                min=-12,
                max=14,
                step=1,
                default_value=float(current_offset)
            )
        ]
        
        def on_submit(p: Player, response: str):
            try:
                values = json.loads(response)
                offset = int(float(values[0]))
                
                data = self.db.get(player.name) or {}
                data['timezoneOffset'] = offset
                self.db.set(player.name, data)
                
                sign = "+" if offset >= 0 else ""
                player.send_message(f"§aYour timezone offset has been set to UTC{sign}{offset}.")
            except (json.JSONDecodeError, TypeError, ValueError):
                player.send_message("§cError saving timezone setting.")
            
            self.open_admin_panel(player)
        
        form = ModalForm(
            title="Timezone Settings",
            controls=controls,
            submit_button="Save",
            on_submit=on_submit,
            on_close=lambda p: self.open_admin_panel(player)
        )
        
        player.send_form(form)
    
    # ========== Forms Configuration ==========
    
    def open_forms_config(self, player: Player) -> None:
        """Open the forms configuration dialog."""
        config = self.db.get('formsConfig') or {
            'adminItem': 'minecraft:compass',
            'claimItem': 'minecraft:stick',
            'entityTag': 'daily_login',
            'interactionType': 'Both'
        }
        
        interaction_types = ['Hit', 'Interact', 'Both']
        current_interaction = config.get('interactionType', 'Both')
        try:
            interaction_index = interaction_types.index(current_interaction)
        except ValueError:
            interaction_index = 2  # Default to 'Both'
        
        controls = [
            TextInput(
                label="Open Admin Form [Required]",
                placeholder="Item ID",
                default_value=config.get('adminItem', 'minecraft:compass')
            ),
            TextInput(
                label="Open Daily Claim [empty = none]",
                placeholder="Item ID",
                default_value=config.get('claimItem', 'minecraft:stick')
            ),
            TextInput(
                label="Entity Tag [empty = none]",
                placeholder="e.g., daily_login",
                default_value=config.get('entityTag', 'daily_login')
            ),
            Dropdown(
                label="Interaction/Slapper Type",
                options=interaction_types,
                default_index=interaction_index
            )
        ]
        
        def on_submit(p: Player, response: str):
            try:
                values = json.loads(response)
                
                admin_item = str(values[0]).strip() or 'minecraft:compass'
                claim_item = str(values[1]).strip() if values[1] else ''
                entity_tag = str(values[2]).strip() if values[2] else ''
                interaction_type = interaction_types[int(values[3])]
                
                new_config = {
                    'adminItem': admin_item,
                    'claimItem': claim_item,
                    'entityTag': entity_tag,
                    'interactionType': interaction_type
                }
                
                self.db.set('formsConfig', new_config)
                self.db.set('itemConfig', {'adminItem': admin_item, 'claimItem': claim_item})
                
                player.send_message(
                    f"§aConfig updated: Admin Item - {admin_item}, "
                    f"Claim Item - {claim_item or 'none'}, "
                    f"Entity Tag - {entity_tag or 'none'}, "
                    f"Interaction Type - {interaction_type}"
                )
            except (json.JSONDecodeError, TypeError, ValueError, IndexError):
                player.send_message("§cError saving configuration.")
            
            self.open_admin_panel(player)
        
        form = ModalForm(
            title="Open Forms Configuration",
            controls=controls,
            submit_button="Save",
            on_submit=on_submit,
            on_close=lambda p: self.open_admin_panel(player)
        )
        
        player.send_form(form)
    
    # ========== Money Objective Configuration ==========
    
    def open_money_objective_config(self, player: Player) -> None:
        """Open the money objective configuration dialog."""
        config = self.db.get('rewardOptions') or {'currencyObj': 'money'}
        
        controls = [
            TextInput(
                label="Scoreboard Objective Name",
                placeholder="Enter scoreboard object name",
                default_value=config.get('currencyObj', 'money')
            )
        ]
        
        def on_submit(p: Player, response: str):
            try:
                values = json.loads(response)
                new_obj = str(values[0]).strip()
                
                if new_obj:
                    current = self.db.get('rewardOptions') or {}
                    current['currencyObj'] = new_obj
                    self.db.set('rewardOptions', current)
                    player.send_message(f"§aMoney object updated to: {new_obj}")
                else:
                    player.send_message("§cYou must enter a name for the money object.")
            except (json.JSONDecodeError, TypeError):
                player.send_message("§cError saving money objective.")
            
            self.open_admin_panel(player)
        
        form = ModalForm(
            title="Edit Money Objective",
            controls=controls,
            submit_button="Save",
            on_submit=on_submit,
            on_close=lambda p: self.open_admin_panel(player)
        )
        
        player.send_form(form)
