# Git CMS

[English](README.md) | [日本語](README.ja.md)

**Fork it. Write on GitHub. Publish your blog.** A Python-powered blog that turns Markdown posts into HTML and JSON, then deploys to GitHub Pages from the same repository.

No database, separate publishing repository, personal access token, or custom admin interface is needed.

```text
Save a Markdown post on GitHub
  → GitHub Actions runs Python
  → HTML, JSON, and images are generated in dist/
  → GitHub Pages publishes the blog
```

## Quick start

1. **Fork** this repository. Keep your fork **public** to use GitHub Pages on GitHub Free.
2. Open the **Actions** tab in your fork and enable workflows if prompted.
3. Go to **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**. This initial setup is required; otherwise `actions/configure-pages` fails with `Get Pages site failed / Not Found`.
4. Edit `config/site.yaml` and commit to the default branch, usually `main`.
5. Wait for **Actions → Build and publish blog** to succeed, then visit the URL shown in **Settings → Pages**.

You can also run **Actions → Build and publish blog → Run workflow** on the default branch. Forking alone does not start a deployment. You do not need to add one of GitHub's suggested workflow templates.

The usual URL is `https://<username>.github.io/<repository>/`. User sites named `<username>.github.io` and custom domains also work. All internal links are relative; no username or repository name is hardcoded.

Only the default branch deploys. Pull requests and other branches run tests and builds without publishing. If you rename the default branch, also check the allowed deployment branches under **Settings → Environments → github-pages**.

Organization policies may restrict Actions or Pages. Private repositories require a Pages-compatible plan such as GitHub Pro.

## Configure your blog

Edit `config/site.yaml`:

```yaml
title: My Journal
description: Notes on everyday life and things along the way.
author: Your Name
theme: literary
headline: |-
  A life,
  written down.
```

The interface, date labels, examples, and build messages are in English. No language setting or translation system is required.

### Choose a theme

| Value | Design |
| --- | --- |
| `literary` (default) | Warm paper, serif typography, a large headline, a featured latest post, and a two-column list |
| `notebook` | A sage sidebar, monthly post groups, and a date column |
| `newspaper` | A centered masthead, edition date, bold lead story, ruled columns, and serif article text |

To select the notebook theme:

```yaml
theme: notebook
```

Commit the change to apply it to both the index and article pages. Article URLs and JSON stay the same across themes. Omitting `theme` selects `literary`; an unsupported value stops the build before replacing existing output.

`headline` sets the large heading in `literary`. Use `|-` as shown above for line breaks. The notebook and newspaper themes do not display this setting. The blog name is always controlled by `title`.

All three themes adapt to narrow screens and the system's dark-mode preference. They use system fonts and do not load external fonts, JavaScript, or icon libraries.

To customize the design, edit `page.html` and `style.css` in `theme/literary/`, `theme/notebook/`, or `theme/newspaper/`. Shared article styles live in `theme/shared.css`.

### Newspaper edition

Set `theme: newspaper` for a newspaper-style front page. The latest post becomes the lead story, the next two appear in the side column, and additional posts form a three-column list. With one post, the side column introduces your journal using the configured description and author. With no posts, the page shows an empty state.

The masthead's date comes from the latest published post on the index and from the current article on detail pages. It is not the build date, so rebuilding without new posts does not create a fictional new edition. Article pages use a single readable text column with a drop cap. The front page stacks into one column on narrow screens.

## Write a post on GitHub

1. Open the `posts` directory in your fork.
2. Choose **Add file → Create new file** and name it something like `my-first-post.md`.
3. Write your post in this format:

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

4. **Commit changes** to the default branch, or merge a pull request if branch protection requires it.
5. The blog and JSON update after the workflow succeeds.

- The filename becomes the article's `slug`. Use lowercase letters, numbers, and hyphens.
- `title`, `publishedAt`, `draft`, and a nonempty body are required. `description` and `tags` are optional.
- Only `.md` files directly inside `posts/` are included.
- Use `draft: true` to exclude an article and its images from the generated blog and JSON. Change it to `draft: false` to publish.
- Missing `draft` values and strings such as `"false"` cause an error.
- `publishedAt` controls display and sorting, not scheduling. A future-dated article with `draft: false` is published immediately.
- Edit a file to update it. Set `draft: true` or delete the file to remove it from the next deployment.
- Headings, lists, quotes, links, images, fenced code, tables, and strikethrough are supported. Raw HTML is escaped instead of executed.

**In a public repository, draft files, images, and commit history remain visible on GitHub.** The draft flag controls inclusion in the blog; it does not make repository content private. Removing a published article cannot recall downloaded copies or caches.

`posts/hello-world.md` is a published example; edit or delete it before using your blog. `posts/draft-example.md` demonstrates a draft.

## Add images

Upload article images to `assets/<slug>/`. For `posts/my-first-post.md`, use a path such as `assets/my-first-post/cover.png`.

You can upload files through GitHub's **Add file → Upload files**. Reference them relative to the article:

```markdown
![A description](../assets/my-first-post/cover.png)
```

This path works in both GitHub's Markdown view and the published article.

PNG, JPEG, GIF, WebP, and AVIF files in published articles' folders are copied into the output. Draft images and other file types are excluded. Removing or unpublishing an article also removes its generated HTML, JSON, and images on the next successful deployment.

Link to another article with its generated filename, such as `[Another post](other-post.html)`.

## Generated output and JSON

```text
dist/
├── index.html                 # Article index
├── theme.css                  # Selected theme and shared styles
├── .nojekyll
├── posts.json                 # Article summaries, without bodies
├── posts/
│   ├── hello-world.html        # Article page
│   └── hello-world.json        # Article metadata and Markdown body
└── assets/
    └── hello-world/            # Images, when present
```

`dist/` is generated and ignored by Git. GitHub Actions runs the same build command and publishes only this directory.

Other websites and applications can consume the JSON:

| Path | Contents |
| --- | --- |
| `posts.json` | Summaries sorted newest first, then by slug for equal dates |
| `posts/<slug>.json` | Article metadata and Markdown body |

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

Resolve relative URLs in Markdown against the article's `posts/<slug>.html` or `posts/<slug>.json` URL. If you render the Markdown elsewhere, disable raw HTML or sanitize the output appropriately.

## Run locally

Use Python 3.12 or newer:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s test -v
python scripts/build.py
python -m http.server 8000 --directory dist
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

Open `http://localhost:8000/`. After changing posts, configuration, or theme files, rerun `python scripts/build.py` and refresh the page.

Invalid inputs or templates stop the build before replacing previous output. Failed tests or builds do not deploy.

## License

MIT License. See [LICENSE](LICENSE).

## References

- [GitHub Pages setup and supported plans](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Deploying to Pages with GitHub Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Markdown HTML handling](https://markdown-it-py.readthedocs.io/en/latest/security.html)
