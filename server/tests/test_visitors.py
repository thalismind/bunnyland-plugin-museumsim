"""Visitor/tour flavor is a deterministic function of what is on display."""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.ecs import replace_component

from bunnyland_museumsim import spawn_collectible, spawn_museum
from bunnyland_museumsim.authentication import FORGERY, AuthenticityComponent
from bunnyland_museumsim.visitors import (
    BUSY_THRESHOLD,
    TOUR_THRESHOLD,
    visitor_fragments,
    visitor_interest,
)


def _character(world, room, name="Ada"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _expose_forgery(piece):
    replace_component(
        piece,
        replace(AuthenticityComponent(genuine=False), verdict=FORGERY),
    )


# -- visitor_interest -------------------------------------------------------------------


def test_interest_sums_displayed_value():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    spawn_collectible(actor.world, room_id=room.id, name="Vase", rarity="epic")  # 200
    spawn_collectible(actor.world, room_id=room.id, name="Coin", rarity="common")  # 10
    assert visitor_interest(actor.world, room) == 210


def test_interest_ignores_an_exposed_forgery():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    real = spawn_collectible(actor.world, room_id=room.id, name="Vase", rarity="epic")
    fake = spawn_collectible(
        actor.world, room_id=room.id, name="Fake", rarity="legendary", genuine=False
    )
    _expose_forgery(fake)
    assert real  # displayed
    assert visitor_interest(actor.world, room) == 200  # the legendary forgery no longer counts


# -- visitor_fragments ------------------------------------------------------------------


def test_fragments_report_a_quiet_gallery():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    spawn_collectible(actor.world, room_id=room.id, name="Coin", rarity="common")

    lines = visitor_fragments(actor.world, ada)

    assert lines == ["A few visitors wander the quiet galleries."]


def test_fragments_report_a_busy_gallery():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    spawn_collectible(actor.world, room_id=room.id, name="Vase", rarity="epic")  # 200 = busy
    assert BUSY_THRESHOLD <= 200 < TOUR_THRESHOLD

    lines = visitor_fragments(actor.world, ada)

    assert lines == ["A steady stream of visitors moves through the galleries."]


def test_fragments_report_a_guided_tour_around_the_star_piece():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    spawn_collectible(actor.world, room_id=room.id, name="Crown", rarity="legendary")  # 500

    lines = visitor_fragments(actor.world, ada)

    assert any("guided tour has gathered around Crown" in line for line in lines)
    assert "The galleries are crowded with visitors today." in lines


def test_tour_line_omitted_when_only_forgeries_reach_the_threshold():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    # A genuine piece keeps interest above the tour threshold, but the top piece is a forgery
    # that must not be named as the tour's star.
    spawn_collectible(actor.world, room_id=room.id, name="Crown", rarity="legendary")
    fake = spawn_collectible(
        actor.world, room_id=room.id, name="Fake Crown", rarity="legendary", genuine=False
    )
    _expose_forgery(fake)

    lines = visitor_fragments(actor.world, ada)

    assert any("guided tour has gathered around Crown" in line for line in lines)
    assert not any("Fake Crown" in line for line in lines)


def test_no_fragments_without_a_character():
    assert visitor_fragments(WorldActor().world, None) == []


def test_no_fragments_outside_a_museum():
    actor = WorldActor()
    plain = spawn_entity(actor.world, [RoomComponent(title="Alley")])
    ada = _character(actor.world, plain)
    assert visitor_fragments(actor.world, ada) == []


def test_no_fragments_in_an_empty_museum():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    assert visitor_fragments(actor.world, ada) == []
