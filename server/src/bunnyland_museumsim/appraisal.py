"""The ``appraise`` verb: read a reachable collectible's category, rarity, and value.

Appraisal is pure inspection — it changes no state. It resolves a collectible the character
can reach (held or in the room), then reports its details through a
:class:`~bunnyland_museumsim.events.PieceAppraisedEvent`. Validation order: invalid character
-> missing character -> invalid item -> missing item -> unreachable -> not a collectible.
"""

from __future__ import annotations

from bunnyland.core.actions import ActionArgument, ActionDefinition
from bunnyland.core.commands import CommandCost, Lane, SubmittedCommand
from bunnyland.core.events import EventVisibility
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    ok,
    rejected,
    require_character,
    require_reachable_entity,
)

from .collectibles import collectible_value
from .components import CollectibleComponent
from .events import PieceAppraisedEvent
from .spatial import room_of


class AppraiseHandler:
    """Report the category, rarity, and appraised value of a reachable collectible."""

    command_type = "appraise"

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

        collectible = item.get_component(CollectibleComponent)
        room = room_of(ctx.world, character_id)
        return ok(
            PieceAppraisedEvent(
                **ctx.event_base(
                    visibility=EventVisibility.PRIVATE,
                    actor_id=str(character_id),
                    room_id=str(room.id) if room is not None else None,
                    target_ids=(str(item.id),),
                    item_id=str(item.id),
                    category=collectible.category,
                    rarity=collectible.rarity,
                    value=collectible_value(collectible),
                )
            )
        )


APPRAISE_DEF = ActionDefinition(
    command_type="appraise",
    title="Appraise collectible",
    description="Inspect a collectible within reach to learn its category, rarity, and value.",
    lane=Lane.WORLD,
    cost=CommandCost(action=1),
    arguments={
        "item_id": ActionArgument(
            title="Collectible",
            description="The collectible to appraise.",
            kind="entity",
            required=True,
        ),
    },
)

APPRAISAL_ACTION_DEFINITIONS = (APPRAISE_DEF,)
APPRAISAL_ACTION_HANDLERS = (AppraiseHandler,)


__all__ = [
    "APPRAISAL_ACTION_DEFINITIONS",
    "APPRAISAL_ACTION_HANDLERS",
    "APPRAISE_DEF",
    "AppraiseHandler",
]
