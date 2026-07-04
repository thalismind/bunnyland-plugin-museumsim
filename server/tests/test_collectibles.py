from __future__ import annotations

from bunnyland_museumsim import CollectibleComponent
from bunnyland_museumsim.collectibles import (
    RARITIES,
    collectible_piece_key,
    collectible_value,
    piece_key,
    rarity_rank,
)


def test_rarity_rank_is_ascending():
    ranks = [rarity_rank(rarity) for rarity in RARITIES]
    assert ranks == sorted(ranks)
    assert ranks == list(range(len(RARITIES)))


def test_unknown_rarity_ranks_below_all():
    assert rarity_rank("mythic++") == -1


def test_value_rises_with_rarity():
    common = collectible_value(CollectibleComponent(rarity="common"))
    legendary = collectible_value(CollectibleComponent(rarity="legendary"))
    assert 0 < common < legendary


def test_unknown_rarity_has_zero_value():
    assert collectible_value(CollectibleComponent(rarity="nonsense")) == 0


def test_piece_key_is_case_insensitive_and_stable():
    assert piece_key("Fossil", "Trilobite") == piece_key("fossil", "trilobite")
    assert piece_key("fossil", "trilobite") == "fossil/trilobite"


def test_collectible_piece_key_uses_category_and_name():
    component = CollectibleComponent(category="relic", rarity="rare")
    assert collectible_piece_key(component, "Bronze Idol") == "relic/bronze idol"
