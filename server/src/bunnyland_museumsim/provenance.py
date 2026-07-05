"""Provenance: route donations and verdicts through core history, imagegen, memory, reputation.

A donation is not just an inventory move — it is a moment worth remembering. The
:class:`MuseumProvenanceReactor` listens on the actor bus and, for each donated piece:

- writes a durable **world-history** provenance record (core ``history``);
- projects the gift onto the donor's **deed reputation** (core ``history``/social standing);
- accrues the donor's :class:`~bunnyland_museumsim.patrons.PatronOf` **typed edge**;
- requests a generated **display image** for the piece (core ``imagegen``); and
- files a line in the museum's **memory** journal, when a memory store is present.

It also records a history line when a piece is **authenticated as a forgery**, so an unmasking
leaves provenance behind. Every core hook degrades gracefully: with no memory store the journal
line is simply skipped, and the reactor never assumes a synergy pack is loaded.
"""

from __future__ import annotations

import logging

from bunnyland.core.ecs import parse_entity_id, replace_component
from bunnyland.imagegen.components import ImageRequestComponent
from bunnyland.imagegen.spec import ImagePurpose
from bunnyland.mechanics.history import apply_deed_reputation, record_world_history
from relics import World

from .authentication import FORGERY, PieceAuthenticatedEvent
from .collectibles import RARITY_VALUES, rarity_rank
from .events import PieceDonatedEvent
from .museum import entity_name, museum_of
from .patrons import record_patronage
from .spatial import room_of

#: Memory collection the museum journals donations and unmaskings into.
MUSEUM_JOURNAL = "museum-log"

_log = logging.getLogger(__name__)


class MuseumProvenanceReactor:
    """Turn donation and authentication events into history, images, and reputation."""

    def __init__(self, actor) -> None:
        self._actor = actor
        self.world: World = actor.world
        self._warned_no_store = False

    def subscribe(self, bus) -> None:
        bus.subscribe(PieceDonatedEvent, self._on_donated)
        bus.subscribe(PieceAuthenticatedEvent, self._on_authenticated)

    # -- helpers -----------------------------------------------------------------------

    @property
    def _store(self):
        return getattr(self._actor, "memory_store", None)

    def _entity(self, raw_id: str | None):
        parsed = parse_entity_id(raw_id or "")
        if parsed is None or not self.world.has_entity(parsed):
            return None
        return self.world.get_entity(parsed)

    def _journal(self, text: str, tags: tuple[str, ...], epoch: int) -> None:
        store = self._store
        if store is None:
            if not self._warned_no_store:
                _log.warning(
                    "museum memory journal disabled: no core memory store installed; "
                    "donations will still be recorded to world history."
                )
                self._warned_no_store = True
            return
        store.add(MUSEUM_JOURNAL, text=text, tags=tags, created_at_epoch=epoch, source="museum")

    # -- donation ----------------------------------------------------------------------

    def _on_donated(self, event: PieceDonatedEvent) -> None:
        piece = self._entity(event.item_id)
        museum = self._entity(event.museum_id)
        if piece is None or museum is None:
            return
        piece_name = entity_name(piece)
        museum_name = museum_of(museum).name if museum_of(museum) is not None else "the museum"
        value = RARITY_VALUES.get(event.rarity, 0)
        summary = f"{piece_name} was donated to {museum_name}."
        tags = ("museum", "donation", event.category, event.rarity)

        record_world_history(
            self.world,
            summary=summary,
            source_event_id=event.event_id,
            event_type="museum.donation",
            created_at_epoch=event.world_epoch,
            location_id=event.museum_id,
            actor_ids=(event.actor_id or "",),
            target_ids=(event.item_id,),
            tags=tags,
            salience=1.0 + rarity_rank(event.rarity) * 0.5,
        )
        if event.actor_id:
            apply_deed_reputation(
                self.world,
                actor_id=event.actor_id,
                deed_id=event.event_id,
                summary=f"Donated {piece_name} to {museum_name}",
                tags=("museum-patron", "generosity"),
                score=0.5 * (rarity_rank(event.rarity) + 1),
            )
            donor_id = parse_entity_id(event.actor_id)
            if donor_id is not None:
                record_patronage(
                    self.world, donor_id, museum.id, value=value, epoch=event.world_epoch
                )
        self._request_display_image(piece, event.museum_id, event.world_epoch)
        self._journal(summary, tags, event.world_epoch)

    def _request_display_image(self, piece, museum_id: str, epoch: int) -> None:
        if piece.has_component(ImageRequestComponent):
            return
        replace_component(
            piece,
            ImageRequestComponent(
                purpose=ImagePurpose.ENTITY.value,
                requested_at_epoch=epoch,
                requested_by=museum_id,
            ),
        )

    # -- authentication ----------------------------------------------------------------

    def _on_authenticated(self, event: PieceAuthenticatedEvent) -> None:
        if event.verdict != FORGERY:
            return
        piece = self._entity(event.item_id)
        if piece is None:
            return
        room = room_of(self.world, piece.id)
        piece_name = entity_name(piece)
        summary = f"{piece_name} was exposed as a forgery."
        tags = ("museum", "forgery")
        record_world_history(
            self.world,
            summary=summary,
            source_event_id=event.event_id,
            event_type="museum.forgery",
            created_at_epoch=event.world_epoch,
            location_id=str(room.id) if room is not None else "",
            actor_ids=(event.examiner_id,),
            target_ids=(event.item_id,),
            tags=tags,
            salience=2.0,
        )
        self._journal(summary, tags, event.world_epoch)


def install_provenance(actor) -> None:
    """Register the provenance reactor on a world actor (a ``service_factories`` entry)."""
    MuseumProvenanceReactor(actor).subscribe(actor.bus)


__all__ = [
    "MUSEUM_JOURNAL",
    "MuseumProvenanceReactor",
    "install_provenance",
]
