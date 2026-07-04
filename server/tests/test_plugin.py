from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_museumsim import (
    CollectibleComponent,
    DisplayCaseComponent,
    ExhibitComponent,
    MuseumComponent,
    MuseumWorldgenHook,
    museum_fragments,
)
from bunnyland_museumsim.plugin import PLUGIN_ID


def test_plugin_loads_with_module_qualified_id():
    plugins = load_modules(["bunnyland_museumsim"])
    assert [p.id for p in plugins] == [f"bunnyland_museumsim.{PLUGIN_ID}"]


def test_plugin_declares_its_components():
    plugin = load_modules(["bunnyland_museumsim"])[0]
    for component in (
        CollectibleComponent,
        MuseumComponent,
        ExhibitComponent,
        DisplayCaseComponent,
    ):
        assert component in plugin.ecs.components


def test_plugin_declares_content():
    plugin = load_modules(["bunnyland_museumsim"])[0]
    assert MuseumWorldgenHook in plugin.content.worldgen_hooks
    assert museum_fragments in plugin.content.prompt_fragments


def test_plugin_applies_and_registers_verbs():
    actor = WorldActor()
    applied = apply_plugins(load_modules(["bunnyland_museumsim"]), actor)
    assert applied[0].id == f"bunnyland_museumsim.{PLUGIN_ID}"
    command_types = {definition.command_type for definition in actor.action_definitions()}
    assert {"donate", "appraise"} <= command_types
