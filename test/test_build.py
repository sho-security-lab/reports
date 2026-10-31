import json
import tempfile
import unittest
from pathlib import Path

from scripts.build import build, parse_post


def article(draft=False, extra=""):
    return (
        '---\ntitle: テスト\npublishedAt: "2026-10-31"\ntags: [日記]\n'
        f"draft: {str(draft).lower()}\n{extra}---\n\n## 本文\n\nこんにちは\n"
    )


class BuildTests(unittest.TestCase):
    def test_invalid_metadata_stops_build(self):
        cases = [
            (article().replace("draft: false", ""), "hello", "draft"),
            (article().replace("false", '"false"'), "hello", "draft"),
            (article().replace("false", "off"), "hello", "draft"),
            (article().replace("false", "0"), "hello", "draft"),
            (article().replace("2026-10-31", "2026-02-30"), "hello", "publishedAt"),
            (article(), "../hello", "ファイル名"),
            (article(extra="draft: true\n"), "hello", "重複"),
        ]
        for source, slug, message in cases:
            with self.subTest(source=source, slug=slug):
                with self.assertRaisesRegex(ValueError, message):
                    parse_post(source, slug)

    def test_yaml_dates_and_strings_keep_their_types(self):
        post = parse_post(article().replace('"2026-10-31"', "2026-10-31").replace("[日記]", "[on, off, yes, no]"), "hello")
        self.assertEqual(post["publishedAt"], "2026-10-31")
        self.assertEqual(post["tags"], ["on", "off", "yes", "no"])

    def test_only_public_files_are_generated_and_removed_when_unpublished(self):
        with tempfile.TemporaryDirectory(prefix="git-cms-") as directory:
            root = Path(directory)
            for name in ["posts", "assets/hello", "assets/private", "dist"]:
                (root / name).mkdir(parents=True)
            files = {
                "posts/hello.md": article(extra="secret: 非公開のメモ\n"),
                "posts/private.md": article(True),
                "assets/hello/cover.png": "public image",
                "assets/hello/notes.txt": "private notes",
                "assets/private/cover.png": "private image",
                "dist/obsolete.json": "old",
            }
            for name, content in files.items():
                (root / name).write_text(content, encoding="utf-8")
            build(root)
            output = root / "dist"
            listing = json.loads((output / "posts.json").read_text(encoding="utf-8"))
            self.assertEqual([post["slug"] for post in listing], ["hello"])
            self.assertNotIn("body", listing[0])
            self.assertNotIn("secret", listing[0])
            post = json.loads((output / "posts/hello.json").read_text(encoding="utf-8"))
            self.assertEqual(post["body"], "## 本文\n\nこんにちは")
            self.assertNotIn("secret", post)
            self.assertEqual(sorted(str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()), [
                ".nojekyll", "assets/hello/cover.png", "posts.json", "posts/hello.json",
            ])
            (root / "posts/hello.md").write_text(article(True), encoding="utf-8")
            build(root)
            self.assertEqual(json.loads((output / "posts.json").read_text(encoding="utf-8")), [])
            self.assertEqual(list((output / "posts").iterdir()), [])
            self.assertFalse((output / "assets").exists())

    def test_invalid_input_preserves_previous_output(self):
        with tempfile.TemporaryDirectory(prefix="git-cms-") as directory:
            root = Path(directory)
            (root / "posts").mkdir()
            (root / "posts/hello.md").write_text(article(), encoding="utf-8")
            build(root)
            previous = (root / "dist/posts.json").read_bytes()
            (root / "posts/hello.md").write_text(article().replace("draft: false", ""), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hello.md.*draft"):
                build(root)
            self.assertEqual((root / "dist/posts.json").read_bytes(), previous)

    def test_symbolic_links_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="git-cms-") as directory:
            root = Path(directory)
            (root / "posts").mkdir()
            (root / "posts/hello.md").write_text(article(), encoding="utf-8")
            (root / "assets/hello").mkdir(parents=True)
            (root / "assets/hello/cover.png").symlink_to(root / "posts/hello.md")
            with self.assertRaisesRegex(ValueError, "シンボリックリンク"):
                build(root)
            self.assertFalse((root / "dist").exists())

    def test_posts_are_sorted_by_date_then_slug(self):
        with tempfile.TemporaryDirectory(prefix="git-cms-") as directory:
            root = Path(directory)
            (root / "posts").mkdir()
            for slug, day in [("b", "2026-10-31"), ("a", "2026-10-31"), ("c", "2026-10-30")]:
                (root / "posts" / f"{slug}.md").write_text(article().replace("2026-10-31", day), encoding="utf-8")
            self.assertEqual([post["slug"] for post in build(root)], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
