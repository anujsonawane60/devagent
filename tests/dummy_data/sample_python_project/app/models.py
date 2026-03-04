"""Data models for the application."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class User:
    """Represents a user in the system."""
    id: int
    name: str
    email: str
    is_active: bool = True

    def full_name(self) -> str:
        """Return the user's full name."""
        return self.name

    def deactivate(self) -> None:
        """Deactivate the user account."""
        self.is_active = False


@dataclass
class Project:
    """Represents a project."""
    id: int
    title: str
    owner: User
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None

    def add_tag(self, tag: str) -> None:
        """Add a tag to the project."""
        if tag not in self.tags:
            self.tags.append(tag)

    def summary(self) -> str:
        """Return a brief summary of the project."""
        return f"{self.title} by {self.owner.name}"


def create_user(name: str, email: str) -> User:
    """Factory function to create a new user."""
    return User(id=0, name=name, email=email)
