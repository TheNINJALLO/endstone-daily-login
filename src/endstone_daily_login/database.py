"""
Database module for Daily Login plugin.
Provides JSON-based persistent storage, replacing the JavaScript dynamic properties system.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional, Iterator
from threading import Lock


class Database:
    """
    JSON-based database for persistent storage.
    Thread-safe with automatic file persistence.
    """
    
    def __init__(self, data_folder: Path, filename: str = "data.json"):
        """
        Initialize the database.
        
        Args:
            data_folder: Path to the plugin's data folder
            filename: Name of the JSON file to use
        """
        self._data_folder = Path(data_folder)
        self._filepath = self._data_folder / filename
        self._cache: dict[str, Any] = {}
        self._lock = Lock()
        self._load()
    
    def _load(self) -> None:
        """Load data from the JSON file."""
        if self._filepath.exists():
            try:
                with open(self._filepath, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache = {}
        else:
            self._cache = {}
    
    def _save(self) -> None:
        """Save data to the JSON file."""
        # Ensure directory exists
        self._data_folder.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self._filepath, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[DailyLogin] Error saving database: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value by key.
        
        Args:
            key: The key to look up
            default: Value to return if key doesn't exist
            
        Returns:
            The stored value or default
        """
        with self._lock:
            return self._cache.get(key, default)
    
    def set(self, key: str, value: Any) -> "Database":
        """
        Set a value by key.
        
        Args:
            key: The key to store under
            value: The value to store
            
        Returns:
            Self for chaining
        """
        with self._lock:
            self._cache[key] = value
            self._save()
        return self
    
    def delete(self, key: str) -> bool:
        """
        Delete a key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if key existed and was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._save()
                return True
            return False
    
    def has(self, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            key: The key to check
            
        Returns:
            True if key exists
        """
        with self._lock:
            return key in self._cache
    
    def clear(self) -> None:
        """Clear all data."""
        with self._lock:
            self._cache = {}
            self._save()
    
    @property
    def size(self) -> int:
        """Get the number of stored keys."""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> list[str]:
        """Get all keys."""
        with self._lock:
            return list(self._cache.keys())
    
    def values(self) -> list[Any]:
        """Get all values."""
        with self._lock:
            return list(self._cache.values())
    
    def entries(self) -> list[tuple[str, Any]]:
        """Get all key-value pairs."""
        with self._lock:
            return list(self._cache.items())
    
    def foreach(self, func: callable) -> None:
        """
        Execute a function for each entry.
        
        Args:
            func: Function taking (value, key, db) arguments
        """
        with self._lock:
            for key, value in self._cache.items():
                func(value, key, self)
    
    def __iter__(self) -> Iterator[tuple[str, Any]]:
        """Iterate over entries."""
        with self._lock:
            return iter(list(self._cache.items()))
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return self.has(key)
    
    def __len__(self) -> int:
        """Support len() function."""
        return self.size
