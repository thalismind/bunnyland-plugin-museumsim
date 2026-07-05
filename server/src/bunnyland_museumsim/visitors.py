"""Visitors and tours — flavor, not admission accounting.

A collection that reads richly should feel *visited*. This module derives, purely from world
state, how much of a draw the museum a character stands in currently is, and turns that into a
couple of atmospheric prompt lines: a quiet gallery, a steady stream of visitors, or a guided
tour gathered around the star exhibits. There is no ticketing, no revenue, and no per-visitor
bookkeeping (that was cut from the roadmap) — the "crowd" is a deterministic function of what is
on display, so it never drifts under save/reload.
"""

from __future__ import annotations

from relics import Entity, World

from .authentication import FORGERY, verdict_of
from .collectibles import collectible_value
from .components import CollectibleComponent
from .display import displayed_pieces
from .museum import entity_name, museum_of
from .spatial import room_of

#: Total displayed value at or above which the gallery draws a steady stream of visitors.
BUSY_THRESHOLD = 200
#: Total displayed value at or above which a guided tour forms around the star pieces.
TOUR_THRESHOLD = 500


def visitor_interest(world: World, room: Entity) -> int:
    """Total appraised value on display in ``room``, ignoring exposed forgeries.

    A forgery no longer draws a crowd once it is unmasked, so it stops contributing to interest.
    """
    total = 0
    for piece in displayed_pieces(world, room):
        if verdict_of(piece) == FORGERY:
            continue
        total += collectible_value(piece.get_component(CollectibleComponent))
    return total


def visitor_fragments(world: World, character: Entity) -> list[str]:
    """Describe the crowd the museum a character stands in is drawing right now."""
    if character is None:
        return []
    room = room_of(world, character.id)
    if room is None or museum_of(room) is None:
        return []
    interest = visitor_interest(world, room)
    if interest <= 0:
        return []
    lines: list[str] = []
    if interest >= TOUR_THRESHOLD:
        pieces = [p for p in displayed_pieces(world, room) if verdict_of(p) != FORGERY]
        if pieces:
            star = entity_name(pieces[0])
            lines.append(f"A guided tour has gathered around {star}.")
        lines.append("The galleries are crowded with visitors today.")
    elif interest >= BUSY_THRESHOLD:
        lines.append("A steady stream of visitors moves through the galleries.")
    else:
        lines.append("A few visitors wander the quiet galleries.")
    return lines


__all__ = [
    "BUSY_THRESHOLD",
    "TOUR_THRESHOLD",
    "visitor_fragments",
    "visitor_interest",
]
