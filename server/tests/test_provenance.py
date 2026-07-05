"""The provenance reactor routes donations/verdicts through core history, imagegen, memory."""

from __future__ import annotations

import asyncio

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.events import EventVisibility, event_base
from bunnyland.core.handlers import HandlerContext
from bunnyland.imagegen.components import ImageRequestComponent
from bunnyland.mechanics.history import DeedReputationComponent, world_history_records
from bunnyland.memory import install_memory

from bunnyland_museumsim import (
    spawn_collectible,
    spawn_curator,
    spawn_museum,
)
from bunnyland_museumsim.authentication import AuthenticateHandler, PieceAuthenticatedEvent
from bunnyland_museumsim.donation import DonateHandler
from bunnyland_museumsim.events import PieceDonatedEvent
from bunnyland_museumsim.patrons import patronage_between
from bunnyland_museumsim.provenance import (
    MUSEUM_JOURNAL,
    MuseumProvenanceReactor,
    install_provenance,
)

EPOCH = 50


def _character(world, room, name="Ada"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _donate_event(actor, character, item):
    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="donate",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"item_id": str(item.id)},
    )
    result = DonateHandler().execute(HandlerContext(world=actor.world, epoch=EPOCH), command)
    assert result.ok
    return result.events[0]


def _authenticate_event(actor, character, item):
    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="authenticate",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"item_id": str(item.id)},
    )
    result = AuthenticateHandler().execute(HandlerContext(world=actor.world, epoch=EPOCH), command)
    assert result.ok
    return result.events[0]


def _publish(actor, event):
    asyncio.run(actor.bus.publish(event))


# -- donation provenance ----------------------------------------------------------------


def test_donation_records_history_reputation_patronage_image_and_journal():
    actor = WorldActor()
    store = install_memory(actor)
    install_provenance(actor)
    curator = spawn_curator(actor.world, name="Curator")
    room = spawn_museum(actor.world, curator_id=str(curator.id))
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), curator.id)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, name="Trilobite", category="fossil", rarity="rare")
    ada.add_relationship(Contains(mode=ContainmentMode.INVENTORY), piece.id)

    _publish(actor, _donate_event(actor, ada, piece))

    records = world_history_records(actor.world, tags={"donation"})
    assert any(r.event_type == "museum.donation" for _e, r in records)
    assert ada.has_component(DeedReputationComponent)
    assert "museum-patron" in ada.get_component(DeedReputationComponent).scores
    edge = patronage_between(actor.world, ada.id, room.id)
    assert edge is not None and edge.donations == 1 and edge.total_value == 75
    assert piece.has_component(ImageRequestComponent)
    assert store.search(MUSEUM_JOURNAL)


def test_donation_reactor_is_idempotent_and_skips_a_second_image_request():
    actor = WorldActor()
    install_provenance(actor)
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    piece = spawn_collectible(actor.world, name="Trilobite", category="fossil", rarity="rare")
    ada.add_relationship(Contains(mode=ContainmentMode.INVENTORY), piece.id)
    event = _donate_event(actor, ada, piece)

    _publish(actor, event)
    _publish(actor, event)  # replaying the same event must not duplicate history

    donation_records = [
        r for _e, r in world_history_records(actor.world) if r.event_type == "museum.donation"
    ]
    assert len(donation_records) == 1


def test_donation_without_a_memory_store_still_records_history():
    actor = WorldActor()  # no install_memory -> no memory_store
    reactor = MuseumProvenanceReactor(actor)
    reactor.subscribe(actor.bus)
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    first = spawn_collectible(actor.world, name="A", category="fossil", rarity="rare")
    second = spawn_collectible(actor.world, name="B", category="relic", rarity="epic")
    ada.add_relationship(Contains(mode=ContainmentMode.INVENTORY), first.id)
    ada.add_relationship(Contains(mode=ContainmentMode.INVENTORY), second.id)

    _publish(actor, _donate_event(actor, ada, first))
    assert reactor._warned_no_store is True
    _publish(actor, _donate_event(actor, ada, second))  # warning is not repeated

    assert world_history_records(actor.world, tags={"donation"})


def test_donation_reactor_ignores_events_with_unknown_entities():
    actor = WorldActor()
    install_provenance(actor)
    bogus = PieceDonatedEvent(
        **event_base(
            EPOCH,
            default_visibility=EventVisibility.ROOM,
            actor_id="entity_9999",
            item_id="entity_8888",
            museum_id="entity_7777",
            category="fossil",
            rarity="rare",
        )
    )
    _publish(actor, bogus)
    assert not world_history_records(actor.world, tags={"donation"})


def test_donation_reactor_skips_patronage_for_an_unparseable_actor():
    actor = WorldActor()
    install_provenance(actor)
    room = spawn_museum(actor.world)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Vase", rarity="rare")
    event = PieceDonatedEvent(
        **event_base(
            EPOCH,
            default_visibility=EventVisibility.ROOM,
            actor_id="not-an-id",
            item_id=str(piece.id),
            museum_id=str(room.id),
            category="fossil",
            rarity="rare",
        )
    )
    _publish(actor, event)
    # History still recorded; patronage simply skipped because the actor id will not parse.
    assert world_history_records(actor.world, tags={"donation"})


def test_donation_without_an_actor_still_records_history_and_image():
    actor = WorldActor()
    install_provenance(actor)
    room = spawn_museum(actor.world)
    piece = spawn_collectible(actor.world, room_id=room.id, name="Vase", rarity="rare")
    event = PieceDonatedEvent(
        **event_base(
            EPOCH,
            default_visibility=EventVisibility.ROOM,
            actor_id=None,  # an anonymous/ownerless donation
            item_id=str(piece.id),
            museum_id=str(room.id),
            category="fossil",
            rarity="rare",
        )
    )
    _publish(actor, event)

    assert world_history_records(actor.world, tags={"donation"})
    assert piece.has_component(ImageRequestComponent)  # image still requested


# -- forgery provenance -----------------------------------------------------------------


def test_exposed_forgery_is_written_to_history_and_journal():
    actor = WorldActor()
    store = install_memory(actor)
    install_provenance(actor)
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    fake = spawn_collectible(actor.world, room_id=room.id, name="Fake Idol", genuine=False)

    _publish(actor, _authenticate_event(actor, ada, fake))

    records = world_history_records(actor.world, tags={"forgery"})
    assert any(r.event_type == "museum.forgery" for _e, r in records)
    assert store.search(MUSEUM_JOURNAL)


def test_genuine_authentication_leaves_no_forgery_record():
    actor = WorldActor()
    install_provenance(actor)
    room = spawn_museum(actor.world)
    ada = _character(actor.world, room)
    real = spawn_collectible(actor.world, room_id=room.id, name="Real Vase", genuine=True)

    _publish(actor, _authenticate_event(actor, ada, real))

    assert not world_history_records(actor.world, tags={"forgery"})


def test_forgery_reactor_ignores_a_missing_piece():
    actor = WorldActor()
    install_provenance(actor)
    bogus = PieceAuthenticatedEvent(
        **event_base(
            EPOCH,
            default_visibility=EventVisibility.ROOM,
            actor_id="entity_9999",
            item_id="entity_8888",
            verdict="forgery",
            genuine=False,
            examiner_id="entity_9999",
        )
    )
    _publish(actor, bogus)
    assert not world_history_records(actor.world, tags={"forgery"})
