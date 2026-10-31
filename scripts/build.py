"""MarkdownからブログのHTML・JSON・画像を生成する。"""

import json
import re
import shutil
import sys
from datetime import date
from html import escape
from pathlib import Path
from string import Template

import yaml
from markdown_it import MarkdownIt


class ArticleLoader(yaml.SafeLoader):
    """日付は文字列、真偽値はtrue/falseとして読み、キーの重複を拒否する。"""

    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError("メタデータのキーは文字列にしてください")
            if key in keys:
                raise ValueError(f"メタデータのキーが重複しています: {key}")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


# PyYAMLの既定のYAML 1.1解釈（on/off/yes/noや日付の自動変換）を避ける。
ArticleLoader.yaml_implicit_resolvers = {
    key: [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag not in {"tag:yaml.org,2002:bool", "tag:yaml.org,2002:timestamp"}
    ]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
ArticleLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false|True|False|TRUE|FALSE)$"), list("tTfF")
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif"}
THEME = Path(__file__).resolve().parent.parent / "theme"
DEFAULT_SITE = {
    "title": "My Journal",
    "description": "日々の記録と、考えたこと。",
    "author": "Your Name",
    "language": "ja",
}


def load_site(root):
    file = root / "config" / "site.yaml"
    if not file.exists():
        return DEFAULT_SITE.copy()
    site = yaml.load(file.read_text(encoding="utf-8"), Loader=ArticleLoader)
    if not isinstance(site, dict):
        raise ValueError("config/site.yaml は設定のマッピングにしてください")
    settings = {key: site.get(key, default) for key, default in DEFAULT_SITE.items()}
    for key, value in settings.items():
        if not isinstance(value, str):
            raise ValueError(f"config/site.yaml の {key} は文字列にしてください")
    if not settings["title"].strip():
        raise ValueError("config/site.yaml の title が必要です")
    if not re.fullmatch(r"[a-zA-Z]+(?:-[a-zA-Z0-9]+)*", settings["language"]):
        raise ValueError("config/site.yaml の language は ja、en などで指定してください")
    return settings


def render_blog(posts, site):
    template = Template((THEME / "page.html").read_text(encoding="utf-8"))
    # 生HTMLを無効にし、リンクの危険なスキームもMarkdownItの検証で除外する。
    markdown = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])

    def page(title, description, content, prefix=""):
        return template.substitute(
            language=escape(site["language"], quote=True),
            page_title=escape(title),
            description=escape(description, quote=True),
            site_title=escape(site["title"]),
            author=escape(site["author"]),
            prefix=prefix,
            content=content,
        )

    def tags(post):
        return "".join(f'<span class="tag">{escape(tag)}</span>' for tag in post["tags"])

    rows = []
    for number, post in enumerate(posts, start=1):
        rows.append(
            f'<li class="entry"><span class="entry-number">{number:02d}</span><article>'
            f'<div class="entry-meta"><time datetime="{post["publishedAt"]}">{post["publishedAt"]}</time>'
            f'{tags(post)}</div><h2><a href="posts/{post["slug"]}.html">{escape(post["title"])}</a></h2>'
            f'<p>{escape(post["description"])}</p></article>'
            f'<a class="entry-arrow" href="posts/{post["slug"]}.html" aria-label="{escape(post["title"], quote=True)}を読む">↗</a></li>'
        )
    listing = '<ol class="entries">' + "".join(rows) + "</ol>" if rows else '<p class="empty">まだ記事はありません。</p>'
    content = (
        '<section class="intro"><p class="eyebrow">THE JOURNAL</p>'
        f'<h1>{escape(site["title"])}</h1><p class="intro-description">{escape(site["description"])}</p></section>'
        f'<section aria-label="記事一覧"><div class="section-label"><h2>記事一覧</h2><span>{len(posts):02d} POSTS</span></div>{listing}</section>'
    )
    files = {"index.html": page(site["title"], site["description"], content)}
    for post in posts:
        content = (
            '<article class="post"><a class="back" href="../">← 記事一覧に戻る</a>'
            f'<header class="post-header"><div class="entry-meta"><time datetime="{post["publishedAt"]}">{post["publishedAt"]}</time>'
            f'{tags(post)}</div><h1>{escape(post["title"])}</h1>'
            f'<p class="post-description">{escape(post["description"])}</p></header>'
            f'<div class="prose">{markdown.render(post["body"])}</div></article>'
        )
        files[f'posts/{post["slug"]}.html'] = page(
            f'{post["title"]} | {site["title"]}', post["description"], content, "../"
        )
    files["theme.css"] = (THEME / "style.css").read_text(encoding="utf-8")
    return files


def parse_post(source, slug):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("ファイル名は半角英数字とハイフンで指定してください")
    source = source.removeprefix("\ufeff").replace("\r\n", "\n")
    match = re.fullmatch(r"---\n([\s\S]*?)\n---(?:\n|$)([\s\S]*)", source)
    if not match:
        raise ValueError("記事の先頭に --- で囲んだメタデータが必要です")
    meta = yaml.load(match[1], Loader=ArticleLoader)
    if not isinstance(meta, dict):
        raise ValueError("メタデータが不正です")
    if type(meta.get("draft")) is not bool:
        raise ValueError("draft: true または false が必要です")
    # 下書きは本文・メタデータ・画像のいずれも公開しない。
    if meta["draft"]:
        return None
    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title が必要です")
    published_at = meta.get("publishedAt")
    date_error = "publishedAt は実在する日付を YYYY-MM-DD 形式で指定してください"
    if not isinstance(published_at, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", published_at):
        raise ValueError(date_error)
    try:
        date.fromisoformat(published_at)
    except ValueError as error:
        raise ValueError(date_error) from error
    tags = meta.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise ValueError("tags は文字列の配列で指定してください")
    description = meta.get("description", "")
    if not isinstance(description, str):
        raise ValueError("description は文字列で指定してください")
    body = match[2].strip()
    if not body:
        raise ValueError("本文が必要です")
    return {
        "slug": slug,
        "title": title.strip(),
        "publishedAt": published_at,
        "description": description,
        "tags": tags,
        "body": body,
    }


def collect_images(directory, relative):
    if directory.is_symlink():
        raise ValueError(f"シンボリックリンクは公開できません: {directory}")
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ValueError(f"画像フォルダが不正です: {directory}")
    images = []
    for entry in sorted(directory.iterdir()):
        target = relative / entry.name
        if entry.is_symlink():
            raise ValueError(f"シンボリックリンクは公開できません: {entry}")
        if entry.is_dir():
            images.extend(collect_images(entry, target))
        elif entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS:
            images.append((entry, target))
    return images


def write_json(file, value):
    file.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build(root=None):
    root = Path.cwd() if root is None else Path(root)
    site = load_site(root)
    posts = []
    images = []
    for entry in sorted((root / "posts").iterdir()):
        if entry.suffix != ".md":
            continue
        if entry.is_symlink() or not entry.is_file():
            raise ValueError(f"通常の記事ファイルが必要です: {entry.name}")
        try:
            post = parse_post(entry.read_text(encoding="utf-8"), entry.stem)
        except (ValueError, yaml.YAMLError) as error:
            raise ValueError(f"{entry.name}: {error}") from error
        if post is None:
            continue
        posts.append(post)
        assets = root / "assets"
        if assets.is_symlink() or (assets.exists() and not assets.is_dir()):
            raise ValueError("assets は通常のフォルダにしてください")
        images.extend(collect_images(assets / post["slug"], Path("assets") / post["slug"]))
    posts.sort(key=lambda post: post["slug"])
    posts.sort(key=lambda post: post["publishedAt"], reverse=True)
    pages = render_blog(posts, site)
    # 入力検証が終わってから、以前の生成物を置き換える。
    output = root / "dist"
    if output.is_symlink():
        raise ValueError("dist は通常のフォルダにしてください")
    if output.exists():
        shutil.rmtree(output)
    (output / "posts").mkdir(parents=True)
    write_json(output / "posts.json", [{key: value for key, value in post.items() if key != "body"} for post in posts])
    for post in posts:
        write_json(output / "posts" / f"{post['slug']}.json", post)
    for name, content in pages.items():
        (output / name).write_text(content, encoding="utf-8")
    for source, target in images:
        destination = output / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    return posts


if __name__ == "__main__":
    try:
        print(f"{len(build())}件の記事を dist/ に生成しました")
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
