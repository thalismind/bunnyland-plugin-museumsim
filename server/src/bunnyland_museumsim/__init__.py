"""Out-of-tree Bunnyland plugin: a collection museum.

Items across packs opt into an open :class:`CollectibleComponent`; a ``donate`` verb gives a
held collectible to a :class:`MuseumComponent` room, which records it in a persistent exhibit
and refuses duplicates; an ``appraise`` verb reports a piece's category, rarity, and value; a
per-tick :class:`MuseumConsequence` completes exhibits and rewards donors; and display cases
make a well-stocked museum read richly in prompts.
"""

from .appraisal import APPRAISE_DEF, AppraiseHandler
from .collectibles import (
    RARITIES,
    RARITY_VALUES,
    collectible_piece_key,
    collectible_value,
    piece_key,
    rarity_rank,
)
from .components import CollectibleComponent, ExhibitComponent, MuseumComponent
from .display import (
    DisplayCaseComponent,
    display_case_in_room,
    displayed_pieces,
    museum_fragments,
)
from .donation import DONATE_DEF, DonateHandler
from .enrichment import MuseumWorldgenHook
from .events import PieceAppraisedEvent, PieceDonatedEvent
from .exhibits import (
    COMPLETION_BOND,
    ExhibitCompletedEvent,
    MuseumConsequence,
    exhibit_is_full,
)
from .install import install_museumsim
from .museum import (
    donation_counts,
    exhibit_for_category,
    exhibits_in_room,
    museum_of,
)
from .plugin import PLUGIN_ID, bunnyland_plugins, plugin
from .prefabs import (
    spawn_collectible,
    spawn_curator,
    spawn_display_case,
    spawn_exhibit,
    spawn_museum,
)
from .spatial import holder_of, room_of

__all__ = [
    "APPRAISE_DEF",
    "COMPLETION_BOND",
    "DONATE_DEF",
    "PLUGIN_ID",
    "RARITIES",
    "RARITY_VALUES",
    "AppraiseHandler",
    "CollectibleComponent",
    "DisplayCaseComponent",
    "DonateHandler",
    "ExhibitCompletedEvent",
    "ExhibitComponent",
    "MuseumComponent",
    "MuseumConsequence",
    "MuseumWorldgenHook",
    "PieceAppraisedEvent",
    "PieceDonatedEvent",
    "bunnyland_plugins",
    "collectible_piece_key",
    "collectible_value",
    "display_case_in_room",
    "displayed_pieces",
    "donation_counts",
    "exhibit_for_category",
    "exhibit_is_full",
    "exhibits_in_room",
    "holder_of",
    "install_museumsim",
    "museum_fragments",
    "museum_of",
    "piece_key",
    "plugin",
    "rarity_rank",
    "room_of",
    "spawn_collectible",
    "spawn_curator",
    "spawn_display_case",
    "spawn_exhibit",
    "spawn_museum",
]
