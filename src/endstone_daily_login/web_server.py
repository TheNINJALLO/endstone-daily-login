"""
Web server module for Daily Login plugin.
Provides REST API and serves static web UI for remote configuration.
"""

import json
import threading
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse, parse_qs

if TYPE_CHECKING:
    from endstone_daily_login.daily_login import DailyLoginPlugin


# The dashboard stays disabled until the operator provides a secret at runtime.
WEB_PASSWORD = os.environ.get("ENDSTONE_DAILY_LOGIN_WEB_PASSWORD", "").strip()


class DailyLoginAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the Daily Login web API."""
    
    plugin: "DailyLoginPlugin" = None
    static_dir: Path = None
    
    def log_message(self, format, *args):
        """Override to use plugin logger."""
        if self.plugin:
            self.plugin.logger.info(f"[WebUI] {args[0]}")
    
    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_file(self, filepath: Path, content_type: str):
        """Send a static file."""
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, "File not found")
    
    def _check_auth(self) -> bool:
        """Check if request has valid authentication."""
        auth = self.headers.get("Authorization", "")
        if WEB_PASSWORD and auth.startswith("Bearer "):
            token = auth[7:]
            return token == WEB_PASSWORD
        return False
    
    def _read_body(self) -> dict:
        """Read and parse JSON body."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        try:
            return json.loads(body.decode())
        except json.JSONDecodeError:
            return {}
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # API routes
        if path.startswith("/api/"):
            if not self._check_auth():
                self._send_json({"error": "Unauthorized"}, 401)
                return
            
            if path == "/api/config":
                self._get_config()
            elif path == "/api/players":
                self._get_players()
            elif path == "/api/enchantments":
                self._get_enchantments()
            else:
                self._send_json({"error": "Not found"}, 404)
            return
        
        # Auth check endpoint (no auth required)
        if path == "/api/auth":
            query = parse_qs(parsed.query)
            password = query.get("password", [""])[0]
            if WEB_PASSWORD and password == WEB_PASSWORD:
                self._send_json({"success": True, "token": WEB_PASSWORD})
            else:
                self._send_json({"success": False}, 401)
            return
        
        # Static files
        self._serve_static(path)
    
    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path
        
        # Auth endpoint (no auth required)
        if path == "/api/auth":
            body = self._read_body()
            password = body.get("password", "")
            if WEB_PASSWORD and password == WEB_PASSWORD:
                self._send_json({"success": True, "token": WEB_PASSWORD})
            else:
                self._send_json({"success": False, "error": "Invalid password"}, 401)
            return
        
        if not self._check_auth():
            self._send_json({"error": "Unauthorized"}, 401)
            return
        
        body = self._read_body()
        
        if path == "/api/config/money":
            self._update_money_config(body)
        elif path == "/api/config/items":
            self._update_items_config(body)
        elif path == "/api/config/structures":
            self._update_structures_config(body)
        elif path == "/api/config/forms":
            self._update_forms_config(body)
        elif path == "/api/config/settings":
            self._update_settings(body)
        elif path == "/api/reload":
            self._reload_config()
        elif path.startswith("/api/players/") and path.endswith("/reset-claim"):
            player_name = path.split("/")[3]
            self._reset_player_claim(player_name)
        elif path.startswith("/api/players/") and path.endswith("/reset-streak"):
            player_name = path.split("/")[3]
            self._reset_player_streak(player_name)
        else:
            self._send_json({"error": "Not found"}, 404)
    
    def _serve_static(self, path: str):
        """Serve static files."""
        if path == "/" or path == "":
            path = "/index.html"
        
        # Security: prevent directory traversal
        safe_path = path.lstrip("/").replace("..", "")
        filepath = self.static_dir / safe_path
        
        if not filepath.exists() or not filepath.is_file():
            # Fallback to index.html for SPA routing
            filepath = self.static_dir / "index.html"
        
        # Determine content type
        ext = filepath.suffix.lower()
        content_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
        }
        content_type = content_types.get(ext, "application/octet-stream")
        
        self._send_file(filepath, content_type)
    
    # ========== API Handlers ==========
    
    def _get_config(self):
        """Get all configuration."""
        db = self.plugin.db
        config = {
            "money": db.get("moneyRewardSettings") or {"amounts": [1000], "randomize": False, "enabled": True},
            "items": db.get("itemRewardSettings") or {"items": [], "randomize": False, "enabled": False},
            "structures": db.get("structureRewardSettings") or {"structures": [], "randomize": False, "enabled": False},
            "forms": db.get("formsConfig") or {
                "adminItem": "minecraft:compass",
                "claimItem": "minecraft:stick",
                "entityTag": "daily_login",
                "interactionType": "Both"
            },
            "settings": db.get("rewardOptions") or {"currencyObj": "money"}
        }
        self._send_json(config)
    
    def _get_players(self):
        """Get all player data."""
        db = self.plugin.db
        players = []
        
        # Get all keys that look like player data
        for key in db.keys():
            data = db.get(key)
            if isinstance(data, dict) and "streak" in data:
                players.append({
                    "name": key,
                    "streak": data.get("streak", 0),
                    "longestStreak": data.get("longestStreak", 0),
                    "lastClaim": data.get("lastClaim", 0),
                    "lastLogin": data.get("lastLogin", 0)
                })
        
        self._send_json({"players": players})
    
    def _get_enchantments(self):
        """Get enchantment compatibility data."""
        from endstone_daily_login.enchantment_data import ENCHANTMENT_COMPATIBILITY, get_enchantment_display_name
        
        # Convert to a format suitable for the web UI
        result = {}
        for item_type, enchants in ENCHANTMENT_COMPATIBILITY.items():
            result[item_type] = [
                {"id": e, "name": get_enchantment_display_name(e)}
                for e in enchants
            ]
        
        self._send_json({"enchantments": result})
    
    def _update_money_config(self, body: dict):
        """Update money reward settings."""
        self.plugin.db.set("moneyRewardSettings", {
            "amounts": body.get("amounts", [1000]),
            "randomize": body.get("randomize", False),
            "enabled": body.get("enabled", True)
        })
        self._send_json({"success": True})
    
    def _update_items_config(self, body: dict):
        """Update item reward settings."""
        self.plugin.db.set("itemRewardSettings", {
            "items": body.get("items", []),
            "randomize": body.get("randomize", False),
            "enabled": body.get("enabled", False)
        })
        self._send_json({"success": True})
    
    def _update_structures_config(self, body: dict):
        """Update structure reward settings."""
        self.plugin.db.set("structureRewardSettings", {
            "structures": body.get("structures", []),
            "randomize": body.get("randomize", False),
            "enabled": body.get("enabled", False)
        })
        self._send_json({"success": True})
    
    def _update_forms_config(self, body: dict):
        """Update forms configuration."""
        self.plugin.db.set("formsConfig", {
            "adminItem": body.get("adminItem", "minecraft:compass"),
            "claimItem": body.get("claimItem", "minecraft:stick"),
            "entityTag": body.get("entityTag", "daily_login"),
            "interactionType": body.get("interactionType", "Both")
        })
        self._send_json({"success": True})
    
    def _update_settings(self, body: dict):
        """Update general settings."""
        self.plugin.db.set("rewardOptions", {
            "currencyObj": body.get("currencyObj", "money")
        })
        self._send_json({"success": True})
    
    def _reload_config(self):
        """Reload configuration from file."""
        self.plugin.db._load()
        self._send_json({"success": True, "message": "Configuration reloaded"})
    
    def _reset_player_claim(self, player_name: str):
        """Reset a player's claim."""
        data = self.plugin.db.get(player_name)
        if data:
            data["lastClaim"] = 0
            self.plugin.db.set(player_name, data)
            self._send_json({"success": True})
        else:
            self._send_json({"error": "Player not found"}, 404)
    
    def _reset_player_streak(self, player_name: str):
        """Reset a player's streak."""
        data = self.plugin.db.get(player_name)
        if data:
            data["streak"] = 0
            self.plugin.db.set(player_name, data)
            self._send_json({"success": True})
        else:
            self._send_json({"error": "Player not found"}, 404)


class WebServer:
    """Web server for Daily Login plugin."""
    
    def __init__(self, plugin: "DailyLoginPlugin", port: int = 8080):
        self.plugin = plugin
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        
        # Set up handler with plugin reference
        DailyLoginAPIHandler.plugin = plugin
        DailyLoginAPIHandler.static_dir = Path(__file__).parent / "static"
    
    def start(self):
        """Start the web server in a background thread."""
        if not WEB_PASSWORD:
            self.plugin.logger.warning(
                "Web UI disabled: set ENDSTONE_DAILY_LOGIN_WEB_PASSWORD before starting Endstone."
            )
            return False
        try:
            self.server = HTTPServer(("0.0.0.0", self.port), DailyLoginAPIHandler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            self.plugin.logger.info(f"Web UI started on http://0.0.0.0:{self.port}")
            return True
        except Exception as e:
            self.plugin.logger.error(f"Failed to start web server: {e}")
            return False
    
    def stop(self):
        """Stop the web server."""
        if self.server:
            self.server.shutdown()
            self.plugin.logger.info("Web UI stopped")
