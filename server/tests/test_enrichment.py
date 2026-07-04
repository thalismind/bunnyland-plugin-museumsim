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
