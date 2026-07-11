"""Declarative museum furnishing and collectible classification."""

from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    GenerationChild,
    GenerationDelta,
    GenerationRequest,
    HoldableComponent,
    IdentityComponent,
    PortableComponent,
)

from .authentication import AuthenticityComponent
from .components import (
    CollectibleComponent,
    ExhibitComponent,
    MuseumComponent,
    MuseumHasCurator,
)
from .display import DisplayCaseComponent
from .restoration import ConditionComponent

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
CATEGORY_TERMS = (
    ("fossil", ("fossil", "bone", "amber", "prehistoric", "trilobite", "ammonite")),
    ("relic", ("relic", "artifact", "artefact", "antiquity", "idol", "talisman", "tablet")),
    ("art", ("painting", "sculpture", "artwork", "masterpiece", "portrait", "canvas")),
    ("gem", ("gem", "crystal", "jewel", "diamond", "gemstone", "opal")),
    ("specimen", ("specimen", "insect", "butterfly", "herbarium", "pressed flower")),
    ("fish", ("trophy fish", "marlin", "koi", "prize catch")),
)
RARITY_TERMS = (
    ("legendary", ("legendary", "mythic", "fabled")),
    ("epic", ("epic", "priceless", "masterwork")),
    ("rare", ("rare", "precious", "exquisite")),
    ("uncommon", ("uncommon", "unusual", "fine")),
)
SEED_EXHIBITS = (
    ("fossil", ("trilobite", "ammonite", "fern frond")),
    ("relic", ("bronze idol", "clay tablet")),
    ("art", ("still life", "portrait bust")),
)
SEED_COLLECTIBLES = (
    ("trilobite", "fossil", "uncommon", True, None),
    ("bronze idol", "relic", "rare", False, None),
    ("odd curio", "curio", "common", None, 0.4),
)


def _text(request: GenerationRequest) -> str:
    return " ".join(
        (request.source_key, request.entity_kind, request.description, *request.tags)
    ).casefold()


def _first_match(text, table):
    return next(
        (label for label, terms in table if any(term in text for term in terms)),
        None,
    )


def _child(request, key, kind, components, *, additional_edges=()):
    return GenerationChild(
        request=GenerationRequest(
            entity_kind=kind,
            description=key.replace("-", " "),
            source_seed=request.source_seed,
            source_key=f"{request.source_key}:{key}",
            tags=("museumsim",),
        ),
        parent_edge=Contains(mode=ContainmentMode.ROOM_CONTENT),
        additional_parent_edges=additional_edges,
        components=tuple(components),
    )


class MuseumGenerationEnricher:
    capabilities: tuple[str, ...] = ()

    def enrich(self, request: GenerationRequest) -> GenerationDelta:
        text = _text(request)
        if request.entity_kind == "room" and any(term in text for term in MUSEUM_TERMS):
            children = [
                _child(
                    request,
                    "curator",
                    "character",
                    (
                        IdentityComponent(
                            name="Curator",
                            kind="character",
                            tags=("museumsim", "curator"),
                        ),
                        CharacterComponent(),
                    ),
                    additional_edges=(MuseumHasCurator(),),
                ),
                _child(
                    request,
                    "display-case",
                    "display-case",
                    (
                        IdentityComponent(
                            name="display case",
                            kind="display-case",
                            tags=("museumsim",),
                        ),
                        DisplayCaseComponent(),
                    ),
                ),
            ]
            children.extend(
                _child(
                    request,
                    f"{category}-exhibit",
                    "exhibit",
                    (
                        IdentityComponent(
                            name=f"{category} exhibit",
                            kind="exhibit",
                            tags=("museumsim",),
                        ),
                        ExhibitComponent(category=category, required=required),
                    ),
                )
                for category, required in SEED_EXHIBITS
            )
            for name, category, rarity, genuine, condition in SEED_COLLECTIBLES:
                components = [
                    IdentityComponent(
                        name=name,
                        kind="item",
                        tags=("museumsim", "collectible"),
                    ),
                    PortableComponent(),
                    HoldableComponent(slot="hand"),
                    CollectibleComponent(category=category, rarity=rarity),
                ]
                if genuine is not None:
                    components.append(AuthenticityComponent(genuine=genuine))
                if condition is not None:
                    components.append(ConditionComponent(condition=condition))
                children.append(_child(request, name, "item", components))
            return GenerationDelta(
                components=(MuseumComponent(name="Museum"),),
                children=tuple(children),
            )

        if request.entity_kind != "room":
            if any(
                isinstance(component, CollectibleComponent)
                for component in request.context.get("base_components", ())
            ):
                return GenerationDelta()
            category = _first_match(text, CATEGORY_TERMS)
            if category is not None:
                return GenerationDelta(
                    components=(
                        CollectibleComponent(
                            category=category,
                            rarity=_first_match(text, RARITY_TERMS) or "common",
                        ),
                    )
                )
        return GenerationDelta()


__all__ = [
    "CATEGORY_TERMS",
    "MUSEUM_TERMS",
    "MuseumGenerationEnricher",
    "RARITY_TERMS",
    "SEED_COLLECTIBLES",
    "SEED_EXHIBITS",
]
