import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from scripts.build import build, parse_post, render_blog, DEFAULT_SITE


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in {"href", "src"}:
                self.urls.append(value)


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
                ".nojekyll", "assets/hello/cover.png", "index.html", "posts.json", "posts/hello.html", "posts/hello.json", "theme.css",
            ])
            self.assertNotIn("private", (output / "index.html").read_text(encoding="utf-8"))
            (root / "posts/hello.md").write_text(article(True), encoding="utf-8")
            build(root)
            self.assertEqual(json.loads((output / "posts.json").read_text(encoding="utf-8")), [])
            self.assertEqual(list((output / "posts").iterdir()), [])
            self.assertFalse((output / "assets").exists())
            self.assertIn("まだ記事はありません", (output / "index.html").read_text(encoding="utf-8"))

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

    def test_html_renders_markdown_and_escapes_metadata_and_raw_html(self):
        post = parse_post(article(), "hello")
        post["title"] = '<script>alert("title")</script>'
        post["description"] = '\" onmouseover=\"alert(1)'
        post["tags"] = ["<img src=x onerror=alert(1)>"]
        post["body"] += '\n\n<script>alert(1)</script>\n\n[link](javascript:alert(1))\n\n![bad](javascript:alert(1))'
        site = dict(DEFAULT_SITE, title="<script>site</script>", author="<script>author</script>")
        pages = render_blog([post], site)
        for name in ["index.html", "posts/hello.html"]:
            self.assertNotIn("<script>", pages[name])
            self.assertIn("&lt;script&gt;", pages[name])
            links = Links()
            links.feed(pages[name])
            self.assertFalse(any(url.startswith("javascript:") for url in links.urls))
        self.assertIn("<h2>本文</h2>", pages["posts/hello.html"])

    def test_page_links_work_at_domain_root_and_repository_subpath(self):
        with tempfile.TemporaryDirectory(prefix="git-cms-") as directory:
            root = Path(directory)
            (root / "posts").mkdir()
            (root / "assets/hello").mkdir(parents=True)
            (root / "assets/hello/cover.png").write_bytes(b"image")
            (root / "posts/hello.md").write_text(article() + '\n![画像](../assets/hello/cover.png)\n', encoding="utf-8")
            (root / "config").mkdir()
            (root / "config/site.yaml").write_text("title: 自分のブログ\nauthor: 著者\n", encoding="utf-8")
            build(root)
            self.assertIn("自分のブログ", (root / "dist/index.html").read_text(encoding="utf-8"))
            for base in ["https://example.com/", "https://example.com/my-fork/"]:
                for name in ["index.html", "posts/hello.html"]:
                    links = Links()
                    links.feed((root / "dist" / name).read_text(encoding="utf-8"))
                    for href in links.urls:
                        resolved = urlparse(urljoin(base + name, href)).path
                        self.assertTrue(resolved.startswith(urlparse(base).path))
                        target = root / "dist" / resolved.removeprefix(urlparse(base).path)
                        self.assertTrue(target.exists(), f"Missing link: {base}{name} -> {href}")

    def test_invalid_site_settings_preserve_output(self):
        with tempfile.TemporaryDirectory(prefix="git-cms-") as directory:
            root = Path(directory)
            (root / "posts").mkdir()
            build(root)
            previous = (root / "dist/index.html").read_bytes()
            (root / "config").mkdir()
            (root / "config/site.yaml").write_text("title: []\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "title"):
                build(root)
            self.assertEqual((root / "dist/index.html").read_bytes(), previous)

    def test_workflow_deploys_only_default_branch_without_external_secrets(self):
        import yaml

        file = Path(__file__).resolve().parent.parent / ".github/workflows/publish.yml"
        source = file.read_text(encoding="utf-8")
        workflow = yaml.safe_load(source)
        self.assertNotIn("secrets.", source)
        self.assertNotIn("external_repository", source)
        deploy = workflow["jobs"]["deploy"]
        self.assertEqual(deploy["needs"], "build")
        self.assertIn("github.event.repository.default_branch", deploy["if"])
        self.assertIn("github.event_name != 'pull_request'", deploy["if"])
        self.assertEqual(deploy["permissions"], {"pages": "write", "id-token": "write"})


if __name__ == "__main__":
    unittest.main()
