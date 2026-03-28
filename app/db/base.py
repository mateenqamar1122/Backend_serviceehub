"""
Base model for Supabase database operations.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID


class BaseModel:
    """
    Base model for Supabase database operations.
    All models should inherit from this.
    """

    def __init__(self, **kwargs):
        """Initialize model with provided kwargs."""
        self.created_at: Optional[datetime] = kwargs.get("created_at")
        self.updated_at: Optional[datetime] = kwargs.get("updated_at")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model instance from dictionary."""
        return cls(**data)

