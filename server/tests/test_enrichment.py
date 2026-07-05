from __future__ import annotations

import asyncio

from bunnyland.core import IdentityComponent, RoomComponent, WorldActor, spawn_entity
from bunnyland.core.components import GenerationIntentComponent
from bunnyland.core.ecs import contents
from bunnyland.core.events import ObjectGeneratedEvent, RoomGeneratedEvent, event_base
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_museumsim import CollectibleComponent, ExhibitComponent, MuseumComponent
from bunnyland_museumsim.display import DisplayCaseComponent


def _actor():
    actor = WorldActor()
    apply_plugins(load_modules(["bunnyland_museumsim"]), actor)
    return actor


def _publish(actor, event):
    asyncio.run(actor.bus.publish(event))


def _generate_room(actor, *, tags=(), description=""):
    room = spawn_entity(actor.world, [RoomComponent(title="Hall")])
    event = RoomGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id=str(room.id),
        entity_key="hall",
        entity_kind="room",
        generation=GenerationIntentComponent(tags=tuple(tags), description=description),
        room_key="hall",
    )
    _publish(actor, event)
    return room


def _generate_object(actor, *, tags=(), description=""):
    entity = spawn_entity(actor.world, [IdentityComponent(name="thing", kind="item")])
    event = ObjectGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id=str(entity.id),
        entity_key="thing",
        entity_kind="object",
        generation=GenerationIntentComponent(tags=tuple(tags), description=description),
        object_key="thing",
    )
    _publish(actor, event)
    return entity


def _component_types(actor, room, component_type):
    found = []
    for entity_id in contents(room):
        if actor.world.has_entity(entity_id):
            entity = actor.world.get_entity(entity_id)
            if entity.has_component(component_type):
                found.append(entity)
    return found


def test_museum_room_is_furnished():
    actor = _actor()
    room = _generate_room(actor, tags=("museum",))

    assert room.has_component(MuseumComponent)
    assert room.get_component(MuseumComponent).curator_id != ""
    assert _component_types(actor, room, ExhibitComponent)
    assert _component_types(actor, room, DisplayCaseComponent)
    # seeded loose collectibles for players to donate
    assert _component_types(actor, room, CollectibleComponent)


def test_museum_detected_from_description_text():
    actor = _actor()
    room = _generate_room(actor, description="a grand hall of antiquities")

    assert room.has_component(MuseumComponent)


def test_plain_room_is_not_a_museum():
    actor = _actor()
    room = _generate_room(actor, tags=("kitchen",), description="a cozy pantry")

    assert not room.has_component(MuseumComponent)


def test_collectible_object_is_tagged():
    actor = _actor()
    entity = _generate_object(actor, tags=("fossil",), description="a rare ancient trilobite")

    assert entity.has_component(CollectibleComponent)
    component = entity.get_component(CollectibleComponent)
    assert component.category == "fossil"
    assert component.rarity == "rare"


def test_plain_object_is_not_tagged():
    actor = _actor()
    entity = _generate_object(actor, tags=("wooden", "crate"))

    assert not entity.has_component(CollectibleComponent)


def test_furnishing_a_museum_is_idempotent():
    actor = _actor()
    room = _generate_room(actor, tags=("museum",))
    cases_before = len(_component_types(actor, room, DisplayCaseComponent))

    # Re-firing the room-generated event must not double-furnish the museum.
    event = RoomGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id=str(room.id),
        entity_key="hall",
        entity_kind="room",
        generation=GenerationIntentComponent(tags=("museum",), description=""),
        room_key="hall",
    )
    _publish(actor, event)

    assert len(_component_types(actor, room, DisplayCaseComponent)) == cases_before


def test_tagging_a_collectible_is_idempotent():
    actor = _actor()
    entity = _generate_object(actor, tags=("fossil",), description="a rare trilobite")
    first = entity.get_component(CollectibleComponent)

    event = ObjectGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id=str(entity.id),
        entity_key="thing",
        entity_kind="object",
        generation=GenerationIntentComponent(tags=("gem",), description="a diamond"),
        object_key="thing",
    )
    _publish(actor, event)

    assert entity.get_component(CollectibleComponent) == first  # unchanged


def test_generation_events_for_unknown_entities_are_ignored():
    actor = _actor()
    hook = actor  # events referencing a non-existent entity must be no-ops
    room_event = RoomGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id="entity_9999",
        entity_key="hall",
        entity_kind="room",
        generation=GenerationIntentComponent(tags=("museum",), description=""),
        room_key="hall",
    )
    object_event = ObjectGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id="???",
        entity_key="thing",
        entity_kind="object",
        generation=GenerationIntentComponent(tags=("fossil",), description=""),
        object_key="thing",
    )
    _publish(hook, room_event)
    _publish(hook, object_event)  # no exception -> handled gracefully
