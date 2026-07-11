from __future__ import annotations

from dataclasses import replace

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.ecs import replace_component
from bunnyland.core.handlers import HandlerContext
from bunnyland.foundation.social.mechanics import bond_between

from bunnyland_museumsim import (
    ExhibitCompletedEvent,
    ExhibitComponent,
    MuseumConsequence,
    exhibit_is_full,
    spawn_collectible,
    spawn_curator,
    spawn_exhibit,
    spawn_museum,
)
from bunnyland_museumsim.donation import DonateHandler

EPOCH = 100


def _character(world, room, name="Ada"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _donate(actor, character, item):
    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="donate",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={"item_id": str(item.id)},
    )
    return DonateHandler().execute(HandlerContext(world=actor.world, epoch=EPOCH), command)


# -- exhibit_is_full --------------------------------------------------------------------


def test_exhibit_is_full_only_when_all_required_donated():
    assert not exhibit_is_full(ExhibitComponent(required=()))
    assert not exhibit_is_full(ExhibitComponent(required=("a", "b"), donated=("a",)))
    assert exhibit_is_full(ExhibitComponent(required=("a", "b"), donated=("a", "b")))


# -- MuseumConsequence ------------------------------------------------------------------


def test_completed_exhibit_emits_event_and_flips_flag():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    exhibit = spawn_exhibit(
        actor.world, room_id=room.id, category="fossil", required=("trilobite",)
    )
    component = exhibit.get_component(ExhibitComponent)
    replace_component(exhibit, replace(component, donated=("trilobite",)))

    events = MuseumConsequence().process(actor.world, EPOCH)

    assert len(events) == 1
    assert isinstance(events[0], ExhibitCompletedEvent)
    assert events[0].category == "fossil"
    assert exhibit.get_component(ExhibitComponent).completed is True


def test_completion_fires_only_once():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    exhibit = spawn_exhibit(
        actor.world, room_id=room.id, category="fossil", required=("trilobite",)
    )
    replace_component(
        exhibit, replace(exhibit.get_component(ExhibitComponent), donated=("trilobite",))
    )
    consequence = MuseumConsequence()

    assert len(consequence.process(actor.world, EPOCH)) == 1
    assert consequence.process(actor.world, EPOCH + 1) == []


def test_incomplete_exhibit_emits_nothing():
    actor = WorldActor()
    room = spawn_museum(actor.world)
    spawn_exhibit(actor.world, room_id=room.id, category="fossil", required=("trilobite", "fern"))

    assert MuseumConsequence().process(actor.world, EPOCH) == []


def test_completing_an_exhibit_raises_the_donor_reputation():
    actor = WorldActor()
    curator = spawn_curator(actor.world, name="Curator")
    room = spawn_museum(actor.world, curator_id=str(curator.id))
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), curator.id)
    ada = _character(actor.world, room)
    spawn_exhibit(actor.world, room_id=room.id, category="fossil", required=("Trilobite",))
    piece = spawn_collectible(actor.world, name="Trilobite", category="fossil")
    ada.add_relationship(Contains(mode=ContainmentMode.INVENTORY), piece.id)

    assert _donate(actor, ada, piece).ok
    MuseumConsequence().process(actor.world, EPOCH)

    bond = bond_between(actor.world, curator.id, ada.id)
    assert bond is not None
    assert bond.affinity > 0.0


def test_reward_is_skipped_when_the_curator_id_is_unparseable():
    actor = WorldActor()
    room = spawn_museum(actor.world, curator_id="not-an-id")
    ada = _character(actor.world, room)
    exhibit = spawn_exhibit(
        actor.world, room_id=room.id, category="fossil", required=("trilobite",)
    )
    replace_component(
        exhibit,
        replace(
            exhibit.get_component(ExhibitComponent),
            donated=("trilobite",),
            last_donor_id=str(ada.id),
        ),
    )

    events = MuseumConsequence().process(actor.world, EPOCH)

    assert isinstance(events[0], ExhibitCompletedEvent)  # completes despite the bad curator id


def test_reward_is_skipped_when_the_curator_entity_is_gone():
    actor = WorldActor()
    curator = spawn_curator(actor.world, name="Curator")
    curator_id = curator.id
    room = spawn_museum(actor.world, curator_id=str(curator_id))
    ada = _character(actor.world, room)
    exhibit = spawn_exhibit(
        actor.world, room_id=room.id, category="fossil", required=("trilobite",)
    )
    replace_component(
        exhibit,
        replace(
            exhibit.get_component(ExhibitComponent),
            donated=("trilobite",),
            last_donor_id=str(ada.id),
        ),
    )
    actor.world.remove(curator_id)  # curator parses but no longer exists

    events = MuseumConsequence().process(actor.world, EPOCH)

    assert isinstance(events[0], ExhibitCompletedEvent)


def test_completion_without_a_curator_still_completes():
    actor = WorldActor()
    room = spawn_museum(actor.world)  # no curator_id
    exhibit = spawn_exhibit(
        actor.world, room_id=room.id, category="fossil", required=("trilobite",)
    )
    replace_component(
        exhibit, replace(exhibit.get_component(ExhibitComponent), donated=("trilobite",))
    )

    events = MuseumConsequence().process(actor.world, EPOCH)

    assert isinstance(events[0], ExhibitCompletedEvent)
    assert exhibit.get_component(ExhibitComponent).completed is True
