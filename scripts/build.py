"""公開記事のMarkdownをJSONへ変換する。"""

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml


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
