"""Out-of-tree Bunnyland plugin: a collection museum.

Items across packs opt into an open :class:`CollectibleComponent`; a ``donate`` verb gives a
held collectible to a :class:`MuseumComponent` room, which records it in a persistent exhibit
and refuses duplicates; an ``appraise`` verb reports a piece's category, rarity, and value; a
per-tick :class:`MuseumConsequence` completes exhibits and rewards donors; and display cases
make a well-stocked museum read richly in prompts.

The v2 expansion adds the headline **authentication / forgeries** mechanic (``authenticate`` a
piece to confirm it is genuine or expose a forgery), **restoration** (``restore`` a damaged
piece), and **visitors/tours** flavor. Donations are routed through core systems by a provenance
reactor — a world-**history** record, a generated display **image** (imagegen), a **memory**
journal line, the donor's deed reputation, and a :class:`PatronOf` typed edge — and a museum that
grows famous raises a storyteller ``famous_exhibit`` incident.
"""

from .appraisal import APPRAISE_DEF, AppraiseHandler
from .authentication import (
    AUTHENTIC,
    AUTHENTICATE_DEF,
    FORGERY,
    UNEXAMINED,
    AuthenticateHandler,
    AuthenticityComponent,
    PieceAuthenticatedEvent,
    authenticity_of,
    verdict_of,
)
from .collectibles import (
    RARITIES,
    RARITY_VALUES,
    collectible_piece_key,
    collectible_value,
    piece_key,
    rarity_rank,
)
from .components import (
    CollectibleComponent,
    ExhibitComponent,
    MuseumComponent,
    MuseumHasCurator,
)
from .display import (
    DisplayCaseComponent,
    display_case_in_room,
    displayed_pieces,
    museum_fragments,
)
from .donation import DONATE_DEF, DonateHandler
from .enrichment import MuseumGenerationEnricher
from .events import PieceAppraisedEvent, PieceDonatedEvent
from .exhibits import (
    COMPLETION_BOND,
    ExhibitCompletedEvent,
    MuseumConsequence,
    exhibit_is_full,
)
from .incidents import FAMOUS_EXHIBIT, FamousExhibitEvent, MuseumStorytellerConsequence
from .install import install_museumsim
from .museum import (
    donation_counts,
    exhibit_for_category,
    exhibits_in_room,
    museum_of,
)
from .patrons import PatronOf, patron_tier, patronage_between, record_patronage
from .plugin import PLUGIN_ID, RECOMMENDED_PACKS, bunnyland_plugins, plugin
from .prefabs import (
    spawn_collectible,
    spawn_curator,
    spawn_display_case,
    spawn_exhibit,
    spawn_museum,
)
from .provenance import MUSEUM_JOURNAL, MuseumProvenanceReactor, install_provenance
from .restoration import (
    RESTORE_DEF,
    ConditionComponent,
    PieceRestoredEvent,
    RestoreHandler,
    condition_of,
    is_damaged,
)
from .spatial import holder_of, room_of
from .visitors import visitor_fragments, visitor_interest

__all__ = [
    "APPRAISE_DEF",
    "AUTHENTIC",
    "AUTHENTICATE_DEF",
    "COMPLETION_BOND",
    "DONATE_DEF",
    "FAMOUS_EXHIBIT",
    "FORGERY",
    "MUSEUM_JOURNAL",
    "PLUGIN_ID",
    "RARITIES",
    "RARITY_VALUES",
    "RECOMMENDED_PACKS",
    "RESTORE_DEF",
    "UNEXAMINED",
    "AppraiseHandler",
    "AuthenticateHandler",
    "AuthenticityComponent",
    "CollectibleComponent",
    "ConditionComponent",
    "DisplayCaseComponent",
    "DonateHandler",
    "ExhibitCompletedEvent",
    "ExhibitComponent",
    "FamousExhibitEvent",
    "MuseumComponent",
    "MuseumHasCurator",
    "MuseumConsequence",
    "MuseumProvenanceReactor",
    "MuseumStorytellerConsequence",
    "MuseumGenerationEnricher",
    "PatronOf",
    "PieceAppraisedEvent",
    "PieceAuthenticatedEvent",
    "PieceDonatedEvent",
    "PieceRestoredEvent",
    "RestoreHandler",
    "authenticity_of",
    "bunnyland_plugins",
    "collectible_piece_key",
    "collectible_value",
    "condition_of",
    "display_case_in_room",
    "displayed_pieces",
    "donation_counts",
    "exhibit_for_category",
    "exhibit_is_full",
    "exhibits_in_room",
    "holder_of",
    "install_museumsim",
    "install_provenance",
    "is_damaged",
    "museum_fragments",
    "museum_of",
    "patron_tier",
    "patronage_between",
    "piece_key",
    "plugin",
    "rarity_rank",
    "record_patronage",
    "room_of",
    "spawn_collectible",
    "spawn_curator",
    "spawn_display_case",
    "spawn_exhibit",
    "spawn_museum",
    "verdict_of",
    "visitor_fragments",
    "visitor_interest",
]
