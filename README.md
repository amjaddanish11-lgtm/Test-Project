# Noor Neon — Custom Acrylic + LED Neon Signs (UAE)

Premium one-page lead-generation website. Zero dependencies, no build step — deploy the folder as-is to any static host (GitHub Pages, Netlify, Vercel, cPanel).

## Before going live — 2 required edits

1. **WhatsApp number** — edit `js/main.js`, top of file:
   ```js
   whatsapp: "971500000000", // ← replace with your real number, digits only
   ```
2. **Brand name** — "Noor Neon" is a placeholder. Find & replace `Noor Neon` / `NOOR NEON` in `index.html`.

## Where things live

| What | Where |
|---|---|
| WhatsApp number + default message | `js/main.js` (`SITE` config) |
| Per-button prefilled messages | `data-wa-msg` attributes in `index.html` |
| Pricing, FAQ, copy | `index.html` (plain HTML sections) |
| Gallery photos | `assets/img/*.webp` (optimized WebP, ~1000px) |
| Design tokens (colors, fonts) | `:root` in `css/styles.css` |

## Run locally

```
python3 -m http.server 8000
```
