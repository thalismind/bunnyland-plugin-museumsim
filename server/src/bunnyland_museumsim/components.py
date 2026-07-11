"""Shared ECS state for the museum pack.

Three immutable components carry all persistent museum state:

- :class:`CollectibleComponent` is the **open opt-in tag** that any pack's item can carry
  (a fossil from a dig, a legendary fish, a spirit relic). It is defined *here*, in this
  package, so Museumsim never depends on the packs that produce collectibles — they depend
  on (or simply reuse) this component instead.
- :class:`MuseumComponent` lives on a room and holds the master donation ledger. Donated
  pieces are recorded as sorted, de-duplicated ``piece_key`` strings so duplicates are
  refused deterministically and the ledger survives save/reload.
- :class:`ExhibitComponent` lives on a per-category exhibit entity resting in the museum
  room. It lists the piece names it still wants and the ones already donated, and flips to
  ``completed`` once its wants are satisfied.

Components are frozen; every mutation swaps a whole value with
``replace_component(entity, replace(component, ...))``.
"""

from __future__ import annotations

from pydantic.dataclasses import dataclass
from relics import Component, Edge


@dataclass(frozen=True)
class CollectibleComponent(Component):
    """Marks an item as museum-worthy loot.

    ``category`` groups pieces into an exhibit ("fossil", "relic", "art", "fish", ...) and
    ``rarity`` is one of the tiers in :mod:`bunnyland_museumsim.collectibles`. Other packs
    attach this to their reward items to feed the shared museum sink.
    """

    category: str = "curio"
    rarity: str = "common"


@dataclass(frozen=True)
class MuseumComponent(Component):
    """A room that accepts donations. ``donated`` is the sorted piece-key ledger."""

    name: str = "Museum"
    donated: tuple[str, ...] = ()


@dataclass(frozen=True)
class MuseumHasCurator(Edge):
    """museum room -> curator character."""


@dataclass(frozen=True)
class ExhibitComponent(Component):
    """One category's collection goal, resting on an entity in the museum room."""

    category: str = "curio"
    required: tuple[str, ...] = ()
    donated: tuple[str, ...] = ()
    completed: bool = False
    last_donor_id: str = ""


__all__ = [
    "CollectibleComponent",
    "ExhibitComponent",
    "MuseumComponent",
    "MuseumHasCurator",
]
