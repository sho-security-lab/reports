# Git CMS

非公開のGitHubリポジトリでMarkdown記事を管理し、公開対象のJSONと画像だけを別の公開リポジトリのGitHub Pagesへ配信します。専用の投稿画面やデータベースは不要です。

```text
非公開リポジトリで記事を保存
  → GitHub ActionsでJSONを生成
  → 公開専用リポジトリへ生成物を転送
  → GitHub Pagesで配信
```

## 初回設定

### 1. 記事用・公開用リポジトリを用意する

- このプロジェクトを記事用の **Private** リポジトリに配置します。既定ブランチは `main` にしてください。
- 生成物だけを置く **Public** リポジトリ（例: `blog-data`）を別途作成します。READMEを付けて初期化してください。
- 公開用リポジトリはこのCMS専用にしてください。配信時に `main` の内容を生成物で置き換えます。

GitHub Freeでも、この組み合わせで利用できます。非公開リポジトリのActionsにはプランごとの利用枠があります。

### 2. 公開用リポジトリへの鍵を設定する

手元で、この用途専用のSSH鍵を作成します（既存の鍵を上書きしないパスを指定）。

```sh
ssh-keygen -t ed25519 -C "git-cms-publish" -f ./git-cms-publish -N ""
```

1. 公開用リポジトリの **Settings → Deploy keys → Add deploy key** に `git-cms-publish.pub` の内容を登録し、**Allow write access** を有効にします。
2. 記事用リポジトリの **Settings → Secrets and variables → Actions → Secrets** に、`PUBLISH_DEPLOY_KEY` という名前で秘密鍵 `git-cms-publish` の内容を登録します。
3. 同じ画面の **Variables** に `PUBLISH_REPOSITORY` を追加し、`所有者/blog-data` のように公開用リポジトリを指定します（URLではありません）。

鍵はリポジトリ外で作成し、コミットしないでください。記事用リポジトリの `GITHUB_TOKEN` だけでは、別リポジトリへの書き込みはできないため専用鍵を使います。

### 3. GitHub Pagesを有効にする

1. 記事用リポジトリの **Actions → Build and publish blog JSON → Run workflow** を実行します。
2. 公開用リポジトリに生成物が届いたら、**Settings → Pages** を開きます。
3. **Source: Deploy from a branch**、**Branch: main**、**Folder: / (root)** を選択して保存します。
4. Pagesのデプロイが完了したら、同画面に表示されるURLにアクセスします。ルートページは作成しないため、末尾に `posts.json` を付けて確認してください。

例: `https://OWNER.github.io/blog-data/posts.json`

設定していない状態でもローカルビルドとPRの検証はできます。mainへの配信は設定不足をエラーとして通知します。サンプルの `hello-world.md` は公開対象なので、最初の配信前に編集するか `draft: true` にしてください。

## GitHubの画面から投稿する

1. **記事用の非公開リポジトリ**で `posts` フォルダを開きます。
2. **Add file → Create new file** で `my-first-post.md` のようなファイルを作成します。
3. 次の内容を入力します。

```markdown
---
title: はじめての記事
publishedAt: "2026-10-31"
description: 記事一覧に表示する説明です。
tags: [日記, お知らせ]
draft: false
---

ここから本文です。

## 見出し

Markdownで記事を書けます。
```

4. **Commit changes** から `main` に保存します。ブランチ保護がある場合はPRを作り、mainへマージします。
5. Actionsと公開用リポジトリのPagesデプロイが完了すると、公開JSONに反映されます。

- ファイル名がURL用の `slug` になります。半角小文字英数字とハイフンを使ってください。
- `title`、`publishedAt`、`draft`、本文は必須です。`description` と `tags` は省略できます。
- `draft: true` は非公開、`draft: false` は公開です。指定漏れ・文字列の `"false"` はエラーにし、誤公開を防ぎます。
- `publishedAt` は表示・並び順のための日付です。予約投稿の機能はありません。未来の日付でも `draft: false` なら公開されます。
- 記事の更新はファイルを編集して保存します。公開停止は `draft: true` に変更するか、記事ファイルを削除します。
- 公開停止後も、すでにダウンロードされたデータや配信キャッシュは回収できません。
- `posts` 直下の `.md` が対象です。下書きのサンプルは `posts/draft-example.md` にあります。

## 画像

記事ごとに `assets/<slug>/` フォルダへ画像をアップロードします。例えば `posts/my-first-post.md` の画像は `assets/my-first-post/cover.png` です。

GitHubの **Add file → Upload files** で追加できます。記事が公開されると、その記事の画像フォルダ内のPNG/JPEG/GIF/WebP/AVIFも公開されます。公開しない画像を公開記事のフォルダに置かないでください。下書き記事の画像は配信しません。記事を非公開化すると、次の配信で生成物から画像も削除します。

本文には配信先のURLを記載すると、ブログ側でそのまま扱えます。

```markdown
![説明](https://OWNER.github.io/blog-data/assets/my-first-post/cover.png)
```

## 公開JSON

| パス | 内容 |
| --- | --- |
| `posts.json` | 公開日の降順の記事一覧。本文は含みません |
| `posts/<slug>.json` | 記事のメタデータとMarkdown本文 |
| `assets/<slug>/...` | 公開記事の画像 |

記事JSONの例:

```json
{
  "slug": "hello-world",
  "title": "はじめての記事",
  "publishedAt": "2026-10-31",
  "description": "記事の説明",
  "tags": ["日記"],
  "body": "## 見出し\n\nMarkdownの本文です。"
}
```

ブログ側の取得例:

```js
const base = 'https://OWNER.github.io/blog-data/';
const response = await fetch(new URL('posts.json', base));
if (!response.ok) throw new Error('記事一覧を取得できませんでした');
const posts = await response.json();

if (posts.length > 0) {
  const detail = await fetch(new URL(`posts/${posts[0].slug}.json`, base));
  if (!detail.ok) throw new Error('記事を取得できませんでした');
  const post = await detail.json();
  console.log(post.title, post.body);
}
```

本文はMarkdownのまま返します。ブログ側でMarkdownをHTMLに変換し、表示時にはHTMLをサニタイズしてください。このプロジェクトにはブログの表示画面は含みません。

## ローカルで確認する

Python 3.12以上を使います。YAMLの読み取りにはPyYAMLを使用します。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s test -v
python scripts/build.py
```

`dist/` に公開対象だけを生成します。毎回作り直すため、記事を削除・非公開化した後の古いJSONは残りません。タイトルなどの公開用フィールドのみ出力し、追加のメタデータは出力しません。入力不備がある場合は配信を止め、既存の公開内容を維持します。

## 参考

- [GitHub Pagesの利用条件と公開設定](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [別リポジトリへの配信とDeploy keyの設定](https://github.com/peaceiris/actions-gh-pages#%EF%B8%8F-deploy-to-external-repository-external_repository)
- [PythonのGitHub Actions設定](https://github.com/actions/setup-python)
