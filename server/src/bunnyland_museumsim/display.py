"""Display cases and the museum's prompt fragments.

A :class:`DisplayCaseComponent` is a container entity resting in the museum room. Donated
pieces are tucked into a case when one is present, so a well-stocked museum reads richly:
``museum_fragments`` walks the room a character stands in and, if it is a museum, lists the
most notable pieces on display (highest appraised value first) plus a running "N of M
donated" tally.

The fragment provider is the shared ``(world, character) -> list[str]`` shape, so it feeds
both the LLM actor context and the human character-chat prompt. Lines are de-duplicated and
returned in a deterministic order.
"""

from __future__ import annotations

from bunnyland.core import contents
from pydantic.dataclasses import dataclass
from relics import Component, Entity, World

from .collectibles import collectible_value
from .components import CollectibleComponent
from .museum import donation_counts, entity_name, museum_of
from .spatial import room_of

#: How many notable pieces to name in a room description before summarising the rest.
MAX_NOTABLE = 3


@dataclass(frozen=True)
class DisplayCaseComponent(Component):
    """A case that holds donated pieces on display within a museum room."""

    label: str = "display case"


def display_case_in_room(world: World, room: Entity) -> Entity | None:
    """First display case resting in ``room`` (sorted by id), or ``None``."""
    cases: list[Entity] = []
    for entity_id in contents(room):
        if not world.has_entity(entity_id):
            continue
        entity = world.get_entity(entity_id)
        if entity.has_component(DisplayCaseComponent):
            cases.append(entity)
    cases.sort(key=lambda entity: str(entity.id))
    return cases[0] if cases else None


def displayed_pieces(world: World, room: Entity) -> list[Entity]:
    """Collectible entities on display in ``room`` — loose in it or inside its cases.

    Sorted by descending appraised value, then name, so the "notable" pieces come first and
    ties break deterministically.
    """
    pieces: list[Entity] = []
    for entity_id in contents(room):
        if not world.has_entity(entity_id):
            continue
        entity = world.get_entity(entity_id)
        if entity.has_component(CollectibleComponent):
            pieces.append(entity)
        elif entity.has_component(DisplayCaseComponent):
            for inner_id in contents(entity):
                if not world.has_entity(inner_id):
                    continue
                inner = world.get_entity(inner_id)
                if inner.has_component(CollectibleComponent):
                    pieces.append(inner)
    pieces.sort(
        key=lambda piece: (
            -collectible_value(piece.get_component(CollectibleComponent)),
            entity_name(piece),
        )
    )
    return pieces


def museum_fragments(world: World, character: Entity) -> list[str]:
    """Describe the museum a character stands in: notable pieces plus a donation tally."""
    if character is None:
        return []
    room = room_of(world, character.id)
    museum = museum_of(room)
    if room is None or museum is None:
        return []
    lines: list[str] = []
    pieces = displayed_pieces(world, room)
    for piece in pieces[:MAX_NOTABLE]:
        component = piece.get_component(CollectibleComponent)
        lines.append(
            f"On display: {entity_name(piece)} "
            f"(a {component.rarity} {component.category})."
        )
    extra = len(pieces) - MAX_NOTABLE
    if extra > 0:
        lines.append(f"...and {extra} more piece(s) on display.")
    donated, required = donation_counts(world, room)
    if required > 0:
        lines.append(f"{museum.name}: {donated} of {required} donated.")
    return lines


__all__ = [
    "MAX_NOTABLE",
    "DisplayCaseComponent",
    "display_case_in_room",
    "displayed_pieces",
    "museum_fragments",
]
