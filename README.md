# Bunnyland Museumsim

Out-of-tree [Bunnyland](https://github.com/thalismind/bunnyland-server) plugin about
**collections and curation** — a museum that accepts donations, appraises rarities, and fills
up as the world's players explore. The trophy case for everything the other packs produce.

Items across packs can carry an open `CollectibleComponent(category, rarity)` — a fossil, a
legendary fish, a spirit relic. This package **defines that component itself**, so Museumsim
is a self-contained sink other packs opt into rather than a dependency they must import.

The bundle:

- **Collectible tags** — `CollectibleComponent(category, rarity)` plus a fixed rarity ladder
  (`common` -> `legendary`) with an appraised value per tier.
- **Donation** — a `donate` verb gives a held collectible to a `MuseumComponent` room, which
  records it in a persistent, de-duplicated ledger and refuses duplicates.
- **Appraisal** — an `appraise` verb reports a reachable collectible's category, rarity, and
  value without changing any state.
- **Exhibits & completion** — per-category `ExhibitComponent` entities track wanted vs.
  donated pieces; a light `MuseumConsequence` completes a filled exhibit exactly once, emits
  an event, and raises the donor's standing with the curator (reusing the core `SocialBond`
  reputation layer).
- **Display cases** — donated pieces rest in a `DisplayCaseComponent`, and the museum's prompt
  fragments list the most notable pieces on display plus a running "N of M donated" tally.

A worldgen hook furnishes museum-like generated rooms (curator, exhibits, a display case, and
a few seeded collectibles) and tags collectible-looking generated objects, all deterministically.

This repo intentionally keeps all museum work outside the main `bunnyland-server` repo.

## Layout

- `server/` - Python Bunnyland plugin package with the collectible/museum/exhibit components,
  the donate and appraise verbs, the exhibit-completion consequence, display prompt fragments,
  a worldgen enrichment hook, spawn factories, and tests.

## Server Plugin

The plugin exposes `bunnyland_museumsim.bunnyland_plugins()` and contributes:

- `CollectibleComponent`, `MuseumComponent`, `ExhibitComponent`, `DisplayCaseComponent`.
- `donate` and `appraise` - the two player/AI verbs.
- `MuseumConsequence` - completes filled exhibits and rewards donors each tick.
- `museum_fragments` - renders notable pieces on display and the donation tally into prompts.
- `MuseumWorldgenHook` - furnishes museum rooms and tags collectible objects in generated worlds.
- `spawn_collectible`, `spawn_museum`, `spawn_exhibit`, `spawn_display_case`, `spawn_curator`
  - spawn factories.

## Running

This package builds no containers. It is loaded into the stock server via `--module`:

```bash
bunnyland serve --module bunnyland_museumsim
```

`default_enabled=True`, so no `--plugin` flag is required once the module is imported. The
`bunnyland_museumsim` package must be importable by the server (installed into the server's
environment, or on `PYTHONPATH`).

## Development

Run server tests against a sibling `bunnyland-server` checkout (no install required —
`server/tests/conftest.py` puts both packages on `sys.path`). From `server/`:

```bash
uv run --project ../../bunnyland-server -m pytest
uv run --project ../../bunnyland-server ruff check src tests
```

See [`server/README.md`](server/README.md) for more detail.

## Contributing & Conduct

This plugin follows the Bunnyland project's
[contribution guidelines](CONTRIBUTING.md) and [code of conduct](CODE_OF_CONDUCT.md),
which point back to the `bunnyland-server` repository.

## License

Licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
