"""Static HTML, link, robots, and sitemap validation for the SEO audit."""

from __future__ import annotations

import json
import pathlib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit


class _Markup(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = False
        self.title_text: list[str] = []
        self.meta: list[dict[str, str]] = []
        self.link_tags: list[dict[str, str]] = []
        self.anchors: list[dict[str, str]] = []
        self._json_ld = False
        self.json_ld: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self.title = True
        elif tag == "meta":
            self.meta.append(values)
        elif tag == "link":
            self.link_tags.append(values)
        elif tag == "a":
            self.anchors.append(values)
        elif tag == "script":
            self._json_ld = (
                values.get("type", "").casefold() == "application/ld+json"
            )

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.title = False
        elif tag == "script":
            self._json_ld = False

    def handle_data(self, data: str) -> None:
        if self.title:
            self.title_text.append(data)
        if self._json_ld:
            self.json_ld.append(data)


def absolute_http_url(value: str) -> bool:
    parsed = urlsplit(value.strip())
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
    )


def _has_meta(
    markup: _Markup,
    key: str,
    value: str | None = None,
    *,
    absolute_url: bool = False,
    expected_origin: str | None = None,
) -> bool:
    for row in markup.meta:
        identity = (row.get("name") or row.get("property") or "").casefold()
        content = row.get("content", "").strip()
        if identity != key.casefold() or not content:
            continue
        if value is not None and content.casefold() != value.casefold():
            continue
        if absolute_url and not absolute_http_url(content):
            continue
        if expected_origin is not None and _origin(content) != expected_origin:
            continue
        return True
    return False


def _origin(value: str) -> str:
    parsed = urlsplit(value.strip())
    return f"{parsed.scheme}://{parsed.netloc}"


def _has_link(
    markup: _Markup,
    rel: str,
    hreflang: str | None = None,
    *,
    expected_origin: str | None = None,
    exact_url: str | None = None,
) -> bool:
    for row in markup.link_tags:
        relations = row.get("rel", "").casefold().split()
        href = row.get("href", "").strip()
        if rel.casefold() not in relations or not absolute_http_url(href):
            continue
        if expected_origin is not None and _origin(href) != expected_origin:
            continue
        if exact_url is not None and href != exact_url:
            continue
        if hreflang is None or row.get("hreflang", "").casefold() == hreflang:
            return True
    return False


def _internal_link_findings(
    root: pathlib.Path, html_path: pathlib.Path, markup: _Markup
) -> list[str]:
    missing: list[str] = []
    for row in markup.anchors:
        href = row.get("href", "").strip()
        parsed = urlsplit(href)
        if (
            not href
            or parsed.scheme
            or parsed.netloc
            or href.startswith(("#", "mailto:", "tel:", "javascript:"))
        ):
            continue
        local = (html_path.parent / parsed.path).resolve()
        try:
            local.relative_to(root)
        except ValueError:
            missing.append(parsed.path)
            continue
        if parsed.path.endswith("/") and local.is_dir():
            local = local / "index.html"
        if local.is_symlink() or not local.is_file():
            missing.append(parsed.path)
    return sorted(set(missing))


def _structured_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for item in value for row in _structured_rows(item)]
    if not isinstance(value, dict):
        return []
    rows = [value]
    if "@graph" in value:
        rows.extend(_structured_rows(value["@graph"]))
    return rows


def _valid_structured_data(markup: _Markup) -> bool:
    for raw in markup.json_ld:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for row in _structured_rows(value):
            context = row.get("@context")
            row_type = row.get("@type")
            if context != "https://schema.org" or not isinstance(row.get("name"), str):
                continue
            if row_type == "SoftwareApplication" and all(
                isinstance(row.get(field), str) and row[field].strip()
                for field in ("applicationCategory", "operatingSystem")
            ):
                return True
            if (
                row_type == "SoftwareSourceCode"
                and all(
                    isinstance(row.get(field), str) and row[field].strip()
                    for field in ("codeRepository", "license", "programmingLanguage")
                )
                and absolute_http_url(row["codeRepository"])
            ):
                return True
    return False


def _valid_robots(root: pathlib.Path, expected_origin: str | None) -> bool:
    path = root / "robots.txt"
    if not path.is_file() or path.is_symlink():
        return False
    lines = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    has_agent = any(line.casefold().startswith("user-agent:") for line in lines)
    has_rule = any(
        line.casefold().startswith(("allow:", "disallow:")) for line in lines
    )
    sitemap_rows = [
        line.split(":", 1)[1].strip()
        for line in lines
        if line.casefold().startswith("sitemap:")
    ]
    return has_agent and has_rule and any(
        absolute_http_url(row)
        and (expected_origin is None or _origin(row) == expected_origin)
        for row in sitemap_rows
    )


def _valid_sitemap(root: pathlib.Path, expected_origin: str | None) -> bool:
    path = root / "sitemap.xml"
    if not path.is_file() or path.is_symlink():
        return False
    try:
        document = ET.fromstring(path.read_text(encoding="utf-8"))
    except (UnicodeError, ET.ParseError):
        return False
    if document.tag.rsplit("}", 1)[-1] != "urlset":
        return False
    locations = [
        element.text.strip()
        for element in document.iter()
        if element.tag.rsplit("}", 1)[-1] == "loc"
        and isinstance(element.text, str)
        and element.text.strip()
    ]
    return bool(locations) and all(
        absolute_http_url(row)
        and (expected_origin is None or _origin(row) == expected_origin)
        for row in locations
    )


def _check(check_id: str, passed: bool, details: str = "") -> dict[str, str]:
    return {
        "id": check_id,
        "status": "PASS" if passed else "FAIL",
        "details": details,
    }


def _unobserved_checks() -> list[dict[str, str]]:
    return [
        {
            "id": check_id,
            "status": "NOT_OBSERVED",
            "details": "runtime-rendered; external observations required",
        }
        for check_id in (
            "canonical",
            "description",
            "hreflang",
            "internal-links",
            "json-ld",
            "open-graph",
            "robots",
            "sitemap",
            "title",
            "twitter-card",
        )
    ]


def static_checks(
    root: pathlib.Path,
    files: list[pathlib.Path],
    expected_url: str | None = None,
) -> list[dict[str, str]]:
    html_paths = [
        path for path in files if path.suffix.casefold() in {".html", ".htm"}
    ]
    if not html_paths:
        return _unobserved_checks()
    entry = next(
        (path for path in html_paths if path.name.casefold() == "index.html"),
        html_paths[0],
    )
    markup = _Markup()
    markup.feed(entry.read_text(encoding="utf-8"))
    missing_links = _internal_link_findings(root, entry, markup)
    expected_origin = _origin(expected_url) if expected_url else None
    checks = [
        _check("title", bool("".join(markup.title_text).strip())),
        _check("description", _has_meta(markup, "description")),
        _check(
            "canonical",
            _has_link(
                markup,
                "canonical",
                expected_origin=expected_origin,
                exact_url=expected_url,
            ),
        ),
        _check(
            "hreflang",
            _has_link(
                markup, "alternate", "en", expected_origin=expected_origin
            )
            and _has_link(
                markup, "alternate", "tr", expected_origin=expected_origin
            ),
        ),
        _check(
            "open-graph",
            all(
                _has_meta(
                    markup,
                    key,
                    absolute_url=key in {"og:image", "og:url"},
                    expected_origin=(
                        expected_origin if key in {"og:image", "og:url"} else None
                    ),
                )
                for key in ("og:title", "og:description", "og:image", "og:url")
            ),
        ),
        _check(
            "twitter-card",
            _has_meta(markup, "twitter:card", "summary_large_image")
            and _has_meta(markup, "twitter:image", absolute_url=True),
        ),
        _check("json-ld", _valid_structured_data(markup)),
        _check("robots", _valid_robots(root, expected_origin)),
        _check("sitemap", _valid_sitemap(root, expected_origin)),
        _check("internal-links", not missing_links, ", ".join(missing_links)),
    ]
    return sorted(checks, key=lambda row: row["id"])
