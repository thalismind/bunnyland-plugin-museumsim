"""The ``donate`` verb: give a held collectible to the museum you stand in.

Validation follows the project order: invalid character -> missing character -> invalid item
-> missing item -> not held -> not a collectible -> no museum here -> duplicate -> apply.

On success the piece is:

1. recorded in the room's :class:`MuseumComponent` ledger as a de-duplicated ``piece_key``
   (so donating the same piece twice is refused),
2. recorded in the matching :class:`ExhibitComponent` (by category, if one exists), with the
   donor stamped as ``last_donor_id`` for later reputation recognition, and
3. re-parented out of the donor's hands into a display case (or, lacking one, onto the museum
   floor), where the display fragments will describe it.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import ContainmentMode, Contains
from bunnyland.core.actions import ActionArgument, ActionDefinition
from bunnyland.core.commands import CommandCost, Lane, SubmittedCommand
from bunnyland.core.ecs import remove_from_container, replace_component
from bunnyland.core.events import EventVisibility
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    ok,
    rejected,
    require_character,
    require_entity,
)

from .collectibles import collectible_piece_key
from .components import CollectibleComponent, ExhibitComponent, MuseumComponent
from .display import display_case_in_room
from .events import PieceDonatedEvent
from .museum import entity_name, exhibit_for_category
from .spatial import holder_of, room_of


class DonateHandler:
    """Donate a held collectible to the museum in the character's current room."""

    command_type = "donate"

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id, _character, rejection = require_character(ctx, command.character_id)
        if rejection is not None:
            return rejection
        item_id, item, rejection = require_entity(
            ctx,
            command.payload.get("item_id"),
            invalid_reason="invalid item id",
            missing_reason="item does not exist",
        )
        if rejection is not None:
            return rejection
        holder = holder_of(ctx.world, item_id)
        if holder is None or holder.id != character_id:
            return rejected("you are not holding that")
        if not item.has_component(CollectibleComponent):
            return rejected("that is not a collectible")
        room = room_of(ctx.world, character_id)
        if room is None or not room.has_component(MuseumComponent):
            return rejected("there is no museum here")

        collectible = item.get_component(CollectibleComponent)
        name = entity_name(item)
        key = collectible_piece_key(collectible, name)
        museum = room.get_component(MuseumComponent)
        if key in museum.donated:
            return rejected("that piece is already in the collection")

        self._record(ctx, room, museum, collectible, name, key, str(character_id))
        self._display(ctx, room, item)
        return ok(
            PieceDonatedEvent(
                **ctx.event_base(
                    visibility=EventVisibility.ROOM,
                    actor_id=str(character_id),
                    room_id=str(room.id),
                    target_ids=(str(item.id),),
                    item_id=str(item.id),
                    museum_id=str(room.id),
                    category=collectible.category,
                    rarity=collectible.rarity,
                )
            )
        )

    def _record(self, ctx, room, museum, collectible, name, key, donor_id) -> None:
        replace_component(room, replace(museum, donated=tuple(sorted((*museum.donated, key)))))
        exhibit = exhibit_for_category(ctx.world, room, collectible.category)
        if exhibit is not None:
            component = exhibit.get_component(ExhibitComponent)
            merged = tuple(sorted(dict.fromkeys((*component.donated, name))))
            replace_component(exhibit, replace(component, donated=merged, last_donor_id=donor_id))

    def _display(self, ctx, room, item) -> None:
        remove_from_container(ctx.world, item.id)
        case = display_case_in_room(ctx.world, room)
        if case is not None:
            case.add_relationship(Contains(mode=ContainmentMode.CONTAINER), item.id)
        else:
            room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), item.id)


DONATE_DEF = ActionDefinition(
    command_type="donate",
    title="Donate collectible",
    description="Donate a collectible you are holding to the museum you are standing in.",
    lane=Lane.WORLD,
    cost=CommandCost(action=1),
    arguments={
        "item_id": ActionArgument(
            title="Collectible",
            description="The collectible you are holding to donate.",
            kind="entity",
            required=True,
        ),
    },
)

DONATION_ACTION_DEFINITIONS = (DONATE_DEF,)
DONATION_ACTION_HANDLERS = (DonateHandler,)


__all__ = [
    "DONATE_DEF",
    "DONATION_ACTION_DEFINITIONS",
    "DONATION_ACTION_HANDLERS",
    "DonateHandler",
]
