from __future__ import annotations

from bunnyland.core import IdentityComponent, WorldActor, spawn_entity
from bunnyland.prompts import ComponentPromptContext, PromptPerspective

from bunnyland_museumsim import spawn_curator, spawn_museum
from bunnyland_museumsim.patrons import (
    PatronOf,
    patron_tier,
    patronage_between,
    record_patronage,
)


def _fp_ctx(world, entity):
    return ComponentPromptContext.for_entity(world, entity)


def _tp_ctx(world, entity, viewer):
    return ComponentPromptContext(perspective=PromptPerspective(viewer=viewer), entity=entity)


# -- patron_tier ------------------------------------------------------------------------


def test_patron_tier_names_each_band():
    assert patron_tier(PatronOf(donations=0)) == ""
    assert patron_tier(PatronOf(donations=1)) == "friend"
    assert patron_tier(PatronOf(donations=5)) == "patron"
    assert patron_tier(PatronOf(donations=12)) == "benefactor"


# -- patronage_between ------------------------------------------------------------------


def test_patronage_between_is_none_without_a_donor_entity():
    world = WorldActor().world
    museum = spawn_museum(world)
    assert patronage_between(world, "entity_9999", museum.id) is None


def test_patronage_between_is_none_when_never_donated():
    world = WorldActor().world
    donor = spawn_curator(world, name="Ada")
    museum = spawn_museum(world)
    assert patronage_between(world, donor.id, museum.id) is None


def test_patronage_between_finds_only_the_matching_museum():
    world = WorldActor().world
    donor = spawn_curator(world, name="Ada")
    museum_a = spawn_museum(world, name="A")
    museum_b = spawn_museum(world, name="B")
    record_patronage(world, donor.id, museum_a.id, value=10, epoch=1)

    assert patronage_between(world, donor.id, museum_a.id) is not None
    assert patronage_between(world, donor.id, museum_b.id) is None


# -- record_patronage -------------------------------------------------------------------


def test_record_patronage_creates_then_accumulates():
    world = WorldActor().world
    donor = spawn_curator(world, name="Ada")
    museum = spawn_museum(world)

    first = record_patronage(world, donor.id, museum.id, value=25, epoch=5)
    assert first.donations == 1 and first.total_value == 25
    assert first.first_donation_epoch == 5 and first.last_donation_epoch == 5

    second = record_patronage(world, donor.id, museum.id, value=75, epoch=9)
    assert second.donations == 2 and second.total_value == 100
    assert second.first_donation_epoch == 5 and second.last_donation_epoch == 9


def test_record_patronage_clamps_negative_value():
    world = WorldActor().world
    donor = spawn_curator(world, name="Ada")
    museum = spawn_museum(world)
    edge = record_patronage(world, donor.id, museum.id, value=-50, epoch=1)
    assert edge.total_value == 0


def test_record_patronage_ignores_missing_entities():
    world = WorldActor().world
    museum = spawn_museum(world)
    assert record_patronage(world, "entity_9999", museum.id, value=10, epoch=1) is None
    donor = spawn_curator(world, name="Ada")
    assert record_patronage(world, donor.id, "entity_9999", value=10, epoch=1) is None


# -- prompt fragments -------------------------------------------------------------------


def test_prompt_fragment_reads_first_person_standing():
    world = WorldActor().world
    donor = spawn_entity(world, [IdentityComponent(name="Ada", kind="character")])
    edge = PatronOf(donations=6, total_value=300)
    lines = edge.prompt_fragments(_fp_ctx(world, donor))
    assert lines and "patron" in lines[0] and "6 piece(s)" in lines[0]


def test_prompt_fragment_is_silent_for_bystanders_and_non_donors():
    world = WorldActor().world
    donor = spawn_entity(world, [IdentityComponent(name="Ada", kind="character")])
    other = spawn_entity(world, [IdentityComponent(name="Bo", kind="character")])
    assert PatronOf(donations=6).prompt_fragments(_tp_ctx(world, donor, other)) == ()
    assert PatronOf(donations=0).prompt_fragments(_fp_ctx(world, donor)) == ()
