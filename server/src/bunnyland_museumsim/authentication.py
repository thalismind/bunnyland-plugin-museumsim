"""The headline v2 mechanic: authentication and forgeries.

Every collectible has a hidden ground truth — it is either the real thing or a forgery — carried
on an :class:`AuthenticityComponent`. Curators (or anyone) settle the question with the
``authenticate`` verb: examining a piece resolves its verdict deterministically from that hidden
truth and stamps who examined it and when. A piece with no authenticity record is taken to be
genuine but simply *unexamined* until someone looks; examining it records the verdict.

The verdict is what turns an anonymous donation into provenance: a confirmed forgery is a notable
world moment (recorded to history by the donation reactor and surfaced through the storyteller),
while a confirmed genuine piece earns its place on display.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core.actions import ActionArgument, ActionDefinition
from bunnyland.core.commands import CommandCost, Lane, SubmittedCommand
from bunnyland.core.ecs import replace_component
from bunnyland.core.events import DomainEvent, EventVisibility
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    ok,
    rejected,
    require_character,
    require_reachable_entity,
)
from bunnyland.prompts import ComponentPromptContext
from pydantic.dataclasses import dataclass
from relics import Component, Entity

from .components import CollectibleComponent
from .spatial import room_of

#: Verdict a piece carries before anyone examines it.
UNEXAMINED = "unexamined"
#: Verdict for a piece examination has confirmed genuine.
AUTHENTIC = "authentic"
#: Verdict for a piece examination has exposed as a forgery.
FORGERY = "forgery"


@dataclass(frozen=True)
class AuthenticityComponent(Component):
    """A collectible's hidden authenticity plus the verdict any examination reached.

    ``genuine`` is the ground truth set when the piece is created; ``verdict`` starts
    :data:`UNEXAMINED` and flips to :data:`AUTHENTIC` or :data:`FORGERY` the first time the piece
    is authenticated. ``examiner_id``/``examined_at_epoch`` stamp who settled it.
    """

    genuine: bool = True
    verdict: str = UNEXAMINED
    examiner_id: str = ""
    examined_at_epoch: int = 0

    def prompt_fragments(self, ctx: ComponentPromptContext) -> tuple[str, ...]:
        if self.verdict == UNEXAMINED:
            return ("This piece has not been authenticated.",)
        if self.verdict == FORGERY:
            return ("This piece has been exposed as a forgery.",)
        return ("This piece has been authenticated as genuine.",)


class PieceAuthenticatedEvent(DomainEvent):
    """A character authenticated a collectible, settling its verdict."""

    item_id: str
    verdict: str
    genuine: bool
    examiner_id: str


def authenticity_of(entity: Entity) -> AuthenticityComponent:
    """The piece's authenticity record, or a default (genuine, unexamined) one."""
    if entity.has_component(AuthenticityComponent):
        return entity.get_component(AuthenticityComponent)
    return AuthenticityComponent()


def verdict_of(entity: Entity) -> str:
    """The verdict recorded on ``entity`` (``UNEXAMINED`` when never examined)."""
    return authenticity_of(entity).verdict


class AuthenticateHandler:
    """Examine a reachable collectible and settle whether it is genuine or a forgery."""

    command_type = "authenticate"

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

        current = authenticity_of(item)
        if current.verdict != UNEXAMINED:
            return rejected("that piece has already been authenticated")

        verdict = AUTHENTIC if current.genuine else FORGERY
        replace_component(
            item,
            replace(
                current,
                verdict=verdict,
                examiner_id=str(character_id),
                examined_at_epoch=ctx.epoch,
            ),
        )
        room = room_of(ctx.world, character_id)
        return ok(
            PieceAuthenticatedEvent(
                **ctx.event_base(
                    visibility=EventVisibility.ROOM,
                    actor_id=str(character_id),
                    room_id=str(room.id) if room is not None else None,
                    target_ids=(str(item.id),),
                    item_id=str(item.id),
                    verdict=verdict,
                    genuine=current.genuine,
                    examiner_id=str(character_id),
                )
            )
        )


AUTHENTICATE_DEF = ActionDefinition(
    command_type="authenticate",
    title="Authenticate collectible",
    description="Examine a collectible within reach to confirm it is genuine or expose a forgery.",
    lane=Lane.WORLD,
    cost=CommandCost(action=1),
    arguments={
        "item_id": ActionArgument(
            title="Collectible",
            description="The collectible to authenticate.",
            kind="entity",
            required=True,
        ),
    },
)

AUTHENTICATION_ACTION_DEFINITIONS = (AUTHENTICATE_DEF,)
AUTHENTICATION_ACTION_HANDLERS = (AuthenticateHandler,)


__all__ = [
    "AUTHENTIC",
    "AUTHENTICATE_DEF",
    "AUTHENTICATION_ACTION_DEFINITIONS",
    "AUTHENTICATION_ACTION_HANDLERS",
    "FORGERY",
    "UNEXAMINED",
    "AuthenticateHandler",
    "AuthenticityComponent",
    "PieceAuthenticatedEvent",
    "authenticity_of",
    "verdict_of",
]
