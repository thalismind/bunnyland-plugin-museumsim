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

from bunnyland_museumsim import spawn_collectible, spawn_museum
from bunnyland_museumsim.authentication import (
    AUTHENTIC,
    FORGERY,
    UNEXAMINED,
    AuthenticateHandler,
    AuthenticityComponent,
    PieceAuthenticatedEvent,
    authenticity_of,
    verdict_of,
)

EPOCH = 7


def _character(world, room, name="Ada"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _authenticate(actor, character, item):
    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="authenticate",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"item_id": str(item.id)},
    )
    return AuthenticateHandler().execute(HandlerContext(world=actor.world, epoch=EPOCH), command)


def _ctx():
    world = WorldActor().world
    entity = spawn_entity(world, [IdentityComponent(name="viewer", kind="character")])
    return ComponentPromptContext(
        perspective=PromptPerspective(viewer=entity), entity=entity
    )


# -- component / helpers ----------------------------------------------------------------


def test_authenticity_defaults_to_genuine_and_unexamined():
    piece = spawn_collectible(WorldActor().world, name="Vase")
    assert verdict_of(piece) == UNEXAMINED
    record = authenticity_of(piece)
    assert record.genuine is True and record.verdict == UNEXAMINED


def test_authenticity_of_reads_a_present_record():
    world = WorldActor().world
    piece = spawn_collectible(world, name="Vase", genuine=False)
    assert authenticity_of(piece).genuine is False


def test_prompt_fragments_report_each_verdict():
    ctx = _ctx()
    assert AuthenticityComponent(verdict=UNEXAMINED).prompt_fragments(ctx) == (
        "This piece has not been authenticated.",
    )
    assert AuthenticityComponent(verdict=FORGERY).prompt_fragments(ctx) == (
        "This piece has been exposed as a forgery.",
    )
    assert AuthenticityComponent(verdict=AUTHENTIC).prompt_fragments(ctx) == (
        "This piece has been authenticated as genuine.",
    )


# -- handler happy paths ----------------------------------------------------------------


def test_authenticate_confirms_a_genuine_piece():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Vase", genuine=True)

    result = _authenticate(actor, ada, piece)

    assert result.ok
    event = result.events[0]
    assert isinstance(event, PieceAuthenticatedEvent)
    assert event.verdict == AUTHENTIC and event.genuine is True
    record = authenticity_of(piece)
    assert record.verdict == AUTHENTIC
    assert record.examiner_id == str(ada.id) and record.examined_at_epoch == EPOCH


def test_authenticate_exposes_a_forgery():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Fake", genuine=False)

    result = _authenticate(actor, ada, piece)

    assert result.ok
    assert result.events[0].verdict == FORGERY
    assert verdict_of(piece) == FORGERY


def test_authenticate_without_a_room_still_settles_the_verdict():
    actor = WorldActor()
    ada = spawn_entity(
        actor.world, [IdentityComponent(name="Ada", kind="character"), CharacterComponent()]
    )
    piece = spawn_collectible(actor.world, name="Vase", genuine=True)
    ada.add_relationship(Contains(mode=ContainmentMode.INVENTORY), piece.id)

    result = _authenticate(actor, ada, piece)

    assert result.ok and result.events[0].room_id is None


# -- rejection paths --------------------------------------------------------------------


def test_authenticate_rejects_already_authenticated():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Vase", genuine=True)

    assert _authenticate(actor, ada, piece).ok
    second = _authenticate(actor, ada, piece)

    assert not second.ok
    assert second.reason == "that piece has already been authenticated"


def test_authenticate_rejects_non_collectible():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    rock = spawn_entity(
        actor.world, [IdentityComponent(name="rock", kind="item"), PortableComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), rock.id)

    result = _authenticate(actor, ada, rock)

    assert not result.ok and result.reason == "that is not a collectible"


def test_authenticate_rejects_unreachable_item():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    far_room = spawn_entity(actor.world, [RoomComponent(title="Vault")])
    piece = spawn_collectible(actor.world, room_id=far_room.id, name="Vase", genuine=True)

    result = _authenticate(actor, ada, piece)

    assert not result.ok and result.reason == "that is not within reach"


def test_authenticate_rejects_invalid_and_missing_ids():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)

    invalid = AuthenticateHandler().execute(
        HandlerContext(world=actor.world, epoch=EPOCH),
        build_submitted_command(
            character_id=str(ada.id),
            controller_id="ctrl",
            controller_generation=0,
            command_type="authenticate",
            cost=CommandCost(action=1),
            lane=Lane.WORLD,
            payload={"item_id": "???"},
        ),
    )
    assert invalid.reason == "invalid item id"

    missing = AuthenticateHandler().execute(
        HandlerContext(world=actor.world, epoch=EPOCH),
        build_submitted_command(
            character_id=str(ada.id),
            controller_id="ctrl",
            controller_generation=0,
            command_type="authenticate",
            cost=CommandCost(action=1),
            lane=Lane.WORLD,
            payload={"item_id": "entity_9999"},
        ),
    )
    assert missing.reason == "item does not exist"


def test_authenticate_rejects_invalid_character():
    actor = WorldActor()
    result = AuthenticateHandler().execute(
        HandlerContext(world=actor.world, epoch=EPOCH),
        build_submitted_command(
            character_id="???",
            controller_id="ctrl",
            controller_generation=0,
            command_type="authenticate",
            cost=CommandCost(action=1),
            lane=Lane.WORLD,
            payload={"item_id": "entity_1"},
        ),
    )
    assert not result.ok and result.reason == "invalid character id"
