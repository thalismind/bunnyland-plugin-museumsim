"""A famous museum raises a core storyteller incident, exactly once."""

from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.foundation.storyteller.mechanics import IncidentComponent

from bunnyland_museumsim import spawn_collectible, spawn_museum
from bunnyland_museumsim.incidents import (
    FAMOUS_EXHIBIT,
    FamousExhibitEvent,
    MuseumStorytellerConsequence,
)

EPOCH = 200


def _incidents(world):
    return list(world.query().with_all([IncidentComponent]).execute_entities())


def test_a_valuable_collection_raises_a_famous_exhibit_incident():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    # A single legendary piece (value 500) is exactly the tour threshold -> a famous draw.
    spawn_collectible(actor.world, room_id=room.id, name="Crown", rarity="legendary")

    events = MuseumStorytellerConsequence().process(actor.world, EPOCH)

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, FamousExhibitEvent)
    assert event.museum_id == str(room.id) and event.draw >= 500
    incidents = _incidents(actor.world)
    assert len(incidents) == 1
    assert incidents[0].get_component(IncidentComponent).kind == FAMOUS_EXHIBIT


def test_a_quiet_museum_raises_nothing():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    spawn_collectible(actor.world, room_id=room.id, name="Pebble", rarity="common")

    assert MuseumStorytellerConsequence().process(actor.world, EPOCH) == []
    assert _incidents(actor.world) == []


def test_the_incident_is_raised_only_once():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    spawn_collectible(actor.world, room_id=room.id, name="Crown", rarity="legendary")
    consequence = MuseumStorytellerConsequence()

    assert len(consequence.process(actor.world, EPOCH)) == 1
    assert consequence.process(actor.world, EPOCH + 1) == []
    assert len(_incidents(actor.world)) == 1


def test_a_resolved_prior_incident_does_not_block_a_new_one():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    spawn_collectible(actor.world, room_id=room.id, name="Crown", rarity="legendary")

    # A previously-resolved museum incident sits in the room; it does not count as an active
    # incident, so a fresh one is still raised.
    resolved = spawn_entity(
        actor.world,
        [
            IdentityComponent(name="old exhibit", kind="incident"),
            IncidentComponent(
                kind=FAMOUS_EXHIBIT,
                budget_spent=0.0,
                started_at_epoch=1,
                resolved_at_epoch=5,
            ),
        ],
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), resolved.id)

    events = MuseumStorytellerConsequence().process(actor.world, EPOCH)

    assert len(events) == 1
    active = [
        e
        for e in _incidents(actor.world)
        if e.get_component(IncidentComponent).resolved_at_epoch is None
    ]
    assert len(active) == 1


def test_a_second_museum_gets_its_own_incident():
    actor = WorldActor()
    room_a = spawn_museum(actor.world, name="A")
    room_b = spawn_museum(actor.world, name="B")
    spawn_collectible(actor.world, room_id=room_a.id, name="Crown A", rarity="legendary")
    spawn_collectible(actor.world, room_id=room_b.id, name="Crown B", rarity="legendary")

    events = MuseumStorytellerConsequence().process(actor.world, EPOCH)

    assert len(events) == 2
    assert len(_incidents(actor.world)) == 2
