"""Low-level museum lookups shared by the donate verb, exhibits, and display fragments.

Kept separate from any single mechanic so donation, exhibit-completion, and prompt rendering
can all resolve "the museum in this room" and "the exhibit for this category" without
importing each other. Every collection is sorted before it is returned so iteration order is
deterministic.
"""

from __future__ import annotations

from bunnyland.core import IdentityComponent, contents
from relics import Entity, World

from .components import ExhibitComponent, MuseumComponent


def museum_of(room: Entity | None) -> MuseumComponent | None:
    """The :class:`MuseumComponent` on ``room``, or ``None`` if it is not a museum."""
    if room is None or not room.has_component(MuseumComponent):
        return None
    return room.get_component(MuseumComponent)


def exhibits_in_room(world: World, room: Entity) -> list[Entity]:
    """Exhibit entities resting in ``room``, sorted by id for deterministic iteration."""
    found: list[Entity] = []
    for entity_id in contents(room):
        if not world.has_entity(entity_id):
            continue
        entity = world.get_entity(entity_id)
        if entity.has_component(ExhibitComponent):
            found.append(entity)
    found.sort(key=lambda entity: str(entity.id))
    return found


def exhibit_for_category(world: World, room: Entity, category: str) -> Entity | None:
    """First exhibit in ``room`` collecting ``category``, or ``None``."""
    for exhibit in exhibits_in_room(world, room):
        if exhibit.get_component(ExhibitComponent).category == category:
            return exhibit
    return None


def entity_name(entity: Entity, default: str = "piece") -> str:
    """Display name of ``entity`` from its identity, or ``default``."""
    if entity.has_component(IdentityComponent):
        return entity.get_component(IdentityComponent).name
    return default


def donation_counts(world: World, room: Entity) -> tuple[int, int]:
    """Return ``(donated, required)`` totals across every exhibit in ``room``.

    ``required`` is the number of distinct wanted pieces; ``donated`` is how many of those
    wants are satisfied, so the pair reads naturally as "N of M donated".
    """
    donated = 0
    required = 0
    for exhibit in exhibits_in_room(world, room):
        component = exhibit.get_component(ExhibitComponent)
        wanted = set(component.required)
        required += len(wanted)
        donated += len(wanted & set(component.donated))
    return donated, required


__all__ = [
    "donation_counts",
    "entity_name",
    "exhibit_for_category",
    "exhibits_in_room",
    "museum_of",
]
