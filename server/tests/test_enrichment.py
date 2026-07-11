import asyncio

from bunnyland.core import WorldActor
from bunnyland.core.ecs import contents
from bunnyland.plugins import apply_plugins
from bunnyland.worldgen import ObjectSpec, RoomSpec, WorldProposal, instantiate

from bunnyland_museumsim import CollectibleComponent, ExhibitComponent, MuseumComponent
from bunnyland_museumsim.components import MuseumHasCurator
from bunnyland_museumsim.display import DisplayCaseComponent
from bunnyland_museumsim.plugin import bunnyland_plugins as _plugins


def _world(room: RoomSpec, objects=()):
    actor = WorldActor()
    apply_plugins(_plugins(), actor)
    result = asyncio.run(
        instantiate(
            actor,
            WorldProposal(seed="seed", rooms=[room], objects=list(objects)),
        )
    )
    return actor, result


def _component_types(actor, room, component_type):
    return [
        actor.world.get_entity(entity_id)
        for entity_id in contents(room)
        if actor.world.has_entity(entity_id)
        and actor.world.get_entity(entity_id).has_component(component_type)
    ]


def test_museum_room_is_furnished():
    actor, result = _world(RoomSpec(key="hall", title="Museum Hall"))
    room = actor.world.get_entity(result.rooms["hall"])

    assert room.has_component(MuseumComponent)
    assert len(room.get_relationships(MuseumHasCurator)) == 1
    assert _component_types(actor, room, ExhibitComponent)
    assert _component_types(actor, room, DisplayCaseComponent)
    assert _component_types(actor, room, CollectibleComponent)


def test_museum_detected_from_description_text():
    actor, result = _world(
        RoomSpec(key="hall", title="Hall", description="a grand hall of antiquities")
    )
    assert actor.world.get_entity(result.rooms["hall"]).has_component(MuseumComponent)


def test_plain_room_is_not_a_museum():
    actor, result = _world(RoomSpec(key="pantry", title="Cozy Pantry"))
    assert not actor.world.get_entity(result.rooms["pantry"]).has_component(MuseumComponent)


def test_collectible_object_is_tagged():
    actor, result = _world(
        RoomSpec(key="room", title="Room"),
        objects=(
            ObjectSpec(
                key="thing",
                room_key="room",
                name="rare ancient trilobite",
                tags=("fossil",),
            ),
        ),
    )
    component = actor.world.get_entity(result.objects["thing"]).get_component(CollectibleComponent)
    assert component.category == "fossil"
    assert component.rarity == "rare"


def test_plain_object_is_not_tagged():
    actor, result = _world(
        RoomSpec(key="room", title="Room"),
        objects=(ObjectSpec(key="crate", room_key="room", name="wooden crate"),),
    )
    assert not actor.world.get_entity(result.objects["crate"]).has_component(CollectibleComponent)
