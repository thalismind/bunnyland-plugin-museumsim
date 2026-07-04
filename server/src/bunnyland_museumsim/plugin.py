"""Bunnyland plugin entrypoint for the out-of-tree museumsim collection pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .appraisal import APPRAISAL_ACTION_DEFINITIONS, APPRAISAL_ACTION_HANDLERS
from .components import CollectibleComponent, ExhibitComponent, MuseumComponent
from .display import DisplayCaseComponent, museum_fragments
from .donation import DONATION_ACTION_DEFINITIONS, DONATION_ACTION_HANDLERS
from .enrichment import MuseumWorldgenHook
from .events import PieceAppraisedEvent, PieceDonatedEvent
from .exhibits import ExhibitCompletedEvent
from .install import install_museumsim

PLUGIN_ID = "bunnyland.museumsim"


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Museumsim",
        version="0.1.0",
        default_enabled=True,
        ecs=EcsContribution(
            components=(
                CollectibleComponent,
                MuseumComponent,
                ExhibitComponent,
                DisplayCaseComponent,
            ),
        ),
        commands=CommandContribution(
            action_handlers=DONATION_ACTION_HANDLERS + APPRAISAL_ACTION_HANDLERS,
            action_definitions=DONATION_ACTION_DEFINITIONS + APPRAISAL_ACTION_DEFINITIONS,
            typed_events=(
                PieceDonatedEvent,
                PieceAppraisedEvent,
                ExhibitCompletedEvent,
            ),
        ),
        runtime=RuntimeContribution(
            service_factories=(install_museumsim,),
        ),
        content=ContentContribution(
            prompt_fragments=(museum_fragments,),
            worldgen_hooks=(MuseumWorldgenHook,),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "bunnyland_plugins", "plugin"]
