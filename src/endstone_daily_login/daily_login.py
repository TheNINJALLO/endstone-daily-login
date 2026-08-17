"""
Daily Login Plugin for Endstone.
Provides daily login rewards with streak tracking for Minecraft Bedrock servers.

Ported from the original JavaScript Daily Login 2.7 by LEEFY.
"""

from pathlib import Path
from typing import Optional

from endstone import Player
from endstone.plugin import Plugin
from endstone.command import Command, CommandSender
from endstone.event import event_handler, PlayerJoinEvent, PlayerQuitEvent, PlayerInteractEvent, PlayerInteractActorEvent, ActorKnockbackEvent

from endstone_daily_login.database import Database
from endstone_daily_login.utils import get_current_time_ms, calculate_average


class DailyLoginPlugin(Plugin):
    """Daily Login rewards plugin for Endstone servers."""
    
    api_version = "0.11"
    
    # Plugin metadata
    
    version = "2.7.2"
    description = "Daily login rewards with streak tracking"
    authors = ["LEEFY", "Endstone Port"]
    
    # Commands
    commands = {
        "dailylogin": {
            "description": "Open daily login admin panel",
            "usages": ["/dailylogin"],
            "permissions": ["dailylogin.admin"],
            "aliases": ["dl", "dailyreward"]
        }
    }
    
    # Permissions
    permissions = {
        "dailylogin.admin": {
            "description": "Access to daily login admin panel",
            "default": "op"
        }
    }
    
    def __init__(self):
        super().__init__()
        self.db: Optional[Database] = None
        self.web_server = None
        self._interact_cooldowns: dict[str, float] = {}  # Player name -> last interact time
        self._hit_cooldowns: dict[str, float] = {}  # Player name -> last hit time (for entity hit)
    
    def on_load(self) -> None:
        """Called when the plugin is loaded."""
        self.logger.info("Daily Login plugin loading...")
    
    def on_enable(self) -> None:
        """Called when the plugin is enabled."""
        # Initialize database
        data_folder = Path(self.data_folder)
        self.db = Database(data_folder, "daily_login_data.json")
        
        # Register event listeners
        self.register_events(self)
        
        # Start web server
        try:
            from endstone_daily_login.web_server import WebServer
            self.web_server = WebServer(self, port=25689)
            if self.web_server.start():
                self.logger.info("Web UI available at http://0.0.0.0:25689")
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
        
        self.logger.info("Daily Login plugin enabled!")
        self.logger.info(f"Data folder: {data_folder}")
    
    def on_disable(self) -> None:
        """Called when the plugin is disabled."""
        # Stop web server
        if self.web_server:
            try:
                self.web_server.stop()
            except Exception:
                pass
        self.logger.info("Daily Login plugin disabled!")
    
    # ========== Command Handling ==========
    
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        """Handle plugin commands."""
        if command.name.lower() in ["dailylogin", "dl", "dailyreward"]:
            if not isinstance(sender, Player):
                sender.send_message("§cThis command can only be used by players.")
                return True
            
            player: Player = sender
            
            if not player.is_op:
                player.send_message("§cYou don't have permission to use this command.")
                return True
            
            # Open admin panel
            from endstone_daily_login.forms.admin_forms import AdminForms
            AdminForms(self).open_admin_panel(player)
            return True
        
        return False
    
    # ========== Event Handlers ==========
    
    @event_handler
    def on_player_join(self, event: PlayerJoinEvent) -> None:
        """Handle player join - initialize player data."""
        player = event.player
        self._initialize_player(player)
    
    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent) -> None:
        """Handle player quit - save session data."""
        player = event.player
        self._calculate_session_duration(player)
        self._save_logout_location(player)
    
    @event_handler
    def on_player_interact(self, event: PlayerInteractEvent) -> None:
        """Handle item use for opening forms."""
        player = event.player
        item = event.item
        
        if item is None:
            return
        
        # Cooldown check (1 second)
        import time
        now = time.time()
        last_interact = self._interact_cooldowns.get(player.name, 0)
        if now - last_interact < 1.0:
            return
        self._interact_cooldowns[player.name] = now
        
        config = self.db.get('formsConfig') or {
            'adminItem': 'minecraft:compass',
            'claimItem': 'minecraft:stick'
        }
        
        item_type = item.type.id if hasattr(item.type, 'id') else str(item.type)
        
        # Check for admin item
        if item_type == config.get('adminItem', 'minecraft:compass'):
            if player.is_op:
                from endstone_daily_login.forms.admin_forms import AdminForms
                AdminForms(self).open_admin_panel(player)
        
        # Check for claim item
        elif item_type == config.get('claimItem', 'minecraft:stick'):
            player_data = self._initialize_player(player)
            from endstone_daily_login.forms.reward_forms import RewardForms
            RewardForms(self).open_claim_form(player, player_data)
    
    @event_handler
    def on_player_interact_actor(self, event: PlayerInteractActorEvent) -> None:
        """Handle entity interaction for opening claim form."""
        player = event.player
        actor = event.actor
        
        config = self.db.get('formsConfig') or {
            'entityTag': 'daily_login',
            'interactionType': 'Both'
        }
        
        entity_tag = config.get('entityTag', 'daily_login')
        interaction_type = config.get('interactionType', 'Both')
        
        # Check if entity has the required tag
        if not entity_tag:
            return
        
        # Check if the actor has the configured tag using scoreboard_tags
        has_tag = False
        try:
            # Primary method: scoreboard_tags attribute (list of strings)
            if hasattr(actor, 'scoreboard_tags'):
                has_tag = entity_tag in actor.scoreboard_tags
            else:
                # Fallback: try tags attribute
                has_tag = entity_tag in getattr(actor, 'tags', [])
        except Exception as e:
            self.logger.warning(f"Failed to check entity tags: {e}")
            has_tag = False
        
        if has_tag:
            if interaction_type in ['Interact', 'Both']:
                # Cancel the event to prevent NPC menu from opening
                event.cancel()
                player_data = self._initialize_player(player)
                from endstone_daily_login.forms.reward_forms import RewardForms
                RewardForms(self).open_claim_form(player, player_data)
    
    @event_handler
    def on_actor_knockback(self, event: ActorKnockbackEvent) -> None:
        """Handle entity hit for opening claim form (Hit mode)."""
        # Only trigger if a player caused the knockback
        source = event.source
        if source is None:
            return
        
        # Check if source is a player
        if not isinstance(source, Player):
            return
        player = source
        
        # Cooldown check (1 second) to prevent spam
        import time
        now = time.time()
        last_hit = self._hit_cooldowns.get(player.name, 0)
        if now - last_hit < 1.0:
            return
        self._hit_cooldowns[player.name] = now
        
        actor = event.actor
        
        config = self.db.get('formsConfig') or {
            'entityTag': 'daily_login',
            'interactionType': 'Both'
        }
        
        entity_tag = config.get('entityTag', 'daily_login')
        interaction_type = config.get('interactionType', 'Both')
        
        if not entity_tag:
            return
        
        # Check if the actor has the configured tag using scoreboard_tags
        has_tag = False
        try:
            if hasattr(actor, 'scoreboard_tags'):
                has_tag = entity_tag in actor.scoreboard_tags
            else:
                has_tag = entity_tag in getattr(actor, 'tags', [])
        except Exception as e:
            self.logger.warning(f"Failed to check entity tags (hit): {e}")
            has_tag = False
        
        if has_tag:
            if interaction_type in ['Hit', 'Both']:
                player_data = self._initialize_player(player)
                from endstone_daily_login.forms.reward_forms import RewardForms
                RewardForms(self).open_claim_form(player, player_data)
    
    # ========== Player Data Management ==========
    
    def _initialize_player(self, player: Player) -> dict:
        """
        Initialize or update player data on login.
        
        Args:
            player: The player to initialize
            
        Returns:
            The player's data dictionary
        """
        player_data = self.db.get(player.name)
        now = get_current_time_ms()
        
        # Get server's timezone offset
        server_offset = 0  # Default to UTC
        
        if player_data is None:
            # New player
            player_data = {
                'lastClaim': 0,
                'streak': 0,
                'longestStreak': 0,
                'loginDates': [],
                'sessionDurations': [],
                'lastLogin': now,
                'sessionStart': now,
                'timezoneOffset': server_offset
            }
        else:
            # Returning player - check for missed day
            last_login = player_data.get('lastLogin', 0)
            missed_a_day = now - last_login > (24 * 60 * 60 * 1000)  # More than 24 hours
            
            if missed_a_day:
                player_data['streak'] = 0
                player.send_message("§cYou have missed a day. Your streak has been reset to 0.")
            
            # Update login data
            player_data['lastLogin'] = now
            player_data['sessionStart'] = now
            
            # Ensure sessionDurations is a list
            if not isinstance(player_data.get('sessionDurations'), list):
                player_data['sessionDurations'] = []
            
            # Update timezone if not set
            if 'timezoneOffset' not in player_data:
                player_data['timezoneOffset'] = server_offset
        
        # Save updated data
        self.db.set(player.name, player_data)
        
        return player_data
    
    def _calculate_session_duration(self, player: Player) -> None:
        """
        Calculate and save session duration when player leaves.
        
        Args:
            player: The player who is leaving
        """
        player_data = self.db.get(player.name)
        
        if player_data and player_data.get('sessionStart'):
            session_end = get_current_time_ms()
            session_duration = session_end - player_data['sessionStart']
            
            # Add duration to the list (most recent first)
            durations = player_data.get('sessionDurations', [])
            if not isinstance(durations, list):
                durations = []
            
            durations.insert(0, session_duration)
            
            # Keep only last 30 sessions
            if len(durations) > 30:
                durations = durations[:30]
            
            player_data['sessionDurations'] = durations
            
            # Calculate average
            player_data['averageSessionDuration'] = calculate_average(durations)
            
            # Update last logout time
            player_data['lastLogout'] = session_end
            
            # Update longest streak if current is higher
            current_streak = player_data.get('streak', 0)
            longest_streak = player_data.get('longestStreak', 0)
            if current_streak > longest_streak:
                player_data['longestStreak'] = current_streak
            
            # Clean up session start
            del player_data['sessionStart']
            
            # Save
            self.db.set(player.name, player_data)
    
    def _save_logout_location(self, player: Player) -> None:
        """
        Save the player's logout location.
        
        Args:
            player: The player who is leaving
        """
        player_data = self.db.get(player.name) or {}
        
        try:
            loc = player.location
            player_data['lastLogoutLocation'] = {
                'x': int(round(loc.x)),
                'y': int(round(loc.y)),
                'z': int(round(loc.z))
            }
            self.db.set(player.name, player_data)
        except Exception as e:
            self.logger.warning(f"Failed to save logout location for {player.name}: {e}")
