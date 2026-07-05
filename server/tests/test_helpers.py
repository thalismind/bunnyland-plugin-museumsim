"""Edge-branch coverage for the shared spatial, museum, and display helpers."""

from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    PortableComponent,
    RoomComponent,
    WorldActor,
    spawn_entity,
)

from bunnyland_museumsim import spawn_collectible, spawn_display_case, spawn_museum
from bunnyland_museumsim.display import (
    display_case_in_room,
    displayed_pieces,
    museum_fragments,
)
from bunnyland_museumsim.museum import entity_name, exhibit_for_category, museum_of
from bunnyland_museumsim.spatial import holder_of, room_of

# -- spatial ----------------------------------------------------------------------------


def test_holder_of_none_for_removed_or_loose_items():
    world = WorldActor().world
    ghost = spawn_entity(world, [IdentityComponent(name="ghost", kind="item")])
    ghost_id = ghost.id
    world.remove(ghost_id)
    assert holder_of(world, ghost_id) is None  # entity gone

    loose = spawn_entity(world, [IdentityComponent(name="loose", kind="item")])
    assert holder_of(world, loose.id) is None  # no container at all


def test_room_of_none_for_removed_entity():
    world = WorldActor().world
    ghost = spawn_entity(world, [IdentityComponent(name="ghost", kind="item")])
    ghost_id = ghost.id
    world.remove(ghost_id)
    assert room_of(world, ghost_id) is None


def test_room_of_gives_up_on_a_too_deep_chain():
    world = WorldActor().world
    # Build a chain of 10 nested containers with no room at the top; the walk is bounded.
    entities = [
        spawn_entity(world, [IdentityComponent(name=f"box{i}", kind="item"), PortableComponent()])
        for i in range(10)
    ]
    for outer, inner in zip(entities, entities[1:], strict=False):
        outer.add_relationship(Contains(mode=ContainmentMode.CONTAINER), inner.id)
    assert room_of(world, entities[-1].id) is None


# -- museum -----------------------------------------------------------------------------


def test_museum_of_none_for_missing_or_plain_rooms():
    world = WorldActor().world
    assert museum_of(None) is None
    plain = spawn_entity(world, [RoomComponent(title="Alley")])
    assert museum_of(plain) is None


def test_entity_name_falls_back_to_default():
    world = WorldActor().world
    nameless = spawn_entity(world, [PortableComponent()])
    assert entity_name(nameless) == "piece"
    assert entity_name(nameless, default="thing") == "thing"


def test_exhibit_for_category_returns_none_on_mismatch():
    world = WorldActor().world
    room = spawn_museum(world)
    from bunnyland_museumsim import spawn_exhibit

    spawn_exhibit(world, room_id=room.id, category="fossil", required=("bone",))
    assert exhibit_for_category(world, room, "art") is None


# -- display ----------------------------------------------------------------------------


def test_museum_fragments_none_without_a_character():
    assert museum_fragments(WorldActor().world, None) == []


def test_displayed_pieces_ignores_non_collectibles_in_a_case():
    world = WorldActor().world
    room = spawn_museum(world)
    case = spawn_display_case(world, room_id=room.id)
    # A non-collectible tucked into the case must not be listed as a displayed piece.
    trinket = spawn_entity(world, [IdentityComponent(name="mug", kind="item")])
    case.add_relationship(Contains(mode=ContainmentMode.CONTAINER), trinket.id)
    real = spawn_collectible(world, name="Vase", rarity="epic")
    case.add_relationship(Contains(mode=ContainmentMode.CONTAINER), real.id)

    assert display_case_in_room(world, room) is not None
    pieces = displayed_pieces(world, room)
    assert [entity_name(p) for p in pieces] == ["Vase"]  # only the real collectible
