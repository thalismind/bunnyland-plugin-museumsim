"""World-generation enrichment: raise a museum, and tag loot as collectible.

Two independent, deterministic passes so museums appear in generated worlds without the core
generator knowing this plugin exists:

- **Rooms** whose semantic text reads museum-like (gallery, archive, exhibition, ...) are
  furnished into a working museum: a :class:`MuseumComponent`, a curator NPC, a starter set
  of exhibits, a display case, and a few loose collectibles to donate.
- **Objects** whose text names a known collectible kind (fossil, relic, painting, gem, ...)
  get a :class:`CollectibleComponent`, so any pack's generated loot opts into the museum sink.

Both passes are idempotent and free of randomness: category and rarity are chosen by the
first matching term, and already-furnished rooms/objects are left untouched.
"""

from __future__ import annotations

from bunnyland.core.ecs import parse_entity_id, replace_component
from bunnyland.core.events import (
    GeneratedEntityEvent,
    ObjectGeneratedEvent,
    RoomGeneratedEvent,
)
from bunnyland.core.world_actor import WorldActor

from .components import CollectibleComponent, MuseumComponent
from .prefabs import spawn_collectible, spawn_curator, spawn_display_case, spawn_exhibit

#: Words that turn a generated room into a museum.
MUSEUM_TERMS = (
    "museum",
    "gallery",
    "exhibit",
    "exhibition",
    "archive",
    "collection",
    "curator",
    "antiquities",
)

#: Collectible category keyed by the first matching term found in an object's text.
CATEGORY_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("fossil", ("fossil", "bone", "amber", "prehistoric", "trilobite", "ammonite")),
    ("relic", ("relic", "artifact", "artefact", "antiquity", "idol", "talisman", "tablet")),
    ("art", ("painting", "sculpture", "artwork", "masterpiece", "portrait", "canvas")),
    ("gem", ("gem", "crystal", "jewel", "diamond", "gemstone", "opal")),
    ("specimen", ("specimen", "insect", "butterfly", "herbarium", "pressed flower")),
    ("fish", ("trophy fish", "marlin", "koi", "prize catch")),
)

#: Rarity keyed by the first matching term; anything unmatched is ``common``.
RARITY_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("legendary", ("legendary", "mythic", "fabled")),
    ("epic", ("epic", "priceless", "masterwork")),
    ("rare", ("rare", "precious", "exquisite")),
    ("uncommon", ("uncommon", "unusual", "fine")),
)

#: Starter exhibits seeded into a generated museum, each with the pieces it wants.
SEED_EXHIBITS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("fossil", ("trilobite", "ammonite", "fern frond")),
    ("relic", ("bronze idol", "clay tablet")),
    ("art", ("still life", "portrait bust")),
)

#: A few loose collectibles left in a generated museum for players to donate. Each is
#: ``(name, category, rarity, genuine, condition)``: one seeds a hidden forgery to authenticate
#: and one seeds a damaged piece to restore, so the v2 verbs have something to act on out of the
#: box. ``genuine``/``condition`` of ``None`` leaves the piece a plain collectible.
SEED_COLLECTIBLES: tuple[tuple[str, str, str, bool | None, float | None], ...] = (
    ("trilobite", "fossil", "uncommon", True, None),
    ("bronze idol", "relic", "rare", False, None),
    ("odd curio", "curio", "common", None, 0.4),
)


def _text(event: GeneratedEntityEvent) -> str:
    generation = event.generation
    return " ".join(
        (
            event.entity_kind,
            generation.description,
            *generation.tags,
            *generation.wants,
            *generation.needs,
        )
    ).casefold()


def _mentions(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _first_match(text: str, table: tuple[tuple[str, tuple[str, ...]], ...]) -> str | None:
    for label, terms in table:
        if _mentions(text, terms):
            return label
    return None


class MuseumWorldgenHook:
    """Furnish museum rooms and tag collectible objects during world generation."""

    def subscribe(self, actor: WorldActor) -> None:
        self._actor = actor
        actor.bus.subscribe(RoomGeneratedEvent, self._on_room)
        actor.bus.subscribe(ObjectGeneratedEvent, self._on_object)

    def _entity(self, entity_id: str):
        parsed = parse_entity_id(entity_id)
        if parsed is None or not self._actor.world.has_entity(parsed):
            return None
        return self._actor.world.get_entity(parsed)

    def _on_room(self, event: RoomGeneratedEvent) -> None:
        room = self._entity(event.entity_id)
        if room is None or room.has_component(MuseumComponent):
            return
        if not _mentions(_text(event), MUSEUM_TERMS):
            return
        world = self._actor.world
        curator = spawn_curator(world, room_id=room.id, name="Curator")
        replace_component(room, MuseumComponent(name="Museum", curator_id=str(curator.id)))
        spawn_display_case(world, room_id=room.id)
        for category, required in SEED_EXHIBITS:
            spawn_exhibit(world, room_id=room.id, category=category, required=required)
        for piece_name, category, rarity, genuine, condition in SEED_COLLECTIBLES:
            spawn_collectible(
                world,
                room_id=room.id,
                name=piece_name,
                category=category,
                rarity=rarity,
                genuine=genuine,
                condition=condition,
            )

    def _on_object(self, event: ObjectGeneratedEvent) -> None:
        entity = self._entity(event.entity_id)
        if entity is None or entity.has_component(CollectibleComponent):
            return
        text = _text(event)
        category = _first_match(text, CATEGORY_TERMS)
        if category is None:
            return
        rarity = _first_match(text, RARITY_TERMS) or "common"
        replace_component(entity, CollectibleComponent(category=category, rarity=rarity))


__all__ = [
    "CATEGORY_TERMS",
    "MUSEUM_TERMS",
    "RARITY_TERMS",
    "SEED_COLLECTIBLES",
    "SEED_EXHIBITS",
    "MuseumWorldgenHook",
]
