# GitHub Blog Starter

[English](README.md) | [日本語](README.ja.md)

**フォークして、GitHubで記事を書くだけ。** PythonがMarkdownからHTMLとJSONを生成し、同じリポジトリのGitHub Pagesへブログを公開します。

データベース、別の公開用リポジトリ、個人用アクセストークン、専用の管理画面は不要です。

```text
GitHubでMarkdownの記事を保存
  → GitHub ActionsがPythonを実行
  → dist/ にHTML・JSON・画像を生成
  → GitHub Pagesでブログを公開
```

## はじめに

1. このリポジトリを **Fork** します。GitHub FreeでGitHub Pagesを使う場合は、フォーク先を **Public** にしてください。
2. フォーク先の **Actions** タブを開き、ワークフローの有効化を求められた場合は有効にします。
3. **Settings → Pages → Build and deployment → Source** で **GitHub Actions** を選択します。この初回設定を行わないと、`actions/configure-pages` が `Get Pages site failed / Not Found` というエラーになります。
4. `config/site.yaml` を編集し、デフォルトブランチ（通常は `main`）へコミットします。
5. **Actions → Build and publish blog** の成功を確認し、**Settings → Pages** に表示されるURLを開きます。

デフォルトブランチで **Actions → Build and publish blog → Run workflow** を実行することもできます。フォークしただけでは公開処理は始まりません。GitHubが提案するワークフローのテンプレートを追加する必要はありません。

通常の公開URLは `https://<ユーザー名>.github.io/<リポジトリ名>/` です。`<ユーザー名>.github.io` という名前のリポジトリや独自ドメインでも利用できます。画面内のリンクは相対パスなので、ユーザー名やリポジトリ名をコードに埋め込む必要はありません。

公開するのはデフォルトブランチだけです。PRや他のブランチでは、公開せずにテストとビルドを実行します。デフォルトブランチ名を変更した場合は、**Settings → Environments → github-pages** の公開を許可するブランチも確認してください。

組織のポリシーによってActionsやPagesが制限される場合があります。非公開リポジトリでのPages利用には、GitHub Proなどの対応プランが必要です。

## ブログの設定

`config/site.yaml` を編集します。

```yaml
title: My Journal
description: Notes on everyday life and things along the way.
author: Your Name
theme: literary
headline: |-
  A life,
  written down.
```

画面の案内文・日付の表記・サンプル・ビルド時のメッセージは英語です。言語設定や翻訳機能はありません。この日本語版READMEは、利用手順を説明するためのものです。

### テーマの選択

| 設定値 | デザイン |
| --- | --- |
| `literary`（初期設定） | 生成りの背景とセリフ体。大きな見出しと最新記事、その下に2列の記事一覧 |
| `notebook` | 淡い緑のサイドバー。月別の記事一覧と日付の列 |
| `newspaper` | 中央の大きな誌名、発行日、トップ記事の大見出し、罫線と段組み、セリフ体の本文 |

例えばノート風のテーマに変更する場合は、次のように設定します。

```yaml
theme: notebook
```

変更をコミットすると、記事一覧と記事詳細の両方に反映されます。テーマを変更しても、記事URLとJSONの形式は変わりません。`theme` を省略すると `literary` になります。未対応の値を指定した場合は、既存の生成物を置き換える前にビルドを止めます。

`headline` は `literary` のトップに表示する大きな見出しです。上の例のように `|-` を使うと改行できます。`notebook` と `newspaper` では、この設定は表示しません。ブログ名は常に `title` で設定します。

3テーマとも、スマートフォンなどの狭い画面と、端末のダークモード設定に対応しています。システムフォントを使い、外部フォント・JavaScript・アイコンライブラリは読み込みません。

デザインを直接編集する場合は、`theme/literary/`、`theme/notebook/`、`theme/newspaper/` 内の `page.html` と `style.css` を変更してください。本文などの共通スタイルは `theme/shared.css` にあります。

### 新聞風のテーマ

`theme: newspaper` にすると、コンパクトな誌名と細い罫線を使った新聞風のトップページになります。最新の記事をトップ記事として、斜体の紹介文と本文の自動抜粋を添えて表示します。次の2件を脇の列、それ以降の記事を3列の一覧として表示します。記事が1件の場合は、脇の列に設定済みの説明と著者名を使ったブログ紹介を表示します。記事がない場合は、記事がないことを示す案内を表示します。

抜粋には本文の最初の2段落を使い、長い場合は640文字までに収めます。見出し・リスト・引用・コードブロック・画像・マークアップは含めません。メタデータの追加は不要です。JSONには引き続きMarkdown本文全体が含まれます。

誌名の下の日付には、一覧ページでは最新記事の公開日、記事詳細ではその記事の公開日を使います。ビルド日ではないため、記事を追加せずに再ビルドしても発行日が変わることはありません。記事詳細は読みやすい1列の本文と斜体の紹介文で構成します。狭い画面では、トップページも1列に並びます。

## GitHubの画面から記事を書く

1. フォーク先の `posts` フォルダを開きます。
2. **Add file → Create new file** を選び、`my-first-post.md` のような名前を付けます。
3. 次の形式で記事を書きます。

```markdown
---
title: My first post
publishedAt: "2026-10-31"
description: A short introduction for the article list.
tags: [Journal, News]
draft: false
---

Your article starts here.

## A heading

Write your content in Markdown.
```

4. **Commit changes** でデフォルトブランチへ保存します。ブランチ保護がある場合は、PRを作ってマージします。
5. ワークフローが成功すると、ブログとJSONが更新されます。

- ファイル名が記事の `slug` になります。半角の小文字英数字とハイフンを使ってください。
- `title`、`publishedAt`、`draft`、空でない本文は必須です。`description` と `tags` は省略できます。
- 対象は `posts/` 直下の `.md` ファイルです。
- `draft: true` にすると、記事とその画像をブログ・JSONの生成対象から除外します。公開するときは `draft: false` に変更します。
- `draft` の指定漏れや、文字列の `"false"` はエラーになります。
- `publishedAt` は日付の表示と並び順のための設定です。予約投稿ではありません。未来の日付でも `draft: false` なら即座に公開対象になります。
- 更新はファイルの編集で行います。公開停止は `draft: true` への変更、または記事ファイルの削除で行い、次回の公開時に反映されます。
- 見出し・リスト・引用・リンク・画像・コードブロック・表・取り消し線に対応しています。生のHTMLは実行せず、文字として表示します。

**公開リポジトリでは、下書きのファイル・画像・コミット履歴もGitHub上から閲覧できます。** `draft` はブログへの掲載を制御する設定で、リポジトリ内の情報を非公開にする機能ではありません。公開済みの記事を削除しても、取得済みのコピーやキャッシュは回収できません。

`posts/hello-world.md` は公開対象のサンプルです。利用前に編集するか削除してください。`posts/draft-example.md` は下書きのサンプルです。

## 画像を追加する

記事の画像は `assets/<slug>/` にアップロードします。例えば `posts/my-first-post.md` の画像なら、`assets/my-first-post/cover.png` のように配置します。

GitHubの **Add file → Upload files** から追加できます。記事本文には、記事からの相対パスで記載してください。

```markdown
![A description](../assets/my-first-post/cover.png)
```

このパスは、GitHubのMarkdown表示と公開した記事の両方で利用できます。

公開記事のフォルダにあるPNG・JPEG・GIF・WebP・AVIFを生成物へコピーします。下書きの画像や、その他の形式のファイルは含めません。記事を削除・非公開化すると、次に公開処理が成功した時点で、その記事のHTML・JSON・画像も除去します。

記事同士をリンクする場合は、`[Another post](other-post.html)` のように、生成後のファイル名を指定してください。

## 生成ファイルとJSON

```text
dist/
├── index.html                 # 記事一覧
├── theme.css                  # 選択したテーマと共通スタイル
├── .nojekyll
├── posts.json                 # 記事の概要一覧（本文なし）
├── posts/
│   ├── hello-world.html        # 記事ページ
│   └── hello-world.json        # 記事のメタデータとMarkdown本文
└── assets/
    └── hello-world/            # 画像（存在する場合）
```

`dist/` は自動生成し、Gitの管理対象から除外しています。GitHub Actionsも同じビルドコマンドを使い、このフォルダの中身だけを公開します。

JSONは他のWebサイトやアプリからも利用できます。

| パス | 内容 |
| --- | --- |
| `posts.json` | 公開日の新しい順の記事概要。同じ日付の場合はslug順 |
| `posts/<slug>.json` | 記事のメタデータとMarkdown本文 |

```json
{
  "slug": "hello-world",
  "title": "My first post",
  "publishedAt": "2026-10-31",
  "description": "A short introduction.",
  "tags": ["Journal"],
  "body": "## A heading\n\nYour content goes here."
}
```

Markdown内の相対URLは、記事の `posts/<slug>.html` または `posts/<slug>.json` のURLを基準に解決してください。他の場所でMarkdownを表示する場合は、生のHTMLを無効にするか、生成したHTMLを適切にサニタイズしてください。

## ローカルで動かす

Python 3.12以上を使います。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s test -v
python scripts/build.py
python -m http.server 8000 --directory dist
```

Windowsでは、仮想環境の有効化に `.venv\Scripts\activate` を使います。

`http://localhost:8000/` を開いて確認してください。記事・設定・テーマのファイルを編集した後は、`python scripts/build.py` を再実行し、ブラウザを更新します。

入力やテンプレートに不備がある場合は、既存の生成物を置き換える前にビルドを止めます。テストやビルドが失敗した場合は公開しません。

## ライセンス

MIT License。[LICENSE](LICENSE) を参照してください。

## 参考

- [GitHub Pagesの公開設定と対応プラン](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub ActionsからPagesへの公開](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [MarkdownのHTML処理](https://markdown-it-py.readthedocs.io/en/latest/security.html)
