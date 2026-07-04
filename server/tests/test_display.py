from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    WorldActor,
    spawn_entity,
)

from bunnyland_museumsim import (
    displayed_pieces,
    museum_fragments,
    spawn_collectible,
    spawn_display_case,
    spawn_exhibit,
    spawn_museum,
)


def _character(world, room, name="Ada"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def test_no_fragments_outside_a_museum():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Street")])
    ada = _character(actor.world, room)

    assert museum_fragments(actor.world, ada) == []


def test_fragments_list_notable_pieces_and_a_tally():
    actor = WorldActor()
    room = spawn_museum(actor.world, name="City Museum")
    ada = _character(actor.world, room)
    spawn_exhibit(actor.world, room_id=room.id, category="fossil", required=("trilobite", "fern"))
    spawn_collectible(
        actor.world, room_id=room.id, name="Trilobite", category="fossil", rarity="legendary"
    )

    lines = museum_fragments(actor.world, ada)

    assert any("On display: Trilobite" in line for line in lines)
    assert any(line == "City Museum: 0 of 2 donated." for line in lines)


def test_tally_counts_donated_pieces():
    actor = WorldActor()
    room = spawn_museum(actor.world, name="City Museum")
    ada = _character(actor.world, room)
    exhibit = spawn_exhibit(
        actor.world, room_id=room.id, category="fossil", required=("trilobite", "fern")
    )
    from dataclasses import replace

    from bunnyland.core.ecs import replace_component

    from bunnyland_museumsim import ExhibitComponent

    replace_component(
        exhibit, replace(exhibit.get_component(ExhibitComponent), donated=("trilobite",))
    )

    lines = museum_fragments(actor.world, ada)

    assert any(line == "City Museum: 1 of 2 donated." for line in lines)


def test_notable_pieces_are_ordered_by_value():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    spawn_collectible(actor.world, room_id=room.id, name="Common Shell", rarity="common")
    spawn_collectible(actor.world, room_id=room.id, name="Rare Idol", rarity="legendary")

    pieces = displayed_pieces(actor.world, room)

    names = [p.get_component(IdentityComponent).name for p in pieces]
    assert names == ["Rare Idol", "Common Shell"]


def test_pieces_inside_a_display_case_are_counted_on_display():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    case = spawn_display_case(actor.world, room_id=room.id)
    piece = spawn_collectible(actor.world, name="Idol", category="relic")
    case.add_relationship(Contains(mode=ContainmentMode.CONTAINER), piece.id)

    pieces = displayed_pieces(actor.world, room)

    assert piece.id in {p.id for p in pieces}


def test_extra_pieces_are_summarised():
    actor = WorldActor()
    room = spawn_museum(actor.world, name="City Museum")
    ada = _character(actor.world, room)
    for index in range(5):
        spawn_collectible(actor.world, room_id=room.id, name=f"Piece {index}", rarity="common")

    lines = museum_fragments(actor.world, ada)

    assert any("more piece(s) on display" in line for line in lines)
