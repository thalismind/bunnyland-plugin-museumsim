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
  exhibit entities, and `DisplayCaseComponent` on display cases.
- **A `donate` verb** — gives a held collectible to the museum in the character's room,
  records it in the ledger and the matching exhibit, refuses duplicates, and moves the piece
  into a display case (or onto the floor).
- **An `appraise` verb** — reports a reachable collectible's category, rarity, and value
  through a `PieceAppraisedEvent`, changing no state.
- **A `MuseumConsequence`** — each tick completes any newly-filled exhibit exactly once, emits
  `ExhibitCompletedEvent`, and raises the last donor's `SocialBond` standing with the curator.
- **Prompt fragments** — `museum_fragments` lists the most valuable pieces on display and a
  running "N of M donated" tally when a character stands in a museum.
- **A worldgen hook** — `MuseumWorldgenHook` furnishes museum-like generated rooms (curator,
  exhibits, a display case, seeded collectibles) and tags collectible-looking generated
  objects with `CollectibleComponent`, all deterministically.
- **Spawn factories** — `spawn_collectible`, `spawn_museum`, `spawn_exhibit`,
  `spawn_display_case`, `spawn_curator`.

## Reuses

Inventory + `IdentityComponent` tags for collectibles, and the core `SocialBond` reputation
layer (`bunnyland.mechanics.social`) for donor recognition on exhibit completion.
