"""Build a static blog, JSON feeds, and images from Markdown posts."""

import json
import re
import shutil
import sys
from datetime import date
from html import escape
from html.parser import HTMLParser
from itertools import groupby
from pathlib import Path
from string import Template

import yaml
from markdown_it import MarkdownIt


class ArticleLoader(yaml.SafeLoader):
    """Keep dates as strings, recognize true/false, and reject duplicate keys."""

    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ValueError("Metadata keys must be strings")
            if key in keys:
                raise ValueError(f"Duplicate metadata key: {key}")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


# Avoid YAML 1.1 coercion of on/off/yes/no and automatic date conversion.
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
THEMES = {"literary", "notebook", "newspaper"}
DEFAULT_SITE = {
    "title": "My Journal",
    "description": "Notes on everyday life and things along the way.",
    "author": "Your Name",
    "theme": "literary",
    "headline": "A life,\nwritten down.",
}
UI_TEXT = {
    "posts": "All posts", "read": "Read", "read_title": "Read {title}",
    "back": "Back to all posts", "empty": "No posts yet.",
    "skip": "Skip to content", "navigation": "Main navigation",
}
MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)


class ParagraphPreview(HTMLParser):
    """Collect introductory prose without markup, lists, quotes, or code blocks."""

    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current = None
        self.blocked = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"pre", "blockquote", "ul", "ol", "table"}:
            self.blocked += 1
        if tag == "p" and not self.blocked and len(self.paragraphs) < 2:
            self.current = []
        elif tag == "br" and self.current is not None:
            self.current.append(" ")

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "p" and self.current is not None:
            text = " ".join("".join(self.current).split())
            if text:
                self.paragraphs.append(text)
            self.current = None
        if tag in {"pre", "blockquote", "ul", "ol", "table"}:
            self.blocked = max(0, self.blocked - 1)


def render_preview(html):
    parser = ParagraphPreview()
    parser.feed(html)
    paragraphs = []
    remaining = 640
    for text in parser.paragraphs:
        truncated = len(text) > remaining
        if truncated:
            text = text[:remaining].rsplit(" ", 1)[0] or text[:remaining]
            text += "…"
        paragraphs.append(f"<p>{escape(text)}</p>")
        remaining -= len(text)
        if truncated or remaining <= 0:
            break
    return '<div class="entry-excerpt">' + "".join(paragraphs) + '</div>' if paragraphs else ""


def load_site(root):
    file = root / "config" / "site.yaml"
    if not file.exists():
        return DEFAULT_SITE.copy()
    site = yaml.load(file.read_text(encoding="utf-8"), Loader=ArticleLoader)
    if not isinstance(site, dict):
        raise ValueError("config/site.yaml must contain a mapping of settings")
    settings = {key: site.get(key, default) for key, default in DEFAULT_SITE.items()}
    for key, value in settings.items():
        if not isinstance(value, str):
            raise ValueError(f"config/site.yaml: {key} must be a string")
    if not settings["title"].strip():
        raise ValueError("config/site.yaml: title is required")
    if settings["theme"] not in THEMES:
        raise ValueError("config/site.yaml: theme must be literary, notebook, or newspaper")
    return settings


def render_blog(posts, site):
    theme = site.get("theme", "literary")
    if theme not in THEMES:
        raise ValueError("theme must be literary, notebook, or newspaper")
    template = Template((THEME / theme / "page.html").read_text(encoding="utf-8"))
    labels = UI_TEXT
    # Disable raw HTML; MarkdownIt also validates link schemes.
    markdown = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])

    def page(title, description, content, prefix="", kind="index", edition=None):
        if edition is None and posts:
            edition = posts[0]["publishedAt"]
        edition_date = ""
        if edition:
            published = date.fromisoformat(edition)
            weekday = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[published.weekday()]
            edition_date = f'<time datetime="{edition}">{weekday}, {MONTH_NAMES[published.month - 1]} {published.day}, {published.year}</time>'
        return template.substitute(
            page_title=escape(title),
            description=escape(description, quote=True),
            site_title=escape(site["title"]),
            site_description=escape(site["description"]),
            author=escape(site["author"]),
            prefix=prefix,
            content=content,
            page_kind=kind,
            initials=escape(" / ".join(word[0] for word in site["title"].split()[:2])),
            current=' aria-current="page"' if kind == "index" else "",
            posts_label=labels["posts"],
            skip_label=labels["skip"],
            navigation_label=labels["navigation"],
            edition_date=edition_date,
        )

    def tags(post):
        return "".join(f'<span class="tag">{escape(tag)}</span>' for tag in post["tags"])

    def entry(post, heading, featured=False):
        published = date.fromisoformat(post["publishedAt"])
        if theme == "notebook":
            weekday = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")[published.weekday()]
            stamp = (
                f'<time class="date-stamp" datetime="{post["publishedAt"]}">'
                f'<span>{published.year}</span><strong>{published:%m.%d}</strong><span>{weekday}</span></time>'
            )
            meta = f'<div class="entry-tags">{tags(post)}</div>'
        else:
            stamp = ""
            meta = (
                f'<div class="entry-meta"><time datetime="{post["publishedAt"]}">{post["publishedAt"]}</time>'
                f'<div class="entry-tags">{tags(post)}</div></div>'
            )
        preview = render_preview(markdown.render(post["body"])) if theme == "newspaper" and featured else ""
        read_label = "Read more" if theme == "newspaper" else labels["read"]
        return (
            f'<li class="entry">{stamp}{meta if theme != "notebook" else ""}'
            f'<div class="entry-copy"><{heading}><a href="posts/{post["slug"]}.html">{escape(post["title"])}</a></{heading}>'
            f'<p class="entry-deck">{escape(post["description"])}</p>{preview}{meta if theme == "notebook" else ""}</div>'
            f'<a class="entry-link" href="posts/{post["slug"]}.html" aria-label="{escape(labels["read_title"].format(title=post["title"]), quote=True)}">{read_label}</a></li>'
        )

    empty = f'<p class="empty">{labels["empty"]}</p>'
    if theme == "literary":
        listing = '<ol class="entries">' + "".join(entry(post, "h2") for post in posts) + '</ol>' if posts else empty
        content = (
            f'<section class="intro"><h1>{escape(site.get("headline", DEFAULT_SITE["headline"]))}</h1>'
            f'<div class="intro-aside"><p class="eyebrow">{escape(site["title"])}</p>'
            f'<p class="intro-description">{escape(site["description"])}</p></div></section>'
            f'<section aria-label="{labels["posts"]}">{listing}</section>'
        )
    elif theme == "notebook":
        months = []
        for month, month_posts in groupby(posts, key=lambda post: post["publishedAt"][:7]):
            year, number = map(int, month.split("-"))
            month_label = f"{MONTH_NAMES[number - 1]} {year}"
            months.append(
                f'<section class="month"><h2>{month_label}</h2><ol class="entries">'
                + "".join(entry(post, "h3") for post in month_posts) + '</ol></section>'
            )
        content = f'<header class="index-header"><h1>{labels["posts"]}</h1></header>' + ("".join(months) if posts else empty)
    else:
        if posts:
            lead = '<ol class="lead-stories">' + entry(posts[0], "h2", featured=True) + '</ol>'
            if len(posts) > 1:
                sidebar = '<aside class="edition-sidebar"><h2 class="section-title">In this edition</h2><ol class="secondary-stories">'
                sidebar += "".join(entry(post, "h3") for post in posts[1:3]) + '</ol></aside>'
            else:
                sidebar = (
                    '<aside class="edition-sidebar journal-note"><h2 class="section-title">About this journal</h2>'
                    f'<p>{escape(site["description"])}</p><p class="note-author">Written by {escape(site["author"])}</p></aside>'
                )
            listing = f'<div class="front-page">{lead}{sidebar}</div>'
            if len(posts) > 3:
                listing += '<section class="more-stories"><h2 class="section-title">More stories</h2><ol class="entries">'
                listing += "".join(entry(post, "h3") for post in posts[3:]) + '</ol></section>'
        else:
            listing = empty
        content = '<h1 class="front-label">Front page</h1>' + listing
    files = {"index.html": page(site["title"], site["description"], content)}
    for post in posts:
        content = (
            f'<article class="post"><a class="back" href="../">{labels["back"]}</a>'
            f'<header class="post-header"><div class="entry-meta"><time datetime="{post["publishedAt"]}">{post["publishedAt"]}</time>'
            f'{tags(post)}</div><h1>{escape(post["title"])}</h1>'
            f'<p class="post-description">{escape(post["description"])}</p></header>'
            f'<div class="prose">{markdown.render(post["body"])}</div></article>'
        )
        files[f'posts/{post["slug"]}.html'] = page(
            f'{post["title"]} | {site["title"]}', post["description"], content, "../", "article", post["publishedAt"]
        )
    files["theme.css"] = (
        (THEME / "shared.css").read_text(encoding="utf-8") + "\n" + (THEME / theme / "style.css").read_text(encoding="utf-8")
    )
    return files


def parse_post(source, slug):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("The filename must use lowercase letters, numbers, and hyphens")
    source = source.removeprefix("\ufeff").replace("\r\n", "\n")
    match = re.fullmatch(r"---\n([\s\S]*?)\n---(?:\n|$)([\s\S]*)", source)
    if not match:
        raise ValueError("Posts must start with metadata enclosed in ---")
    meta = yaml.load(match[1], Loader=ArticleLoader)
    if not isinstance(meta, dict):
        raise ValueError("Metadata must be a mapping")
    if type(meta.get("draft")) is not bool:
        raise ValueError("draft must be true or false")
    # Exclude drafts, including their metadata and images.
    if meta["draft"]:
        return None
    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required")
    published_at = meta.get("publishedAt")
    date_error = "publishedAt must be a valid date in YYYY-MM-DD format"
    if not isinstance(published_at, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", published_at):
        raise ValueError(date_error)
    try:
        date.fromisoformat(published_at)
    except ValueError as error:
        raise ValueError(date_error) from error
    tags = meta.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise ValueError("tags must be a list of strings")
    description = meta.get("description", "")
    if not isinstance(description, str):
        raise ValueError("description must be a string")
    body = match[2].strip()
    if not body:
        raise ValueError("Post body is required")
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
        raise ValueError(f"Symbolic links cannot be published: {directory}")
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise ValueError(f"Invalid image directory: {directory}")
    images = []
    for entry in sorted(directory.iterdir()):
        target = relative / entry.name
        if entry.is_symlink():
            raise ValueError(f"Symbolic links cannot be published: {entry}")
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
            raise ValueError(f"Posts must be regular files: {entry.name}")
        try:
            post = parse_post(entry.read_text(encoding="utf-8"), entry.stem)
        except (ValueError, yaml.YAMLError) as error:
            raise ValueError(f"{entry.name}: {error}") from error
        if post is None:
            continue
        posts.append(post)
        assets = root / "assets"
        if assets.is_symlink() or (assets.exists() and not assets.is_dir()):
            raise ValueError("assets must be a regular directory")
        images.extend(collect_images(assets / post["slug"], Path("assets") / post["slug"]))
    posts.sort(key=lambda post: post["slug"])
    posts.sort(key=lambda post: post["publishedAt"], reverse=True)
    pages = render_blog(posts, site)
    # Validate all inputs and templates before replacing previous output.
    output = root / "dist"
    if output.is_symlink():
        raise ValueError("dist must be a regular directory")
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
        print(f"Built {len(build())} post(s) in dist/")
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
