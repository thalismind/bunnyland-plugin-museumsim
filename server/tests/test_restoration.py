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
from bunnyland.prompts import ComponentPromptContext, PromptPerspective
from conftest import execute_handler

from bunnyland_museumsim import spawn_collectible, spawn_museum
from bunnyland_museumsim.restoration import (
    PRISTINE,
    ConditionComponent,
    PieceRestoredEvent,
    RestoreHandler,
    condition_of,
    is_damaged,
)

EPOCH = 12


def _character(world, room, name="Ada"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _restore(actor, character, item):
    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="restore",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"item_id": str(item.id)},
    )
    return execute_handler(
        RestoreHandler(), HandlerContext(world=actor.world, epoch=EPOCH), command
    )


def _ctx():
    world = WorldActor().world
    entity = spawn_entity(world, [IdentityComponent(name="viewer", kind="character")])
    return ComponentPromptContext(perspective=PromptPerspective(viewer=entity), entity=entity)


# -- helpers / component ----------------------------------------------------------------


def test_condition_defaults_to_pristine_without_a_record():
    piece = spawn_collectible(WorldActor().world, name="Vase")
    assert condition_of(piece) == PRISTINE
    assert not is_damaged(piece)


def test_damaged_piece_reads_as_damaged():
    piece = spawn_collectible(WorldActor().world, name="Vase", condition=0.4)
    assert condition_of(piece) == 0.4
    assert is_damaged(piece)


def test_prompt_fragments_report_condition():
    ctx = _ctx()
    assert ConditionComponent(condition=1.0).prompt_fragments(ctx) == (
        "This piece is in pristine condition.",
    )
    assert ConditionComponent(condition=0.4).prompt_fragments(ctx) == (
        "This piece is damaged (condition 0.4) and could be restored.",
    )


# -- handler happy path -----------------------------------------------------------------


def test_restore_repairs_a_damaged_piece():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Vase", condition=0.3)

    result = _restore(actor, ada, piece)

    assert result.ok
    event = result.events[0]
    assert isinstance(event, PieceRestoredEvent)
    assert event.condition_before == 0.3 and event.condition_after == PRISTINE
    record = piece.get_component(ConditionComponent)
    assert record.condition == PRISTINE
    assert record.restorer_id == str(ada.id) and record.restored_at_epoch == EPOCH
    assert not is_damaged(piece)


def test_restore_without_a_room_still_repairs():
    actor = WorldActor()
    ada = spawn_entity(
        actor.world, [IdentityComponent(name="Ada", kind="character"), CharacterComponent()]
    )
    piece = spawn_collectible(actor.world, name="Vase", condition=0.5)
    ada.add_relationship(Contains(mode=ContainmentMode.INVENTORY), piece.id)

    result = _restore(actor, ada, piece)

    assert result.ok and result.events[0].room_id is None


# -- rejection paths --------------------------------------------------------------------


def test_restore_rejects_a_pristine_piece():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Vase")

    result = _restore(actor, ada, piece)

    assert not result.ok and result.reason == "that piece needs no restoration"


def test_restore_rejects_non_collectible():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    rock = spawn_entity(
        actor.world, [IdentityComponent(name="rock", kind="item"), PortableComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), rock.id)

    result = _restore(actor, ada, rock)

    assert not result.ok and result.reason == "that is not a collectible"


def test_restore_rejects_unreachable_item():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    far_room = spawn_entity(actor.world, [RoomComponent(title="Vault")])
    piece = spawn_collectible(actor.world, room_id=far_room.id, name="Vase", condition=0.2)

    result = _restore(actor, ada, piece)

    assert not result.ok and result.reason == "that is not within reach"


def test_restore_rejects_invalid_character():
    actor = WorldActor()
    result = RestoreHandler().execute(
        HandlerContext(world=actor.world, epoch=EPOCH),
        build_submitted_command(
            character_id="???",
            controller_id="ctrl",
            controller_generation=0,
            command_type="restore",
            cost=CommandCost(action=1),
            lane=Lane.WORLD,
            payload={"item_id": "entity_1"},
        ),
    )
    assert not result.ok and result.reason == "invalid character id"


def test_restore_rejects_missing_item():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    result = RestoreHandler().execute(
        HandlerContext(world=actor.world, epoch=EPOCH),
        build_submitted_command(
            character_id=str(ada.id),
            controller_id="ctrl",
            controller_generation=0,
            command_type="restore",
            cost=CommandCost(action=1),
            lane=Lane.WORLD,
            payload={"item_id": "entity_9999"},
        ),
    )
    assert not result.ok and result.reason == "item does not exist"
