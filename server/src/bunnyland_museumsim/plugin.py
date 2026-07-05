"""Bunnyland plugin entrypoint for the out-of-tree museumsim collection pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    DependencyContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .appraisal import APPRAISAL_ACTION_DEFINITIONS, APPRAISAL_ACTION_HANDLERS
from .authentication import (
    AUTHENTICATION_ACTION_DEFINITIONS,
    AUTHENTICATION_ACTION_HANDLERS,
    AuthenticityComponent,
    PieceAuthenticatedEvent,
)
from .components import CollectibleComponent, ExhibitComponent, MuseumComponent
from .display import DisplayCaseComponent, museum_fragments
from .donation import DONATION_ACTION_DEFINITIONS, DONATION_ACTION_HANDLERS
from .enrichment import MuseumWorldgenHook
from .events import PieceAppraisedEvent, PieceDonatedEvent
from .exhibits import ExhibitCompletedEvent
from .incidents import FamousExhibitEvent
from .install import install_museumsim
from .patrons import PatronOf
from .restoration import (
    RESTORATION_ACTION_DEFINITIONS,
    RESTORATION_ACTION_HANDLERS,
    ConditionComponent,
    PieceRestoredEvent,
)
from .visitors import visitor_fragments

PLUGIN_ID = "bunnyland.museumsim"

#: Optional synergy packs the museum consumes as a collection sink. Museumsim reads the
#: dependency-free ``CollectibleComponent`` surface, so it runs fully standalone; these are only
#: *recommended* to light up wings fed by other packs — never required.
RECOMMENDED_PACKS = (
    "bunnyland.anglersim",
    "bunnyland.wildsim",
    "bunnyland.aquasim",
    "bunnyland.loresim",
    "bunnyland.cryptidsim",
)


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Museumsim",
        version="0.2.0",
        default_enabled=True,
        dependencies=DependencyContribution(recommends=RECOMMENDED_PACKS),
        ecs=EcsContribution(
            components=(
                CollectibleComponent,
                MuseumComponent,
                ExhibitComponent,
                DisplayCaseComponent,
                AuthenticityComponent,
                ConditionComponent,
            ),
            edges=(PatronOf,),
        ),
        commands=CommandContribution(
            action_handlers=(
                DONATION_ACTION_HANDLERS
                + APPRAISAL_ACTION_HANDLERS
                + AUTHENTICATION_ACTION_HANDLERS
                + RESTORATION_ACTION_HANDLERS
            ),
            action_definitions=(
                DONATION_ACTION_DEFINITIONS
                + APPRAISAL_ACTION_DEFINITIONS
                + AUTHENTICATION_ACTION_DEFINITIONS
                + RESTORATION_ACTION_DEFINITIONS
            ),
            typed_events=(
                PieceDonatedEvent,
                PieceAppraisedEvent,
                ExhibitCompletedEvent,
                PieceAuthenticatedEvent,
                PieceRestoredEvent,
                FamousExhibitEvent,
            ),
        ),
        runtime=RuntimeContribution(
            service_factories=(install_museumsim,),
        ),
        content=ContentContribution(
            prompt_fragments=(museum_fragments, visitor_fragments),
            worldgen_hooks=(MuseumWorldgenHook,),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "RECOMMENDED_PACKS", "bunnyland_plugins", "plugin"]
