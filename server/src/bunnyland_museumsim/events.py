"""Domain events emitted by the donate and appraise verbs."""

from __future__ import annotations

from bunnyland.core.events import DomainEvent


class PieceDonatedEvent(DomainEvent):
    """A character donated a collectible to a museum."""

    item_id: str
    museum_id: str
    category: str
    rarity: str


class PieceAppraisedEvent(DomainEvent):
    """A character appraised a collectible, learning its category, rarity, and value."""

    item_id: str
    category: str
    rarity: str
    value: int


__all__ = ["PieceAppraisedEvent", "PieceDonatedEvent"]
