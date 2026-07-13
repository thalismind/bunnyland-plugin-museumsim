"""Restoration: bring a damaged piece back to display condition.

A collectible's physical state lives on a :class:`ConditionComponent` (``1.0`` pristine, ``0.0``
ruined). Age and rough handling leave pieces below pristine; the ``restore`` verb lets a curator
work on a reachable damaged piece, lifting it back to full condition and stamping who did the
work. A piece with no condition record — or one already pristine — needs no restoration.

Restoration is deliberately deterministic: a restore fully repairs the piece. The interest is in
*who* restored *what* (recorded to history by the donation reactor's sibling record) and in the
piece reading as pristine again on display, not in a decaying-meter chore.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core.actions import ActionArgument, ActionDefinition, ActionEffort, effort_cost
from bunnyland.core.commands import Lane, SubmittedCommand
from bunnyland.core.events import DomainEvent, EventVisibility
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    planned,
    rejected,
    require_character,
    require_reachable_entity,
)
from bunnyland.core.mutations import MutationPlan, SetComponent
from bunnyland.prompts import ComponentPromptContext
from pydantic.dataclasses import dataclass
from relics import Component, Entity

from .components import CollectibleComponent
from .spatial import room_of

#: A piece at or above this condition is considered pristine and needs no restoration.
PRISTINE = 1.0


@dataclass(frozen=True)
class ConditionComponent(Component):
    """A collectible's physical condition and who last restored it."""

    condition: float = PRISTINE
    restorer_id: str = ""
    restored_at_epoch: int = 0

    def prompt_fragments(self, ctx: ComponentPromptContext) -> tuple[str, ...]:
        if self.condition >= PRISTINE:
            return ("This piece is in pristine condition.",)
        return (f"This piece is damaged (condition {self.condition:.1f}) and could be restored.",)


class PieceRestoredEvent(DomainEvent):
    """A character restored a damaged collectible to pristine condition."""

    item_id: str
    restorer_id: str
    condition_before: float
    condition_after: float


def condition_of(entity: Entity) -> float:
    """The piece's condition (``PRISTINE`` when it carries no condition record)."""
    if entity.has_component(ConditionComponent):
        return entity.get_component(ConditionComponent).condition
    return PRISTINE


def is_damaged(entity: Entity) -> bool:
    """Whether ``entity`` is a collectible below pristine condition."""
    return condition_of(entity) < PRISTINE


class RestoreHandler:
    """Restore a reachable damaged collectible to pristine condition."""

    command_type = "restore"

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id, character, rejection = require_character(ctx, command.character_id)
        if rejection is not None:
            return rejection
        item_id, item, rejection = require_reachable_entity(
            ctx,
            character,
            command.payload.get("item_id"),
            invalid_reason="invalid item id",
            missing_reason="item does not exist",
            unreachable_reason="that is not within reach",
        )
        if rejection is not None:
            return rejection
        if not item.has_component(CollectibleComponent):
            return rejected("that is not a collectible")
        if not is_damaged(item):
            return rejected("that piece needs no restoration")

        # A damaged piece always carries a ConditionComponent (a piece without one reads as
        # pristine, so ``is_damaged`` above would have rejected it).
        before = condition_of(item)
        current = item.get_component(ConditionComponent)
        room = room_of(ctx.world, character_id)
        return planned(
            MutationPlan(
                (
                    SetComponent(
                        item.id,
                        replace(
                            current,
                            condition=PRISTINE,
                            restorer_id=str(character_id),
                            restored_at_epoch=ctx.epoch,
                        ),
                    ),
                )
            ),
            PieceRestoredEvent(
                **ctx.event_base(
                    visibility=EventVisibility.ROOM,
                    actor_id=str(character_id),
                    room_id=str(room.id) if room is not None else None,
                    target_ids=(str(item.id),),
                    item_id=str(item.id),
                    restorer_id=str(character_id),
                    condition_before=before,
                    condition_after=PRISTINE,
                )
            )
        )


RESTORE_DEF = ActionDefinition(
    command_type="restore",
    title="Restore collectible",
    description="Restore a damaged collectible within reach to pristine display condition.",
    lane=Lane.WORLD,
    cost=effort_cost(action=ActionEffort.EXTENDED),
    arguments={
        "item_id": ActionArgument(
            title="Collectible",
            description="The damaged collectible to restore.",
            kind="entity",
            required=True,
        ),
    },
)

RESTORATION_ACTION_DEFINITIONS = (RESTORE_DEF,)
RESTORATION_ACTION_HANDLERS = (RestoreHandler,)


__all__ = [
    "PRISTINE",
    "RESTORATION_ACTION_DEFINITIONS",
    "RESTORATION_ACTION_HANDLERS",
    "RESTORE_DEF",
    "ConditionComponent",
    "PieceRestoredEvent",
    "RestoreHandler",
    "condition_of",
    "is_damaged",
]
