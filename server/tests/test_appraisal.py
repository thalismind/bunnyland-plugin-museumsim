from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    PortableComponent,
    RoomComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.handlers import HandlerContext

from bunnyland_museumsim import PieceAppraisedEvent, spawn_collectible
from bunnyland_museumsim.appraisal import AppraiseHandler
from bunnyland_museumsim.collectibles import collectible_value
from bunnyland_museumsim.components import CollectibleComponent


def _room(world):
    return spawn_entity(world, [RoomComponent(title="Vault")])


def _character(world, room, name="Ada"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _hold(holder, item):
    holder.add_relationship(Contains(mode=ContainmentMode.INVENTORY), item.id)


def _cmd(character_id, payload):
    return build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="appraise",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload=payload,
    )


def _ctx(actor):
    return HandlerContext(world=actor.world, epoch=0)


def test_appraise_reports_category_rarity_and_value():
    actor = WorldActor()
    room = _room(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, name="Idol", category="relic", rarity="legendary")
    _hold(ada, piece)

    result = AppraiseHandler().execute(_ctx(actor), _cmd(ada.id, {"item_id": str(piece.id)}))

    assert result.ok
    event = result.events[0]
    assert isinstance(event, PieceAppraisedEvent)
    assert event.category == "relic"
    assert event.rarity == "legendary"
    assert event.value == collectible_value(piece.get_component(CollectibleComponent))


def test_appraise_works_on_a_piece_resting_in_the_room():
    actor = WorldActor()
    room = _room(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Gem", category="gem")

    result = AppraiseHandler().execute(_ctx(actor), _cmd(ada.id, {"item_id": str(piece.id)}))

    assert result.ok


def test_appraise_rejects_unreachable_piece():
    actor = WorldActor()
    room = _room(actor.world)
    other = _room(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=other.id, name="Gem", category="gem")

    result = AppraiseHandler().execute(_ctx(actor), _cmd(ada.id, {"item_id": str(piece.id)}))

    assert not result.ok
    assert result.reason == "that is not within reach"


def test_appraise_rejects_non_collectible():
    actor = WorldActor()
    room = _room(actor.world)
    ada = _character(actor.world, room)
    mug = spawn_entity(
        actor.world, [IdentityComponent(name="mug", kind="item"), PortableComponent()]
    )
    _hold(ada, mug)

    result = AppraiseHandler().execute(_ctx(actor), _cmd(ada.id, {"item_id": str(mug.id)}))

    assert not result.ok
    assert result.reason == "that is not a collectible"


def test_appraise_rejects_invalid_character():
    actor = WorldActor()
    result = AppraiseHandler().execute(_ctx(actor), _cmd("???", {"item_id": "entity_1"}))
    assert not result.ok
    assert result.reason == "invalid character id"


def test_appraise_rejects_missing_item():
    actor = WorldActor()
    room = _room(actor.world)
    ada = _character(actor.world, room)

    result = AppraiseHandler().execute(_ctx(actor), _cmd(ada.id, {"item_id": "entity_9999"}))

    assert not result.ok
    assert result.reason == "item does not exist"
