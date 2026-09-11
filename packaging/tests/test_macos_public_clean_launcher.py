import tempfile
import unittest
from pathlib import Path
from unittest import mock

import launcher


class MacOSPublicCleanLauncherTest(unittest.TestCase):
    def test_launcher_marks_engine_content_cancel_as_return_to_launcher(self):
        self.assertEqual(
            ["Game.ContentManagerReturnToLauncher=true"],
            launcher.with_content_manager_return_policy([]),
        )

    def test_game_process_exit_restores_launcher_home(self):
        target = object.__new__(launcher.Launcher)
        target._game_process = mock.Mock()
        target._game_process.poll.return_value = 0
        target.deiconify = mock.Mock()
        target.lift = mock.Mock()
        target.focus_force = mock.Mock()
        target.show_page = mock.Mock()
        target._set_launch_status = mock.Mock()

        target._watch_game_process()

        target.deiconify.assert_called_once()
        target.show_page.assert_called_once_with("home")
        target._set_launch_status.assert_called_once()

    def test_build_pages_defers_skirmish_until_first_navigation(self):
        target = object.__new__(launcher.Launcher)
        target.content = object()
        target.pages = {}
        page_keys = (
            "notice", "home", "display", "audio", "input", "hotkeys",
            "ai", "advanced", "tools", "replays", "saves", "maps",
            "content", "credits", "skirmish", "net",
        )
        builders = {}
        for key in page_keys:
            builder = mock.Mock(name=f"page_{key}")
            setattr(target, f"_page_{key}", builder)
            builders[key] = builder
        target._scrollable = mock.Mock(side_effect=lambda page, _key: page)

        with mock.patch("launcher.tk.Frame", side_effect=[mock.Mock() for _ in page_keys]):
            target._build_pages()

        builders["notice"].assert_called_once()
        builders["content"].assert_called_once()
        builders["skirmish"].assert_not_called()
        self.assertIn("skirmish", target.pages)
        self.assertNotIn("skirmish", target._built_pages)

    def test_empty_skirmish_map_catalog_has_disabled_placeholder(self):
        values, ready = launcher.skirmish_map_menu_state([])

        self.assertEqual([launcher._tr("尚无可用地图")], values)
        self.assertFalse(ready)

    def test_nonempty_skirmish_map_catalog_preserves_labels(self):
        labels = ["Arena（2 人）", "Oasis（4 人）"]

        values, ready = launcher.skirmish_map_menu_state(labels)

        self.assertEqual(labels, values)
        self.assertTrue(ready)

    @mock.patch("launcher.messagebox.showinfo")
    @mock.patch("launcher.ra2_files.import_retail_content")
    def test_retail_import_invalidates_skirmish_page(self, import_content, _showinfo):
        import_content.return_value = {"healthy": True, "missing_core": []}
        target = object.__new__(launcher.Launcher)
        target._content_refresh = mock.Mock()
        target._invalidate_page = mock.Mock()

        target._import_retail_sources(["/legal/game"])

        target._invalidate_page.assert_called_once_with("skirmish")

    @mock.patch("launcher.messagebox.showinfo")
    @mock.patch("launcher.filedialog.askopenfilename", return_value="/legal/map.oramap")
    @mock.patch("launcher.ra2_files.import_map", return_value="/support/maps/map.oramap")
    def test_map_import_invalidates_skirmish_page(
            self, _import_map, _askopenfilename, _showinfo):
        target = object.__new__(launcher.Launcher)
        target._maps_refresh = mock.Mock()
        target._invalidate_page = mock.Mock()

        target._import_map()

        target._invalidate_page.assert_called_once_with("skirmish")

    def test_startup_notice_precedes_the_existing_content_route(self):
        self.assertEqual("notice", launcher.startup_page())
        self.assertEqual("notice", launcher.guarded_page("home", acknowledged=False))
        self.assertEqual("home", launcher.guarded_page("home", acknowledged=True))

    def test_first_start_opens_content_page_until_minimum_is_ready(self):
        self.assertEqual("content", launcher.initial_page("home", content_ready=False))
        self.assertEqual("home", launcher.initial_page("home", content_ready=True))
        self.assertEqual("content", launcher.initial_page("content", content_ready=True))

    def test_accepting_notice_unlocks_and_routes_to_the_saved_target(self):
        target = object.__new__(launcher.Launcher)
        target.startup_notice_acknowledged = False
        target.post_notice_page = "content"
        target.show_page = mock.Mock()

        target._accept_startup_notice()

        self.assertTrue(target.startup_notice_acknowledged)
        target.show_page.assert_called_once_with("content")

    def test_runtime_root_uses_source_file_outside_frozen_app(self):
        root = launcher.runtime_root(
            frozen=False,
            source_file="/workspace/ra2-mac/launcher.py",
        )

        self.assertEqual("/workspace/ra2-mac", root)

    def test_runtime_root_uses_app_resources_when_frozen(self):
        root = launcher.runtime_root(
            frozen=True,
            executable="/Applications/NUKE HOUR.app/Contents/MacOS/NUKE HOUR",
            meipass="/ignored/_internal",
        )

        self.assertEqual(
            "/Applications/NUKE HOUR.app/Contents/Resources/runtime",
            root,
        )

    def test_runtime_binding_updates_file_management_module(self):
        original = launcher.ra2_files.REPO
        self.addCleanup(setattr, launcher.ra2_files, "REPO", original)

        launcher.bind_runtime_modules("/Applications/NUKE HOUR.app/Contents/Resources/runtime")

        self.assertEqual(
            "/Applications/NUKE HOUR.app/Contents/Resources/runtime",
            launcher.ra2_files.REPO,
        )

    def test_embedded_game_command_precedes_system_runtime(self):
        with tempfile.TemporaryDirectory(prefix="nukehour-runtime-test-") as temporary:
            root = Path(temporary)
            host = root / "NUKE HOUR GAME.app/Contents/MacOS/NuclearCrisis"
            host.parent.mkdir(parents=True)
            host.write_bytes(b"host")
            hostfxr = root / "dotnet/host/fxr/8.0.27/libhostfxr.dylib"
            hostfxr.parent.mkdir(parents=True)
            hostfxr.write_bytes(b"fxr")
            dll = root / "engine/bin/OpenRA.dll"
            dll.parent.mkdir(parents=True)
            dll.write_bytes(b"dll")

            command = launcher.game_command_for_runtime(root, ["Launch.Into=Menu"])

            self.assertEqual(str(host), command[0])
            self.assertEqual(str(hostfxr), command[1])
            self.assertEqual(str(dll), command[2])
            self.assertIn("Engine.ModSearchPaths=./mods," + str(root / "mods"), command)

    @mock.patch("launcher.messagebox.showwarning")
    def test_launch_routes_to_content_page_when_minimum_is_missing(self, showwarning):
        target = object.__new__(launcher.Launcher)
        target._set_launch_status = mock.Mock()
        target.show_page = mock.Mock()
        target._launch_impl = mock.Mock()

        with mock.patch("launcher.ra2_files.content_status", return_value={
            "healthy": False,
            "missing_core": ["language.mix"],
        }):
            target.launch("menu")

        target._launch_impl.assert_not_called()
        target.show_page.assert_called_once_with("content")
        target._set_launch_status.assert_called_once()
        showwarning.assert_called_once()

    @mock.patch("launcher.messagebox.showwarning")
    def test_launch_continues_when_minimum_content_is_ready(self, showwarning):
        target = object.__new__(launcher.Launcher)
        target._set_launch_status = mock.Mock()
        target.show_page = mock.Mock()
        target._launch_impl = mock.Mock()

        with mock.patch("launcher.ra2_files.content_status", return_value={
            "healthy": True,
            "missing_core": [],
        }):
            target.launch("menu")

        target._launch_impl.assert_called_once_with("menu")
        target.show_page.assert_not_called()
        showwarning.assert_not_called()


if __name__ == "__main__":
    unittest.main()
