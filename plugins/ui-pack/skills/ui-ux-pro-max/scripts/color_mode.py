#!/usr/bin/env python3
"""Resolve color intent, palette coherence, contrast, and visible warnings."""

import re

_DARK_QUERY_MARKERS = (
    "dark mode",
    "dark theme",
    "dark ui",
    "darkmode",
    "night mode",
    "midnight",
    "oled",
    "koyu mod",
    "koyu tema",
    "karanlık mod",
    "karanlık tema",
)
_LIGHT_QUERY_MARKERS = (
    "light mode",
    "light theme",
    "light ui",
    "day mode",
    "açık mod",
    "açık tema",
)
_NEGATED_DARK_QUERY_MARKERS = (
    "no dark mode",
    "not dark mode",
    "not a dark mode",
    "not a dark theme",
    "avoid dark mode",
    "without dark mode",
    "do not use dark mode",
    "don't use dark mode",
    "dont use dark mode",
    "i do not want dark mode",
    "i don't want dark mode",
    "i dont want dark mode",
    "never use dark mode",
    "no dark theme",
    "not dark theme",
    "avoid dark theme",
    "without dark theme",
    "do not use dark theme",
    "i do not want a dark theme",
    "i don't want a dark theme",
    "i dont want a dark theme",
    "never use dark theme",
    "dark mode disabled",
    "dark mode is disabled",
    "dark mode off",
    "dark mode false",
    "dark theme disabled",
    "dark theme is disabled",
    "dark theme off",
    "dark theme false",
    "koyu mod olmasın",
    "koyu tema olmasın",
    "karanlık mod olmasın",
    "karanlık tema olmasın",
    "dark mode istemiyorum",
    "dark theme istemiyorum",
    "koyu mod istemiyorum",
    "koyu tema istemiyorum",
    "karanlık mod istemiyorum",
    "karanlık tema istemiyorum",
    "koyu mod kullanma",
    "koyu tema kullanma",
    "karanlık mod kullanma",
    "karanlık tema kullanma",
    "koyu mod kapalı",
    "koyu tema kapalı",
    "karanlık mod kapalı",
    "karanlık tema kapalı",
)
_NEGATED_LIGHT_QUERY_MARKERS = (
    "no light mode",
    "not light mode",
    "not a light mode",
    "not a light theme",
    "avoid light mode",
    "without light mode",
    "do not use light mode",
    "don't use light mode",
    "dont use light mode",
    "i do not want light mode",
    "i don't want light mode",
    "i dont want light mode",
    "never use light mode",
    "no light theme",
    "not light theme",
    "avoid light theme",
    "without light theme",
    "do not use light theme",
    "i do not want a light theme",
    "i don't want a light theme",
    "i dont want a light theme",
    "never use light theme",
    "light mode disabled",
    "light mode is disabled",
    "light mode off",
    "light mode false",
    "light theme disabled",
    "light theme is disabled",
    "light theme off",
    "light theme false",
    "açık mod olmasın",
    "açık tema olmasın",
    "light mode istemiyorum",
    "light theme istemiyorum",
    "açık mod istemiyorum",
    "açık tema istemiyorum",
    "açık mod kullanma",
    "açık tema kullanma",
    "açık mod kapalı",
    "açık tema kapalı",
)
_DARK_PRIMARY_MARKERS = (
    "dark mode primary",
    "dark primary",
    "dark only",
    "dark preferred",
    "dark focused",
    "dark first",
    "dark rich",
    "light mode only as exception",
)
_CONTRADICTORY_ANTI_PATTERNS = {
    "dark": {
        "dark mode",
        "dark modes",
        "dark theme",
        "dark mode by default",
        "dark theme by default",
        "default dark mode",
        "forced dark mode",
    },
    "light": {
        "light mode",
        "light modes",
        "light theme",
        "light mode default",
        "light mode by default",
        "light theme by default",
        "default light mode",
        "forced light mode",
        "light mode only",
    },
}
_DARK_BACKGROUND_MAX_LUMINANCE = 0.18
_WCAG_AA_NORMAL_TEXT_MIN_CONTRAST = 4.5


def _normalize_mode_text(value: str) -> str:
    """Normalize punctuation and whitespace without losing Turkish letters."""
    return re.sub(
        r"\s+", " ", re.sub(r"[-_=:]+", " ", value or "").lower()
    ).strip()


def _phrase_present(text: str, phrases: tuple) -> bool:
    """Match complete phrases so e.g. `highlight mode` is not `light mode`."""
    return any(
        re.search(r"(?<!\w){}(?!\w)".format(re.escape(phrase)), text)
        for phrase in phrases
    )


def _remove_phrases(text: str, phrases: tuple) -> str:
    for phrase in phrases:
        text = re.sub(
            r"(?<!\w){}(?!\w)".format(re.escape(phrase)), " ", text
        )
    return _normalize_mode_text(text)


def _query_color_mode(query: str) -> str:
    """Return dark, light, conflict, or auto from explicit query intent."""
    text = _normalize_mode_text(query)
    negates_dark = _phrase_present(text, _NEGATED_DARK_QUERY_MARKERS)
    negates_light = _phrase_present(text, _NEGATED_LIGHT_QUERY_MARKERS)
    positive_text = _remove_phrases(text, _NEGATED_DARK_QUERY_MARKERS)
    positive_text = _remove_phrases(positive_text, _NEGATED_LIGHT_QUERY_MARKERS)
    wants_dark = negates_light or _phrase_present(
        positive_text, _DARK_QUERY_MARKERS
    )
    wants_light = negates_dark or _phrase_present(
        positive_text, _LIGHT_QUERY_MARKERS
    )
    if wants_dark and wants_light:
        return "conflict"
    if wants_dark:
        return "dark"
    if wants_light:
        return "light"
    return "auto"


def _style_is_dark_primary(style: dict) -> bool:
    if not style:
        return False
    light_support = _normalize_mode_text(style.get("Light Mode ✓", ""))
    dark_support = _normalize_mode_text(style.get("Dark Mode ✓", ""))
    declared = "{} {}".format(light_support, dark_support)
    if _phrase_present(declared, _DARK_PRIMARY_MARKERS):
        return True
    light_is_exception = _phrase_present(
        light_support, ("no", "exception", "low", "inverted only")
    )
    dark_is_primary = _phrase_present(
        dark_support, ("only", "primary", "preferred", "full")
    )
    return light_is_exception and dark_is_primary


def _resolve_color_mode(query: str, style: dict) -> dict:
    """Let explicit intent win; use a dark-primary style only as fallback."""
    requested = _query_color_mode(query)
    if requested != "auto":
        return {"requested": requested, "source": "query"}
    if _style_is_dark_primary(style):
        return {"requested": "dark", "source": "style"}
    return {"requested": "auto", "source": "default"}


def _relative_luminance(hex_color: str):
    """Return WCAG relative luminance for a hex color, or None."""
    if not isinstance(hex_color, str) or not hex_color:
        return None
    value = hex_color.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    if len(value) != 6:
        return None
    try:
        channels = [int(value[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    except ValueError:
        return None
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _palette_value(palette: dict, csv_key: str, output_key: str) -> str:
    return (palette or {}).get(csv_key, (palette or {}).get(output_key, ""))


def _palette_mode(palette: dict) -> str:
    luminance = _relative_luminance(
        _palette_value(palette, "Background", "background")
    )
    if luminance is None:
        return "unknown"
    return "dark" if luminance < _DARK_BACKGROUND_MAX_LUMINANCE else "light"


def _contrast_ratio(palette: dict):
    background = _relative_luminance(
        _palette_value(palette, "Background", "background")
    )
    foreground = _relative_luminance(
        _palette_value(palette, "Foreground", "foreground")
    )
    if background is None or foreground is None:
        return None
    return (max(background, foreground) + 0.05) / (
        min(background, foreground) + 0.05
    )


def _select_palette_for_mode(palettes: list, mode: str) -> tuple:
    """Select the first accessible matching palette and report mode mismatch."""
    if not palettes:
        return {}, False
    if mode not in ("dark", "light"):
        return palettes[0], mode == "auto"
    matching = [palette for palette in palettes if _palette_mode(palette) == mode]
    if not matching:
        return palettes[0], False
    accessible = [
        palette
        for palette in matching
        if (_contrast_ratio(palette) or 0) >= _WCAG_AA_NORMAL_TEXT_MIN_CONTRAST
    ]
    return (accessible or matching)[0], True


def _filter_anti_patterns_for_mode(anti_patterns: str, mode: str) -> str:
    """Remove only exact advice that contradicts the chosen mode."""
    contradictory = _CONTRADICTORY_ANTI_PATTERNS.get(mode, set())
    if not anti_patterns or not contradictory:
        return anti_patterns
    kept = [
        clause.strip()
        for clause in anti_patterns.split("+")
        if clause.strip().lower().rstrip(".!;:") not in contradictory
    ]
    return " + ".join(kept)


def _color_mode_metadata(decision: dict, palette: dict, matched: bool) -> dict:
    requested = decision["requested"]
    resolved = _palette_mode(palette)
    ratio = _contrast_ratio(palette)
    warnings = []
    if requested == "conflict":
        warnings.append("Conflicting light and dark mode requests; kept top palette.")
    elif requested in ("dark", "light") and not matched:
        warnings.append(
            "No {} palette was returned; kept top palette.".format(requested)
        )
    if palette and ratio is None:
        warnings.append("Palette contrast could not be calculated.")
    elif ratio is not None and ratio < _WCAG_AA_NORMAL_TEXT_MIN_CONTRAST:
        warnings.append("Foreground/background contrast is below WCAG AA 4.5:1.")
    return {
        "requested": requested,
        "source": decision["source"],
        "resolved": resolved,
        "matched": matched,
        "contrast_ratio": round(ratio, 2) if ratio is not None else None,
        "wcag_aa_normal_text": (
            ratio is not None and ratio >= _WCAG_AA_NORMAL_TEXT_MIN_CONTRAST
        ),
        "warning": " ".join(warnings),
    }
