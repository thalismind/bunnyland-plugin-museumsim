# bunnyland-museumsim (server plugin)

The out-of-tree Bunnyland plugin package `bunnyland_museumsim`.

## Development

Tests run against a sibling `bunnyland-server` checkout without installing anything —
`tests/conftest.py` puts both this package's `src/` and `../bunnyland-server/src` on
`sys.path`. From this `server/` directory:

```bash
# uses the sibling bunnyland-server's virtualenv/deps
uv run --project ../../bunnyland-server -m pytest
# or, if bunnyland + relics are already importable:
python -m pytest
```

Lint:

```bash
uv run ruff check src tests
```

## Loading into the server

```bash
bunnyland serve --module bunnyland_museumsim
```

`default_enabled=True`, so no `--plugin` flag is required once the module is imported.

## What it contributes

- **Components** — `CollectibleComponent(category, rarity)` (the open opt-in loot tag),
  `MuseumComponent(name, curator_id, donated)` on a room (the donation ledger),
  `ExhibitComponent(category, required, donated, completed, last_donor_id)` on per-category
  exhibit entities, `DisplayCaseComponent` on display cases, `AuthenticityComponent(genuine,
  verdict, ...)` carrying a piece's hidden ground truth and settled verdict, and
  `ConditionComponent(condition, ...)` carrying a piece's physical state.
- **A `PatronOf` typed edge** — a directed `donor -> museum` patronage record (its own index)
  accruing donation count and value; donor recognition is modelled as an edge, never a list.
- **A `donate` verb** — gives a held collectible to the museum in the character's room,
  records it in the ledger and the matching exhibit, refuses duplicates, and moves the piece
  into a display case (or onto the floor).
- **An `appraise` verb** — reports a reachable collectible's category, rarity, and value
  through a `PieceAppraisedEvent`, changing no state.
- **An `authenticate` verb** (headline) — examines a reachable collectible and settles its
  verdict (`authentic`/`forgery`) from the hidden ground truth, emitting `PieceAuthenticatedEvent`.
- **A `restore` verb** — restores a reachable damaged collectible to pristine condition,
  emitting `PieceRestoredEvent`.
- **A `MuseumConsequence`** — each tick completes any newly-filled exhibit exactly once, emits
  `ExhibitCompletedEvent`, and raises the last donor's `SocialBond` standing with the curator.
- **A `MuseumStorytellerConsequence`** — raises a core `famous_exhibit` `IncidentComponent`
  the first time a museum's on-display value becomes a famous draw (idempotent per museum).
- **A `MuseumProvenanceReactor`** — on each donation writes a world-history record, requests a
  generated display image (imagegen), files a memory-journal line (when a store is present),
  projects the donor's deed reputation, and accrues the `PatronOf` edge; it also records a
  history line when a piece is exposed as a forgery.
- **Prompt fragments** — `museum_fragments` lists the most valuable pieces on display and a
  running "N of M donated" tally; `visitor_fragments` describes the crowd (quiet gallery /
  steady stream / guided tour) the museum is drawing.
- **A worldgen hook** — `MuseumWorldgenHook` furnishes museum-like generated rooms (curator,
  exhibits, a display case, seeded collectibles including a hidden forgery and a damaged piece)
  and tags collectible-looking generated objects with `CollectibleComponent`, all deterministically.
- **Spawn factories** — `spawn_collectible` (optionally hidden-authenticity/condition),
  `spawn_museum`, `spawn_exhibit`, `spawn_display_case`, `spawn_curator`.

## Reuses

Inventory + `IdentityComponent` tags for collectibles; the core `SocialBond` reputation layer
(`bunnyland.foundation.social.mechanics`) for donor recognition on exhibit completion; core **history +
imagegen** for provenance and display images; the core **memory** store for the museum journal;
core deed **reputation**; and the core **storyteller** `IncidentComponent` for a famous exhibit.
Synergy source packs are declared only in `DependencyContribution.recommends` — the pack runs
fully standalone on the dependency-free `CollectibleComponent` surface.
