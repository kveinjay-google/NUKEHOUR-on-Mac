import json
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import launcher


class MacosLauncherLayoutTest(unittest.TestCase):
    def test_right_content_panel_covers_the_complete_non_sidebar_area(self):
        layout = launcher.launcher_shell_layout()

        self.assertEqual(
            (launcher.SIDEBAR_W, 0, launcher.WIN_W - launcher.SIDEBAR_W, launcher.WIN_H),
            layout["content"],
        )

    def test_language_selector_has_an_explicit_unclipped_bottom_slot(self):
        layout = launcher.launcher_shell_layout()
        panel_x, panel_y, panel_width, panel_height = layout["language"]
        label_x, label_y, label_width, label_height = layout["language_label"]
        menu_x, menu_y, menu_width, menu_height = layout["language_menu"]
        _footer_x, footer_y, _footer_width, _footer_height = layout["footer"]

        self.assertGreaterEqual(menu_height, 28)
        self.assertGreaterEqual(label_height, 16)
        self.assertEqual((panel_width, panel_width), (label_width, menu_width))
        self.assertGreaterEqual(label_y, panel_y)
        self.assertGreaterEqual(menu_y, label_y + label_height)
        self.assertLessEqual(menu_y + menu_height, panel_y + panel_height)
        self.assertLessEqual(panel_y + panel_height, footer_y)
        self.assertGreaterEqual(panel_x, 0)
        self.assertLessEqual(panel_x + panel_width, launcher.SIDEBAR_W)

    def test_version_footer_is_inside_content_and_right_bottom_aligned(self):
        layout = launcher.launcher_shell_layout()
        x, y, width, height = layout["version_footer"]
        content_x, content_y, content_width, content_height = layout["content"]

        self.assertGreaterEqual(x, content_x)
        self.assertGreaterEqual(y, content_y)
        self.assertLessEqual(x + width, content_x + content_width)
        self.assertLessEqual(y + height, content_y + content_height)
        self.assertEqual(x + width, launcher.WIN_W - 16)
        self.assertEqual(y + height, launcher.WIN_H - 12)

    def test_version_text_uses_brand_and_product_version_without_ra2(self):
        text = launcher.launcher_version_text("1.0.3", 3)

        self.assertEqual("NUKE HOUR 1.0.3 (Build 3)", text)
        self.assertNotIn("RA2", text)

    def test_product_version_reads_source_manifest_and_frozen_bundle(self):
        with tempfile.TemporaryDirectory(prefix="nukehour-version-") as temporary:
            root = Path(temporary)
            (root / "packaging").mkdir()
            (root / "packaging/nukehour-version.json").write_text(
                json.dumps({"version": "1.2.3", "build": 7}), encoding="utf-8")
            self.assertEqual(("1.2.3", 7), launcher.launcher_product_version(root))

            frozen = root / "NUKE HOUR.app/Contents/Resources/runtime"
            frozen.mkdir(parents=True)
            with (root / "NUKE HOUR.app/Contents/Info.plist").open("wb") as stream:
                plistlib.dump({"CFBundleShortVersionString": "2.0.0", "CFBundleVersion": "9"}, stream)
            self.assertEqual(("2.0.0", 9), launcher.launcher_product_version(frozen))

    def test_startup_notice_uses_scrollable_copy_and_fixed_actions(self):
        root = Path(launcher.__file__).resolve().parent
        source = (root / "launcher.py").read_text(encoding="utf-8")
        translations = (root / "launcher_i18n.py").read_text(encoding="utf-8")

        self.assertIn("def _page_notice", source)
        self.assertIn("tk.Text(notice_body", source)
        self.assertIn('self._native_button(actions, "官方网站"', source)
        self.assertIn('self._native_button(actions, "继续"', source)
        self.assertIn("EA 未认可且不支持本产品", source)
        self.assertIn("完全免费开源", source)
        self.assertIn("合法购买并拥有的正版游戏副本", source)
        self.assertIn("官方授权版本", source)
        self.assertIn("恶意代码", source)
        self.assertIn("EA has not endorsed and does not support this product.", translations)
        actions_pack = source.index('actions.pack(side="bottom"')
        notice_pack = source.index('notice_body.pack(fill="both"')
        self.assertLess(actions_pack, notice_pack)

    def test_startup_notice_brand_names_are_linked_to_the_official_website(self):
        self.assertTrue(hasattr(launcher, "notice_brand_link_spans"))
        if not hasattr(launcher, "notice_brand_link_spans"):
            return

        spans = launcher.notice_brand_link_spans(launcher.STARTUP_NOTICE_COPY)

        self.assertEqual(2, len(spans))
        self.assertTrue(all(
            launcher.STARTUP_NOTICE_COPY[start:end] == launcher.BRAND_NAME
            for start, end in spans
        ))

        source = Path(launcher.__file__).read_text(encoding="utf-8")
        self.assertIn('copy.tag_add("brand_website_link"', source)
        self.assertIn('copy.tag_bind("brand_website_link", "<Button-1>"', source)
        self.assertIn("self._open_brand_website", source)

    def test_aqua_controls_use_branded_image_surfaces_with_readable_text(self):
        source = Path(launcher.__file__).read_text(encoding="utf-8")

        self.assertIn("def _control_surface", source)
        self.assertIn("image=base_image", source)
        self.assertIn('compound="center"', source)
        self.assertIn("tk.Menubutton(", source)
        self.assertIn("indicatoron=False", source)
        self.assertIn("font=FONT_LABEL", source)
        self.assertNotIn("language_menu = tk.OptionMenu(", source)

    @mock.patch("launcher.webbrowser.open_new_tab", return_value=True)
    def test_open_brand_website_uses_nuke_hour_url(self, open_new_tab):
        launcher.Launcher._open_brand_website(object())

        open_new_tab.assert_called_once_with("https://nukehour.com")


if __name__ == "__main__":
    unittest.main()
