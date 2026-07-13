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
from bunnyland.core.ecs import contents
from bunnyland.core.handlers import HandlerContext
from conftest import execute_handler

from bunnyland_museumsim import (
    ExhibitComponent,
    MuseumComponent,
    PieceDonatedEvent,
    spawn_collectible,
    spawn_display_case,
    spawn_exhibit,
    spawn_museum,
)
from bunnyland_museumsim.donation import DonateHandler


def _museum(world, **kwargs):
    return spawn_museum(world, name="City Museum", **kwargs)


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
        command_type="donate",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload=payload,
    )


def _ctx(actor):
    return HandlerContext(world=actor.world, epoch=0)


def _donate(actor, character, item):
    return execute_handler(
        DonateHandler(), _ctx(actor), _cmd(character.id, {"item_id": str(item.id)})
    )


def test_donate_records_piece_and_moves_it_to_the_museum():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, name="Trilobite", category="fossil", rarity="rare")
    _hold(ada, piece)

    result = _donate(actor, ada, piece)

    assert result.ok
    assert isinstance(result.events[0], PieceDonatedEvent)
    assert "fossil/trilobite" in room.get_component(MuseumComponent).donated
    # the piece left the donor's hands for the museum floor
    assert piece.id in contents(room)
    assert piece.id not in contents(ada)


def test_donate_fills_the_matching_exhibit():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)
    exhibit = spawn_exhibit(
        actor.world, room_id=room.id, category="fossil", required=("Trilobite",)
    )
    piece = spawn_collectible(actor.world, name="Trilobite", category="fossil", rarity="rare")
    _hold(ada, piece)

    result = _donate(actor, ada, piece)

    assert result.ok
    assert "Trilobite" in exhibit.get_component(ExhibitComponent).donated
    assert exhibit.get_component(ExhibitComponent).last_donor_id == str(ada.id)


def test_donate_places_piece_into_a_display_case_when_present():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)
    case = spawn_display_case(actor.world, room_id=room.id)
    piece = spawn_collectible(actor.world, name="Bronze Idol", category="relic")
    _hold(ada, piece)

    result = _donate(actor, ada, piece)

    assert result.ok
    assert piece.id in contents(case)


def test_donate_rejects_a_duplicate_piece():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)
    first = spawn_collectible(actor.world, name="Trilobite", category="fossil")
    _hold(ada, first)
    _donate(actor, ada, first)

    duplicate = spawn_collectible(actor.world, name="Trilobite", category="fossil")
    _hold(ada, duplicate)

    result = _donate(actor, ada, duplicate)

    assert not result.ok
    assert result.reason == "that piece is already in the collection"


def test_donate_rejects_item_not_held():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Trilobite", category="fossil")

    result = _donate(actor, ada, piece)

    assert not result.ok
    assert result.reason == "you are not holding that"


def test_donate_rejects_non_collectible():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)
    trinket = spawn_entity(
        actor.world, [IdentityComponent(name="mug", kind="item"), PortableComponent()]
    )
    _hold(ada, trinket)

    result = _donate(actor, ada, trinket)

    assert not result.ok
    assert result.reason == "that is not a collectible"


def test_donate_rejects_when_no_museum_here():
    actor = WorldActor()
    plain_room = spawn_entity(actor.world, [RoomComponent(title="Alley")])
    ada = _character(actor.world, plain_room)
    piece = spawn_collectible(actor.world, name="Trilobite", category="fossil")
    _hold(ada, piece)

    result = _donate(actor, ada, piece)

    assert not result.ok
    assert result.reason == "there is no museum here"


def test_donate_rejects_invalid_character():
    actor = WorldActor()
    result = DonateHandler().execute(_ctx(actor), _cmd("???", {"item_id": "entity_1"}))
    assert not result.ok
    assert result.reason == "invalid character id"


def test_donate_rejects_missing_item():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)

    result = DonateHandler().execute(_ctx(actor), _cmd(ada.id, {"item_id": "entity_9999"}))

    assert not result.ok
    assert result.reason == "item does not exist"


def test_donate_rejects_invalid_item_id():
    actor = WorldActor()
    room = _museum(actor.world)
    ada = _character(actor.world, room)

    result = DonateHandler().execute(_ctx(actor), _cmd(ada.id, {"item_id": "???"}))

    assert not result.ok
    assert result.reason == "invalid item id"
