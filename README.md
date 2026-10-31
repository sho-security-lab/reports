# Git CMS

**フォークして、GitHubで記事を書くだけ。** PythonがMarkdownからブログとJSONを生成し、同じリポジトリのGitHub Pagesへ公開します。

投稿・ブログ表示・JSON配信を1つのリポジトリで管理できます。データベース、専用の管理画面、別の配信用リポジトリ、個人用トークンの設定は不要です。

```text
GitHubで記事を保存
  → GitHub ActionsでPythonを実行
  → dist/ にHTML・JSON・画像を生成
  → このリポジトリのGitHub Pagesへ公開
```

## フォークして始める

1. このリポジトリを自分のアカウントへ **Fork** します。GitHub Freeで公開する場合は **Public** にしてください。
2. フォーク先の **Actions** タブで、ワークフローが無効になっている場合は有効にします。
3. **Settings → Pages → Build and deployment → Source** を **GitHub Actions** に設定します。
4. `config/site.yaml` のブログ名・説明・著者名を編集し、デフォルトブランチ（通常は `main`）へ保存します。
5. **Actions → Build and publish blog** が成功したら、**Settings → Pages** に表示されるURLを開きます。

手動で公開する場合は **Actions → Build and publish blog → Run workflow** から、デフォルトブランチを選んで実行します。フォークしただけでは公開処理は始まりません。

通常の公開URLは `https://<ユーザー名>.github.io/<リポジトリ名>/` です。`<ユーザー名>.github.io` という名前のリポジトリや独自ドメインでも利用できます。画面内のリンクは相対パスなので、ユーザー名・リポジトリ名をコードへ埋め込む必要はありません。

公開処理はリポジトリのデフォルトブランチだけで行います。PRや他のブランチではテストとビルドのみ実行します。デフォルトブランチを変更した場合は、**Settings → Environments → github-pages** の配信許可ブランチも確認してください。

組織のポリシーなどでActionsやPagesが制限されている場合は、管理者による設定が必要です。非公開リポジトリからのPages公開にはGitHub Proなどの対象プランが必要です。

## ブログの設定

`config/site.yaml` を編集します。

```yaml
title: My Journal
description: 日々の記録と、考えたこと。
author: Your Name
language: ja
```

`language` はHTMLの言語属性です。画面の案内文は日本語です。デザインを変更する場合は `theme/page.html` と `theme/style.css` を編集してください。スマートフォンとダークモードに対応しています。外部のフォントやJavaScriptの読み込みはありません。

## GitHubの画面から投稿する

1. フォークしたリポジトリの `posts` フォルダを開きます。
2. **Add file → Create new file** で `my-first-post.md` のようなファイルを作成します。
3. 次の形式で記事を書きます。

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

4. **Commit changes** でデフォルトブランチへ保存します。ブランチ保護がある場合はPRを作り、マージしてください。
5. Actionsが成功すると、ブログとJSONが更新されます。

- ファイル名が記事の `slug` になります。半角小文字英数字とハイフンを使ってください。
- `title`、`publishedAt`、`draft`、本文は必須です。`description` と `tags` は省略できます。
- `posts` 直下の `.md` ファイルが対象です。
- `draft: true` の記事はブログ・JSON・配信画像から除外します。公開する場合は `draft: false` にします。
- `draft` の指定漏れや文字列の `"false"` はエラーにします。
- `publishedAt` は表示と並び順のための日付です。予約投稿ではなく、未来の日付でも `draft: false` なら公開されます。
- 更新は記事ファイルの編集、公開停止は `draft: true` への変更またはファイルの削除で行います。
- 見出し・リスト・引用・リンク・画像・コードブロック・表・取り消し線に対応します。本文に書いた生HTMLは実行せず、文字として表示します。

**公開リポジトリでは、下書きの本文や画像もGitHub上のファイル・編集履歴から閲覧できます。** `draft` はブログへの掲載を制御する設定で、秘密の情報を保存するための機能ではありません。公開停止後も、すでに取得されたデータや配信キャッシュは回収できません。

サンプルの `posts/hello-world.md` は公開対象です。自分の記事に編集するか削除してください。`posts/draft-example.md` は下書きの見本です。

## 画像を追加する

記事ごとに `assets/<slug>/` フォルダへ画像をアップロードします。

例: `posts/my-first-post.md` の画像は `assets/my-first-post/cover.png` に配置します。GitHubの **Add file → Upload files** から追加できます。

記事本文には次のように相対パスで記載してください。GitHubのMarkdown表示と公開ブログの両方で同じ画像を参照できます。

```markdown
![説明](../assets/my-first-post/cover.png)
```

公開記事の画像フォルダにあるPNG/JPEG/GIF/WebP/AVIFを配信します。下書き記事の画像や、その他の拡張子のファイルは生成物に含めません。記事を非公開化・削除すると、次回の配信でその記事のHTML・JSON・画像も除去します。

記事同士をリンクする場合は `[別の記事](other-post.html)` のように、公開後のHTMLファイル名を指定してください。

## 公開ファイルとJSON

```text
dist/
├── index.html                 # 記事一覧
├── theme.css                  # ブログのスタイル
├── .nojekyll
├── posts.json                 # 記事一覧JSON（本文なし）
├── posts/
│   ├── hello-world.html        # 記事ページ
│   └── hello-world.json        # 記事JSON（Markdown本文あり）
└── assets/
    └── hello-world/            # 公開記事の画像（存在する場合）
```

`dist/` は自動生成するため、Gitにはコミットしません。GitHub Actionsも同じコマンドで生成し、このフォルダの中身だけをPagesへ配信します。

JSONは他のWebサイトやアプリからも利用できます。

| パス | 内容 |
| --- | --- |
| `posts.json` | 公開日の降順の記事一覧。同日の場合はslug順。本文なし |
| `posts/<slug>.json` | 記事のメタデータとMarkdown本文 |

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

記事本文内の相対URLは、`posts/<slug>.html` または `posts/<slug>.json` のURLを基準に解決してください。別のアプリでMarkdownを表示するときも、生HTMLを無効にするなど適切に処理してください。

## ローカルで確認する

Python 3.12以上を使います。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s test -v
python scripts/build.py
python -m http.server 8000 --directory dist
```

Windowsでは仮想環境の有効化に `.venv\Scripts\activate` を使います。

`http://localhost:8000/` を開くとブログを確認できます。記事や設定を編集した後は `python scripts/build.py` を再実行し、ブラウザを更新してください。

入力やテンプレートに不備がある場合は、既存の `dist/` を置き換える前にビルドを止めます。テストやビルドが失敗した場合は配信しません。

## ライセンス

MIT License。フォークして利用・改変できます。[LICENSE](LICENSE) を参照してください。

## 参考

- [GitHub Pagesの公開設定と対応プラン](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub ActionsからPagesへの配信](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [MarkdownのHTML処理](https://markdown-it-py.readthedocs.io/en/latest/security.html)
