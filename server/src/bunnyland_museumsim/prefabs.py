"""Spawn factories for museum entities.

The loader does not consume ``ContentContribution.prefabs``, so museum pieces are built with
these ``spawn_entity`` helpers (from tests, admin tooling, or the worldgen hook). Collectible
items are portable and holdable; museums are rooms; exhibits and display cases are entities
that rest inside a museum room. Pass ``room_id`` to place a piece into a room, or leave it out
to spawn it loose.
"""

from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    HoldableComponent,
    IdentityComponent,
    PortableComponent,
    RoomComponent,
    spawn_entity,
)
from relics import Entity, World

from .authentication import AuthenticityComponent
from .components import CollectibleComponent, ExhibitComponent, MuseumComponent
from .display import DisplayCaseComponent
from .restoration import ConditionComponent


def _link_into_room(world: World, entity: Entity, room_id) -> None:
    if room_id is None or not world.has_entity(room_id):
        return
    world.get_entity(room_id).add_relationship(
        Contains(mode=ContainmentMode.ROOM_CONTENT), entity.id
    )


def spawn_collectible(
    world: World,
    *,
    room_id=None,
    name: str = "curio",
    category: str = "curio",
    rarity: str = "common",
    genuine: bool | None = None,
    condition: float | None = None,
) -> Entity:
    """Spawn a holdable collectible item, optionally placed in ``room_id``.

    Pass ``genuine`` to give the piece a hidden authenticity ground truth (so it can be
    authenticated as genuine or exposed as a forgery), and ``condition`` (``0.0``-``1.0``) to
    give it a physical condition below pristine (so it can be restored).
    """
    components = [
        IdentityComponent(name=name, kind="item", tags=("museumsim", "collectible")),
        PortableComponent(),
        HoldableComponent(slot="hand"),
        CollectibleComponent(category=category, rarity=rarity),
    ]
    if genuine is not None:
        components.append(AuthenticityComponent(genuine=genuine))
    if condition is not None:
        components.append(ConditionComponent(condition=condition))
    item = spawn_entity(world, components)
    _link_into_room(world, item, room_id)
    return item


def spawn_museum(world: World, *, name: str = "Museum", curator_id: str = "") -> Entity:
    """Spawn a room that acts as a museum, ready to accept donations."""
    return spawn_entity(
        world,
        [
            RoomComponent(title=name, indoor=True),
            MuseumComponent(name=name, curator_id=curator_id),
        ],
    )


def spawn_exhibit(
    world: World,
    *,
    room_id=None,
    category: str = "curio",
    required: tuple[str, ...] = (),
) -> Entity:
    """Spawn an exhibit entity collecting ``category``, optionally placed in ``room_id``."""
    exhibit = spawn_entity(
        world,
        [
            IdentityComponent(
                name=f"{category} exhibit", kind="exhibit", tags=("museumsim",)
            ),
            ExhibitComponent(category=category, required=tuple(sorted(dict.fromkeys(required)))),
        ],
    )
    _link_into_room(world, exhibit, room_id)
    return exhibit


def spawn_display_case(world: World, *, room_id=None, label: str = "display case") -> Entity:
    """Spawn a display case entity, optionally placed in ``room_id``."""
    case = spawn_entity(
        world,
        [
            IdentityComponent(name=label, kind="display-case", tags=("museumsim",)),
            DisplayCaseComponent(label=label),
        ],
    )
    _link_into_room(world, case, room_id)
    return case


def spawn_curator(world: World, *, room_id=None, name: str = "Curator") -> Entity:
    """Spawn a curator NPC, optionally placed in ``room_id``."""
    curator = spawn_entity(
        world,
        [
            IdentityComponent(name=name, kind="character", tags=("museumsim", "curator")),
            CharacterComponent(),
        ],
    )
    _link_into_room(world, curator, room_id)
    return curator


__all__ = [
    "spawn_collectible",
    "spawn_curator",
    "spawn_display_case",
    "spawn_exhibit",
    "spawn_museum",
]
