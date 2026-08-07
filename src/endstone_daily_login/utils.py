"""
Utility functions for Daily Login plugin.
Ported from the original JavaScript functions.js
"""

from typing import Union
from datetime import datetime, timezone, timedelta


def metric_numbers(value: Union[int, float]) -> str:
    """
    Format large numbers with K/M/B/T suffixes.
    
    Args:
        value: The number to format
        
    Returns:
        Formatted string (e.g., "1.5M")
    """
    if value < 1000:
        return str(int(value))
    
    suffixes = ["", "K", "M", "B", "T", "P", "E", "Z", "Y"]
    
    import math
    magnitude = int(math.log10(value) / 3)
    magnitude = min(magnitude, len(suffixes) - 1)
    
    scaled = value / (10 ** (magnitude * 3))
    return f"{scaled:.1f}{suffixes[magnitude]}"


def format_with_commas(value: Union[int, float]) -> str:
    """
    Format a number with comma separators.
    
    Args:
        value: The number to format
        
    Returns:
        Formatted string (e.g., "1,000,000")
    """
    return f"{int(value):,}"


def format_duration(ms: int) -> str:
    """
    Format milliseconds into a human-readable duration string.
    
    Args:
        ms: Duration in milliseconds
        
    Returns:
        Formatted string (e.g., "2 hrs, 30 mins")
    """
    if ms == 0:
        return "Less than a minute"
    
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    hours = int((ms / (1000 * 60 * 60)) % 24)
    days = int(ms / (1000 * 60 * 60 * 24))
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hr{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} min{'s' if minutes > 1 else ''}")
    if seconds > 0 and not parts:  # Only show seconds if nothing else
        parts.append(f"{seconds} sec{'s' if seconds > 1 else ''}")
    
    return ", ".join(parts) if parts else "Less than a minute"


def get_current_time_ms() -> int:
    """
    Get current time in milliseconds since epoch.
    
    Returns:
        Current timestamp in milliseconds
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def format_time_for_timezone(timestamp_ms: int, offset_hours: int) -> str:
    """
    Format a timestamp for a specific timezone offset.
    
    Args:
        timestamp_ms: Timestamp in milliseconds
        offset_hours: Timezone offset in hours from UTC
        
    Returns:
        Formatted datetime string
    """
    dt = datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc)
    adjusted = dt + timedelta(hours=offset_hours)
    return adjusted.strftime("%Y-%m-%d %H:%M:%S")


def get_time_remaining_string(target_ms: int) -> str:
    """
    Get a formatted string for time remaining until a target timestamp.
    
    Args:
        target_ms: Target timestamp in milliseconds
        
    Returns:
        Formatted string (e.g., "5h 30m 15s")
    """
    now = get_current_time_ms()
    remaining = target_ms - now
    
    if remaining <= 0:
        return "0s"
    
    hours = int(remaining / (1000 * 60 * 60))
    minutes = int((remaining % (1000 * 60 * 60)) / (1000 * 60))
    seconds = int((remaining % (1000 * 60)) / 1000)
    
    return f"{hours}h {minutes}m {seconds}s"


def calculate_average(values: list[Union[int, float]]) -> float:
    """
    Calculate the average of a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Average value or 0 if list is empty
    """
    if not values:
        return 0.0
    return sum(values) / len(values)


def is_tool_or_armor(item_type: str) -> bool:
    """
    Check if an item type is a tool or armor that can have enchantments.
    
    Args:
        item_type: Minecraft item type string (e.g., "minecraft:diamond_sword")
        
    Returns:
        True if the item can have enchantments
    """
    from endstone_daily_login.enchantment_data import ENCHANTMENT_COMPATIBILITY
    return item_type in ENCHANTMENT_COMPATIBILITY


def get_display_text(value, default_text: str, formatter=None) -> str:
    """
    Get display text for a value, with optional formatting.
    
    Args:
        value: The value to display
        default_text: Text to show if value is None/undefined
        formatter: Optional function to format the value
        
    Returns:
        Formatted string
    """
    if value is None:
        return default_text
    return formatter(value) if formatter else str(value)
