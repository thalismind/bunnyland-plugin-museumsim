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

The v2 expansion makes the museum feel like part of one living world:

- **Authentication & forgeries** (headline) — every collectible carries a hidden ground truth
  on an `AuthenticityComponent`; an `authenticate` verb examines a reachable piece and settles
  whether it is genuine or a forgery. An exposed forgery becomes a notable world moment.
- **Restoration** — a damaged piece carries a `ConditionComponent`; a `restore` verb brings it
  back to pristine display condition and stamps who did the work.
- **Visitors & tours** — atmospheric prompt lines (a quiet gallery, a steady stream, a guided
  tour around the star piece) derived deterministically from what is on display; no ticketing
  or admission accounting.
- **Provenance through core systems** — each donation writes a world-**history** record,
  requests a generated display **image** (imagegen), files a **memory** journal line, projects
  the donor's deed **reputation**, and accrues a `PatronOf` typed edge for donor recognition.
- **Storyteller** — when a museum's collection grows into a famous draw, it raises a core
  `famous_exhibit` incident so world pressure is paced and other packs can react.

A worldgen hook furnishes museum-like generated rooms (curator, exhibits, a display case, and
a few seeded collectibles — including a hidden forgery and a damaged piece so the v2 verbs have
something to act on) and tags collectible-looking generated objects, all deterministically.

### Verbs

- `donate` — give a held collectible to the museum you stand in.
- `appraise` — read a reachable collectible's category, rarity, and value (no state change).
- `authenticate` — examine a reachable collectible to confirm it is genuine or expose a forgery.
- `restore` — restore a reachable damaged collectible to pristine condition.

### Synergy (optional)

Museumsim reads the dependency-free `CollectibleComponent` surface, so it runs fully standalone.
It only *recommends* collection-source packs (anglersim, wildsim, aquasim, loresim, cryptidsim)
to light up wings fed by other packs — never requires them.

This repo intentionally keeps all museum work outside the main `bunnyland-server` repo.

## Layout

- `server/` - Python Bunnyland plugin package with the collectible/museum/exhibit components,
  the donate and appraise verbs, the exhibit-completion consequence, display prompt fragments,
  a worldgen enrichment hook, spawn factories, and tests.

## Server Plugin

The plugin exposes `bunnyland_museumsim.bunnyland_plugins()` and contributes:

- `CollectibleComponent`, `MuseumComponent`, `ExhibitComponent`, `DisplayCaseComponent`,
  `AuthenticityComponent`, `ConditionComponent`, and the `PatronOf` typed edge.
- `donate`, `appraise`, `authenticate`, and `restore` - the four player/AI verbs.
- `MuseumConsequence` - completes filled exhibits and rewards donors each tick.
- `MuseumStorytellerConsequence` - raises a `famous_exhibit` incident when a museum becomes a draw.
- `MuseumProvenanceReactor` - routes donations/verdicts through core history, imagegen, memory,
  and reputation.
- `museum_fragments` and `visitor_fragments` - render notable pieces, the donation tally, and
  the current crowd into prompts.
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
