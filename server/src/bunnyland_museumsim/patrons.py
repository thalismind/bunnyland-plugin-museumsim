"""Donor recognition as a typed edge (spec 11.15 modelling rules).

A museum remembers *who* built its collection. Rather than stuffing a list of donor ids onto
a component, each donor's standing is a directed :class:`PatronOf` edge ``donor -> museum`` —
its own index, so "who are this museum's patrons" and "what has this donor given" stay cheap
and unambiguous. The edge accrues a running count and appraised value across every donation,
and reads as a patronage tier in first-person prompts.

The *affective* side of the relationship — how the curator personally feels about a generous
donor — is deliberately **not** modelled here; that stays on the core ``SocialBond`` edge,
warmed when an exhibit the donor filled is completed (see :mod:`.exhibits`). One edge type per
kind of relationship.
"""

from __future__ import annotations

from bunnyland.prompts import ComponentPromptContext
from pydantic.dataclasses import dataclass
from relics import Edge, EntityId, World

#: Donation-count thresholds for patronage tiers, ascending. The first tier whose floor is met
#: (scanning high to low) names the donor's standing with a museum.
PATRON_TIERS: tuple[tuple[int, str], ...] = (
    (10, "benefactor"),
    (5, "patron"),
    (1, "friend"),
)


@dataclass(frozen=True)
class PatronOf(Edge):
    """A directed ``donor -> museum`` patronage record, accrued across donations."""

    donations: int = 0
    total_value: int = 0
    first_donation_epoch: int = 0
    last_donation_epoch: int = 0

    def prompt_fragments(self, ctx: ComponentPromptContext) -> tuple[str, ...]:
        if not ctx.is_first_person or self.donations <= 0:
            return ()
        tier = patron_tier(self)
        return (
            f"You are a {tier} of this collection "
            f"({self.donations} piece(s) donated, {self.total_value} in value).",
        )


def patron_tier(edge: PatronOf) -> str:
    """Name a donor's standing from their donation count (``""`` for a non-donor)."""
    for floor, label in PATRON_TIERS:
        if edge.donations >= floor:
            return label
    return ""


def patronage_between(world: World, donor_id: EntityId, museum_id: EntityId) -> PatronOf | None:
    """The directed ``donor -> museum`` patronage edge, or ``None`` if never donated."""
    if not world.has_entity(donor_id):
        return None
    for edge, target in world.get_entity(donor_id).get_relationships(PatronOf):
        if target == museum_id:
            return edge
    return None


def record_patronage(
    world: World,
    donor_id: EntityId,
    museum_id: EntityId,
    *,
    value: int,
    epoch: int,
) -> PatronOf | None:
    """Add one donation to the ``donor -> museum`` patronage edge (created if absent)."""
    if not world.has_entity(donor_id) or not world.has_entity(museum_id):
        return None
    current = patronage_between(world, donor_id, museum_id)
    updated = PatronOf(
        donations=(current.donations if current else 0) + 1,
        total_value=(current.total_value if current else 0) + max(0, value),
        first_donation_epoch=current.first_donation_epoch if current else epoch,
        last_donation_epoch=epoch,
    )
    # add_relationship overwrites an existing edge of the same type+target.
    world.get_entity(donor_id).add_relationship(updated, museum_id)
    return updated


__all__ = [
    "PATRON_TIERS",
    "PatronOf",
    "patron_tier",
    "patronage_between",
    "record_patronage",
]
