# Theme design QA

## Targets and intentional changes

- Literary source: `/tmp/git-cms-design-options/design-1.png`.
- Notebook source: `/tmp/git-cms-design-options/design-2.png`.
- The user requested English-only copy and removal of the third-party icon library. English titles, an editable English headline, text links, and a plain typographic monogram are intentional adaptations.
- Preview fixtures contain three posts to match the density of the source concepts. Two fixture posts exist only in `/tmp/git-cms-theme-preview/`; they are not added to the repository.

## First comparison

- Implementation: `/tmp/git-cms-theme-evidence/literary-desktop.png` and `notebook-desktop.png`.
- Side-by-side evidence: `/tmp/git-cms-theme-evidence/literary-comparison.png` and `notebook-comparison.png`.
- CSS viewport: 1440 × 1000 at device scale factor 1. Literary source: 1505 × 1045; notebook source: 1506 × 1045. Sources are proportionally contained in a 1440 × 1000 comparison frame; implementation screenshots are 1440 × 1000. Each combined image is 2880 × 1000.
- [P2] Literary vertical rhythm: the feature section starts approximately 40px lower than in the concept, pushing the footer below the initial viewport. Fix: reduce the intro's bottom padding and tighten the featured title's line height.
- Notebook: no actionable P0/P1/P2 differences after accounting for the requested English copy and text links.

## Verification

- Both themes: index and article pages at 1440 × 1000 and 390 × 844; no horizontal overflow.
- Opening an article and returning to the index passed in all four theme/viewport combinations.
- Light and dark mobile screenshots captured; no JavaScript exceptions reported.
- Automated build and configuration tests passed.

## Post-fix comparison

- Reduced literary intro bottom padding from 66px to 28px and featured-title line height from 1.5 to 1.35. The fresh comparison shows the feature and two-column list aligned to the intended rhythm, with the footer visible again.
- Increased text-link size to 13px for readability after the requested icon removal.
- Fresh full-view comparisons: `/tmp/git-cms-theme-evidence/literary-comparison.png` and `notebook-comparison.png`.
- Focused headline/feature and sidebar/list comparisons: `/tmp/git-cms-theme-evidence/literary-focus.png` and `notebook-focus.png`. These are combined source/implementation captures at the same scale, cropped to the key typography and spacing regions.
- Mobile index screenshots: `literary-mobile.png` and `notebook-mobile.png` in the same evidence directory. Article screenshots: `literary-article-mobile.png` and `notebook-article-mobile.png`. Dark captures: `literary-dark-mobile.png` and `notebook-dark-mobile.png`.
- Interaction results: `/tmp/git-cms-theme-evidence/results.json`. All four theme/viewport combinations passed article and back navigation. Viewport/scroll widths matched at 1440px and 390px. No runtime exceptions were reported. The generated site has no client JavaScript.

## Required fidelity surfaces

- Fonts and typography: system serif headlines and article titles preserve the source hierarchy; metadata and controls use system sans-serif or monospace. English copy is an intentional adaptation. Mobile headlines wrap without clipping.
- Spacing and layout: literary hero, featured post, and two-column secondary list follow the source composition after the rhythm fix. Notebook preserves the quarter-width sidebar, monthly grouping, and date column. Mobile layouts stack appropriately and article text remains readable.
- Colors and tokens: literary uses warm paper, dark ink, and rust accents; notebook uses sage, off-white, and evergreen. Both light and dark screenshots were inspected for readable text and controls.
- Assets: no third-party icon assets or accompanying licenses remain. Text links and the typographic wordmark/initials follow the user's explicit direction. No photographs or illustrations are required by either layout.
- Copy and content: interface, settings, sample posts, README, and errors are English only. There is no locale selector or translation implementation. Preview-only demonstration posts are not included in the production build.

## Findings and remaining limits

- No actionable P0/P1/P2 findings remain.
- P3: serif shapes vary by installed system font. This is accepted to keep both themes independent of external font services.
- No GitHub deployment was triggered; Pages configuration remains a repository-owner setup step.

## Implementation checklist

- [x] Both themes selectable through `config/site.yaml`.
- [x] Index, article, empty, light, and dark presentations implemented.
- [x] English-only interface and examples; third-party icon assets removed.
- [x] Stable JSON, draft exclusion, theme validation, and relative links verified by 13 tests.
- [x] Desktop/mobile browser checks and fresh post-fix visual comparison passed.

## Newspaper theme verification

- Target: the approved written brief for a third, newspaper-style theme. No raster reference was selected for this addition; this is an implementation review, not a claim of pixel fidelity to an image.
- Evidence: `/tmp/git-cms-theme-evidence/newspaper-desktop.png`, `newspaper-mobile.png`, `newspaper-article-mobile.png`, and `newspaper-dark-mobile.png`.
- Viewports: 1440 × 1000 and 390 × 844 CSS pixels, device scale factor 1.
- Reviewed centered serif masthead, dateline, ruled lead/sidebar layout, three-column additional stories, and single-column article text with drop cap. Light/dark colors remain readable; no assets or external font/icon licenses were added.
- The latest published date identifies the index edition; each article shows its own publication date. Empty, single-post, and multiple-post arrangements are covered by automated tests.
- All three themes passed index-to-article and back navigation at both viewports, without horizontal overflow or runtime exceptions. Test suite: 14 passing tests. JSON remains identical across all three themes.
- Preview-only fixture posts were added under `/tmp/git-cms-theme-preview/newspaper/`; repository posts were not expanded for the design review.
- No actionable P0/P1/P2 findings remain. Live GitHub Pages deployment was not run.

final result: passed
