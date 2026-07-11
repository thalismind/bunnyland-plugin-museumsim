"""Storyteller integration: a famous exhibit draws crowds.

When a museum's collection grows valuable enough to become a genuine draw, that is world
pressure the storyteller should pace and other packs should feel. The
:class:`MuseumStorytellerConsequence` watches every museum and, the first time one crosses into
"famous" territory, spawns a Foundation Storyteller ``IncidentComponent``
(``famous_exhibit``) in the museum room. Because the incident uses the core component, the
storyteller's own prompt surface picks it up automatically — no parallel incident system.

The check is idempotent: a museum that already has an unresolved museum incident in its room is
skipped, so the crowd gathers exactly once per museum and survives save/reload.
"""

from __future__ import annotations

from bunnyland.core import ContainmentMode, Contains, IdentityComponent, contents, spawn_entity
from bunnyland.core.events import DomainEvent, EventVisibility, event_base
from bunnyland.foundation.storyteller.mechanics import IncidentComponent
from relics import Entity, World

from .components import MuseumComponent
from .visitors import TOUR_THRESHOLD, visitor_interest

#: The storyteller incident kind a famous museum raises.
FAMOUS_EXHIBIT = "famous_exhibit"


class FamousExhibitEvent(DomainEvent):
    """A museum's collection became a famous draw, raising a storyteller incident."""

    museum_id: str
    incident_id: str
    draw: int


def _has_active_museum_incident(world: World, room: Entity) -> bool:
    for entity_id in contents(room):
        if not world.has_entity(entity_id):
            continue
        entity = world.get_entity(entity_id)
        if not entity.has_component(IncidentComponent):
            continue
        incident = entity.get_component(IncidentComponent)
        if incident.kind == FAMOUS_EXHIBIT and incident.resolved_at_epoch is None:
            return True
    return False


class MuseumStorytellerConsequence:
    """Raise a ``famous_exhibit`` incident the first time a museum becomes a famous draw."""

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        rooms = list(world.query().with_all([MuseumComponent]).execute_entities())
        rooms.sort(key=lambda entity: str(entity.id))
        for room in rooms:
            draw = visitor_interest(world, room)
            if draw < TOUR_THRESHOLD or _has_active_museum_incident(world, room):
                continue
            incident = spawn_entity(
                world,
                [
                    IdentityComponent(name="famous exhibit", kind="incident"),
                    IncidentComponent(
                        kind=FAMOUS_EXHIBIT,
                        budget_spent=0.0,
                        started_at_epoch=epoch,
                        room_id=str(room.id),
                    ),
                ],
            )
            room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), incident.id)
            events.append(
                FamousExhibitEvent(
                    **event_base(
                        epoch,
                        default_visibility=EventVisibility.ROOM,
                        room_id=str(room.id),
                        target_ids=(str(incident.id),),
                        museum_id=str(room.id),
                        incident_id=str(incident.id),
                        draw=draw,
                    )
                )
            )
        return events


__all__ = [
    "FAMOUS_EXHIBIT",
    "FamousExhibitEvent",
    "MuseumStorytellerConsequence",
]
