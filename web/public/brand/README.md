# Odoolings brand assets

These files are rendered from the same mixed Geist Pixel wordmark and color tokens used
by the website. Regenerate the full set from `web/` with:

```bash
npm run brand:export
```

## Files

| File | Size | Intended use |
| --- | ---: | --- |
| `odoolings-wordmark-on-paper.png` | 2400×720 | Full wordmark on the warm light canvas |
| `odoolings-wordmark-on-ink.png` | 2400×720 | Full wordmark on the near-black canvas |
| `odoolings-wordmark-ink-transparent.png` | 2400×720 | Transparent asset for light backgrounds |
| `odoolings-wordmark-paper-transparent.png` | 2400×720 | Transparent asset for dark backgrounds |
| `odoolings-social-card-paper.png` | 1200×630 | Light Open Graph/social post card |
| `odoolings-social-card-ink.png` | 1200×630 | Dark Open Graph/social post card |
| `odoolings-avatar-paper.png` | 1024×1024 | Light square profile/project mark |
| `odoolings-avatar-ink.png` | 1024×1024 | Dark square profile/project mark |

## Core colors

- Warm paper: `hsl(45 22% 95%)`
- Warm ink: `hsl(30 8% 9%)`
- Violet on light: `hsl(255 55% 52%)`
- Violet on dark: `hsl(255 85% 76%)`

Use the transparent variants when placing the identity over another design. Keep clear
space around the wordmark and do not recolor individual glyphs: the neutral `Odoo` and
violet `lings` split is part of the identity.
