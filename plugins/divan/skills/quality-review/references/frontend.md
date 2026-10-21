# Frontend and Product Quality

- Model loading, error, empty, and success states intentionally.
- Use semantic HTML and keyboard/focus behavior; do not emulate controls with generic clickable elements.
- Preserve shareable/filterable state in the URL when it is part of navigation.
- Avoid component APIs dominated by many boolean props; represent real modes explicitly.
- Reuse design tokens and existing UI primitives instead of magic spacing, colors, or z-index values.
- Use locale-aware number, date, and currency formatting where the product is localized.
