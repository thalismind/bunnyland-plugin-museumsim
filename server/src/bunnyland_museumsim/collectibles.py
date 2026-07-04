"""Collectible tags: rarity tiers, appraised value, and piece identity.

The rarity ladder is a fixed, ordered vocabulary so ranking and value are deterministic and
stable under save/reload. A collectible's *value* is a pure function of its rarity, and its
*piece key* — the identity a museum de-duplicates on — is a pure function of its category
and name. Keeping all of this here (rather than on the frozen component) lets the component
stay a plain data tag that any other pack can attach without importing museum logic.
"""

from __future__ import annotations

from .components import CollectibleComponent

#: Rarity tiers in ascending order; the index is the rank.
RARITIES: tuple[str, ...] = ("common", "uncommon", "rare", "epic", "legendary")

#: Appraised value per rarity tier. Unknown rarities appraise at ``0``.
RARITY_VALUES: dict[str, int] = {
    "common": 10,
    "uncommon": 25,
    "rare": 75,
    "epic": 200,
    "legendary": 500,
}


def rarity_rank(rarity: str) -> int:
    """Ascending rank of a rarity (``common`` is ``0``); ``-1`` for an unknown tier."""
    try:
        return RARITIES.index(rarity)
    except ValueError:
        return -1


def collectible_value(component: CollectibleComponent) -> int:
    """Appraised value of a collectible, from its rarity tier."""
    return RARITY_VALUES.get(component.rarity, 0)


def piece_key(category: str, name: str) -> str:
    """Stable identity a museum de-duplicates on: ``category/name`` (case-folded)."""
    return f"{category.strip().casefold()}/{name.strip().casefold()}"


def collectible_piece_key(component: CollectibleComponent, name: str) -> str:
    """Piece key for a collectible ``component`` displayed under ``name``."""
    return piece_key(component.category, name)


__all__ = [
    "RARITIES",
    "RARITY_VALUES",
    "collectible_piece_key",
    "collectible_value",
    "piece_key",
    "rarity_rank",
]
