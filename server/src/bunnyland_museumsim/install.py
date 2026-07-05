"""Runtime wiring: register the per-tick consequences and the provenance reactor."""

from __future__ import annotations

from bunnyland.core.world_actor import WorldActor

from .exhibits import MuseumConsequence
from .incidents import MuseumStorytellerConsequence
from .provenance import install_provenance


def install_museumsim(actor: WorldActor) -> None:
    """Register museum consequences and the provenance reactor (a ``service_factories`` entry)."""
    actor.register_consequence(MuseumConsequence())
    actor.register_consequence(MuseumStorytellerConsequence())
    install_provenance(actor)


__all__ = ["install_museumsim"]
