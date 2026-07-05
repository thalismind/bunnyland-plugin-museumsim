from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_museumsim import (
    AuthenticityComponent,
    CollectibleComponent,
    ConditionComponent,
    DisplayCaseComponent,
    ExhibitComponent,
    MuseumComponent,
    MuseumWorldgenHook,
    PatronOf,
    PieceAuthenticatedEvent,
    PieceRestoredEvent,
    museum_fragments,
    visitor_fragments,
)
from bunnyland_museumsim.plugin import PLUGIN_ID, RECOMMENDED_PACKS, plugin


def test_plugin_loads_with_module_qualified_id():
    plugins = load_modules(["bunnyland_museumsim"])
    assert [p.id for p in plugins] == [PLUGIN_ID]


def test_plugin_is_version_two():
    assert plugin().version == "0.2.0"


def test_plugin_declares_its_components():
    plugin = load_modules(["bunnyland_museumsim"])[0]
    for component in (
        CollectibleComponent,
        MuseumComponent,
        ExhibitComponent,
        DisplayCaseComponent,
        AuthenticityComponent,
        ConditionComponent,
    ):
        assert component in plugin.ecs.components


def test_plugin_declares_the_patron_edge():
    plugin = load_modules(["bunnyland_museumsim"])[0]
    assert PatronOf in plugin.ecs.edges


def test_plugin_declares_v2_events():
    plugin = load_modules(["bunnyland_museumsim"])[0]
    assert PieceAuthenticatedEvent in plugin.commands.typed_events
    assert PieceRestoredEvent in plugin.commands.typed_events


def test_plugin_recommends_collection_source_packs_without_requiring_them():
    plugin = load_modules(["bunnyland_museumsim"])[0]
    assert set(plugin.dependencies.recommends) == set(RECOMMENDED_PACKS)
    assert not plugin.dependencies.requires


def test_plugin_declares_content():
    plugin = load_modules(["bunnyland_museumsim"])[0]
    assert MuseumWorldgenHook in plugin.content.worldgen_hooks
    assert museum_fragments in plugin.content.prompt_fragments
    assert visitor_fragments in plugin.content.prompt_fragments


def test_plugin_applies_and_registers_verbs():
    actor = WorldActor()
    applied = apply_plugins(load_modules(["bunnyland_museumsim"]), actor)
    assert applied[0].id == PLUGIN_ID
    command_types = {definition.command_type for definition in actor.action_definitions()}
    assert {"donate", "appraise", "authenticate", "restore"} <= command_types
