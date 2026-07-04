"""Runtime wiring: register the per-tick museum consequence on a world actor."""

from __future__ import annotations

from bunnyland.core.world_actor import WorldActor

from .exhibits import MuseumConsequence


def install_museumsim(actor: WorldActor) -> None:
    """Register the exhibit-completion consequence (a ``service_factories`` entry)."""
    actor.register_consequence(MuseumConsequence())


__all__ = ["install_museumsim"]
