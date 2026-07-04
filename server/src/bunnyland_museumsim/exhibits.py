"""Exhibits and completion: watch each exhibit fill up, then reward the donor.

An :class:`~bunnyland_museumsim.components.ExhibitComponent` names the pieces a category
wants (``required``) and the pieces already given (``donated``). A light per-tick
:class:`MuseumConsequence` scans every exhibit and, the first time one's wants are fully
satisfied, flips it to ``completed``, emits an :class:`ExhibitCompletedEvent`, and raises the
last donor's standing with the museum's curator — reusing the core ``SocialBond`` reputation
layer rather than inventing a parallel one.

The check is idempotent: a completed exhibit is skipped, so completion fires exactly once and
survives save/reload with the rest of the exhibit state.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core.ecs import parse_entity_id, replace_component
from bunnyland.core.events import DomainEvent, EventVisibility, event_base
from bunnyland.mechanics.social import adjust_bond
from relics import World

from .components import ExhibitComponent, MuseumComponent
from .museum import museum_of
from .spatial import room_of

#: Reputation deltas granted to a donor by the curator when an exhibit they filled completes.
COMPLETION_BOND: dict[str, float] = {"affinity": 0.2, "trust": 0.1}


class ExhibitCompletedEvent(DomainEvent):
    """An exhibit's wants were all satisfied and it is now complete."""

    exhibit_id: str
    category: str
    donor_id: str = ""


def exhibit_is_full(component: ExhibitComponent) -> bool:
    """True once a non-empty exhibit has every required piece donated."""
    return bool(component.required) and set(component.required) <= set(component.donated)


class MuseumConsequence:
    """Complete newly-filled exhibits and reward their donors each tick."""

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        exhibits = list(world.query().with_all([ExhibitComponent]).execute_entities())
        exhibits.sort(key=lambda entity: str(entity.id))
        for exhibit in exhibits:
            component = exhibit.get_component(ExhibitComponent)
            if component.completed or not exhibit_is_full(component):
                continue
            replace_component(exhibit, replace(component, completed=True))
            self._reward_donor(world, exhibit, component)
            events.append(
                ExhibitCompletedEvent(
                    **event_base(
                        epoch,
                        default_visibility=EventVisibility.ROOM,
                        target_ids=(str(exhibit.id),),
                        exhibit_id=str(exhibit.id),
                        category=component.category,
                        donor_id=component.last_donor_id,
                    )
                )
            )
        return events

    def _reward_donor(self, world: World, exhibit, component: ExhibitComponent) -> None:
        room = room_of(world, exhibit.id)
        museum: MuseumComponent | None = museum_of(room)
        if museum is None or not museum.curator_id or not component.last_donor_id:
            return
        curator_id = parse_entity_id(museum.curator_id)
        donor_id = parse_entity_id(component.last_donor_id)
        if curator_id is None or donor_id is None:
            return
        if not world.has_entity(curator_id) or not world.has_entity(donor_id):
            return
        adjust_bond(world, curator_id, donor_id, COMPLETION_BOND)


__all__ = [
    "COMPLETION_BOND",
    "ExhibitCompletedEvent",
    "MuseumConsequence",
    "exhibit_is_full",
]
