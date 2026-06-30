# Overlay Brand Shell Design

## Goal

Make Daanaa's static state, category, and giving-guide pages feel like the main
site while preserving fast, fully rendered HTML for search engines and AI
systems.

## Scope

- Replace the hard-coded growth-page shell in
  `visibility/scripts/build_growth_pages.py`.
- Use the main site's navy, cream, gold, link, border, and typography tokens.
- Add a responsive static navigation, breadcrumb, and full footer.
- Present repeated directory entries as compact, accessible list items.
- Add optional client-side filtering to state, category, and guide indexes while
  retaining all entries in the initial HTML.
- Keep state/category sample selection, content, canonical URLs, sitemap logic,
  and organization destinations unchanged.

## Structure

The page remains static. The shell provides a white navigation band, a
warm-cream page surface, a 1200px responsive content container, and a deep-navy
footer. Display headings use Cormorant Garamond, branding uses Cinzel, and body
copy uses DM Sans with system fallbacks.

Index pages receive a labeled filter input and an `aria-live` result count.
The small enhancement script hides nonmatching list items; without JavaScript,
the complete directory remains visible and usable.

## Accessibility

Body and link colors meet WCAG AA on light surfaces. Navigation and breadcrumbs
have labels, focus states are visible, touch targets are at least 40px where
applicable, and filtering does not remove content from the source HTML.

## Deployment Safety

The change affects generated static growth pages only. It does not import the
React bundle, share compiled CSS, alter the droplet, or change database/API
behavior. It will deploy with the already-tested clean canonical URL build.
