# Reliable Sources LLC FZ — Custom Acrylic + LED Neon Signs (UAE)

Premium one-page lead-generation website. Zero dependencies, no build step — deploy the folder as-is to any static host (GitHub Pages, Netlify, Vercel, cPanel).

## Business details — where they live

| What | Where |
|---|---|
| WhatsApp number (971563659384) + default message | `js/main.js` (`SITE` config at the top) |
| Per-button prefilled messages | `data-wa-msg` attributes in `index.html` |
| Company name / legal footer | `index.html` (header, footer, meta, JSON-LD) |
| Copy, FAQ, sections | `index.html` (plain HTML) |
| Gallery photos | `assets/img/*.webp` (optimized, ~1000px) |
| Design tokens (colors, fonts) | `:root` in `css/styles.css` |

No prices appear anywhere on the site — all CTAs route to a custom WhatsApp quote. Keep it that way when editing copy.

## Deploy

Upload the whole folder to any static host. Nothing to install or build.

Before/after deploying, set the final domain in the `og:image` URL if you want absolute social-preview links (relative paths work on most platforms).

## Run locally

```
python3 -m http.server 8000
```

## Adding a new gallery photo

1. Export/convert to WebP around 1000px on the long side.
2. Drop it in `assets/img/`.
3. Copy one `<figure class="card g-card">` block in `index.html`, update `src`, `width`/`height`, alt text and caption.
