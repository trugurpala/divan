from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlsplit

PLUGIN_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")
# SemVer 2.0.0: https://semver.org/spec/v2.0.0.html
SEMVER_NUMERIC = r"(?:0|[1-9][0-9]*)"
SEMVER_PRERELEASE = r"(?:0|[1-9][0-9]*|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER_BUILD = r"[0-9A-Za-z-]+"
SEMVER_RE = re.compile(
    rf"{SEMVER_NUMERIC}\.{SEMVER_NUMERIC}\.{SEMVER_NUMERIC}"
    rf"(?:-{SEMVER_PRERELEASE}(?:\.{SEMVER_PRERELEASE})*)?"
    rf"(?:\+{SEMVER_BUILD}(?:\.{SEMVER_BUILD})*)?"
)
SKILL_DISCOVERY_SOFT_BUDGET = 6000
MAX_SKILL_DESCRIPTION = 1024
MAX_PLUGIN_DESCRIPTION = 1024
MAX_DISPLAY_NAME = 30
MAX_SHORT_DESCRIPTION_FINAL = 30
MAX_LONG_DESCRIPTION = 4000
MAX_CAPABILITIES = 20
MAX_DEFAULT_PROMPTS = 3
MAX_DEFAULT_PROMPT_LENGTH = 128
EXPECTED_ALPHA_SKILLS = 7
REQUIRED_QUALITY_REFERENCE = "plugins/divan/skills/quality-review/references/product-engineering.md"
FORBIDDEN_PROCESS_PATHS = ("docs/superpowers",)
INLINE_MARKDOWN_LINK_RE = re.compile(r"(?<!\\)\[[^\]\n]*\]\((<[^>\n]+>|[^\s()]+)\)")


def _markdown_prose(text: str) -> str:
    """Exclude fenced/indented code and matching backtick spans from link checks."""
    lines = []
    fence = ""
    for line in text.splitlines(keepends=True):
        if fence:
            if re.fullmatch(rf" {{0,3}}{re.escape(fence[0])}{{{len(fence)},}}\s*", line):
                fence = ""
            continue
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            fence = marker.group(1)
            continue
        if not line.startswith(("    ", "\t")):
            lines.append(line)
    return re.sub(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", " ", "".join(lines), flags=re.DOTALL)


def _validate_skill_links(plugin_root: Path, errors: list[str]) -> None:
    """Check simple inline [label](path) links, also images and <path with spaces>.

    This is a bounded syntax check, not a Markdown parser: nested labels,
    parenthesized destinations, titles, reference-style links and anchor names
    are not checked. Only skill Markdown is scanned; root README links may
    intentionally target repository documentation outside the package.
    """
    for source in sorted((plugin_root / "skills").rglob("*.md")):
        relative = source.relative_to(plugin_root).as_posix()
        try:
            prose = _markdown_prose(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"cannot read skill Markdown {relative}: {exc}")
            continue
        for match in INLINE_MARKDOWN_LINK_RE.finditer(prose):
            destination = match.group(1).removeprefix("<").removesuffix(">")
            try:
                url = urlsplit(destination)
                if url.scheme in {"http", "https", "mailto"} or destination.startswith("#"):
                    continue
                local_path = unquote(url.path).replace("\\", "/")
                target = (source.parent / local_path).resolve()
                if url.scheme or url.netloc or PureWindowsPath(local_path).drive or not target.is_relative_to(plugin_root):
                    errors.append(f"local Markdown reference outside plugin in {relative}: {destination}")
                elif local_path and not target.is_file():
                    errors.append(f"missing local Markdown reference in {relative}: {destination}")
            except (OSError, RuntimeError, ValueError) as exc:
                errors.append(f"invalid Markdown reference in {relative}: {destination}: {exc}")


def _validate_skill_licenses(plugin_root: Path, errors: list[str]) -> None:
    """Keep the full notice when a skill folder is distributed on its own."""
    try:
        canonical = (plugin_root / "LICENSE").read_bytes()
    except OSError as exc:
        errors.append(f"cannot read plugin LICENSE: {exc}")
        return
    if not canonical.strip():
        errors.append("plugin LICENSE must not be empty")
        return

    for skill in sorted((plugin_root / "skills").iterdir()):
        if not skill.is_dir():
            continue
        notice = skill / "LICENSE"
        relative = notice.relative_to(plugin_root).as_posix()
        try:
            content = notice.read_bytes()
        except OSError as exc:
            errors.append(f"cannot read skill license {relative}: {exc}")
            continue
        if content != canonical:
            errors.append(f"skill license must match plugin LICENSE: {relative}")


def _load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing required file: {path}")
        return {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON at {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected JSON object at {path}")
        return {}
    return value


def _parse_skill_frontmatter(path: Path, errors: list[str]) -> tuple[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        errors.append(f"missing SKILL.md: {path}")
        return "", ""
    except UnicodeDecodeError as exc:
        errors.append(f"SKILL.md must be UTF-8: {path}: {exc}")
        return "", ""

    if not text.startswith("---\n"):
        errors.append(f"missing YAML frontmatter: {path}")
        return "", ""
    end = text.find("\n---\n", 4)
    if end == -1:
        errors.append(f"unterminated YAML frontmatter: {path}")
        return "", ""

    fields: dict[str, str] = {}
    for raw_line in text[4:end].splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if ":" not in raw_line:
            errors.append(f"unsupported frontmatter line in {path}: {raw_line}")
            continue
        key, value = raw_line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")

    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        errors.append(f"skill name missing: {path}")
    if not description:
        errors.append(f"skill description missing: {path}")
    if len(description) > MAX_SKILL_DESCRIPTION:
        errors.append(f"skill description exceeds {MAX_SKILL_DESCRIPTION}: {path}")
    if not text[end + 5 :].strip():
        errors.append(f"skill body is empty: {path}")
    return name, description


def _validate_manifest(manifest: dict, errors: list[str]) -> None:
    name = manifest.get("name")
    if not isinstance(name, str) or not PLUGIN_NAME_RE.fullmatch(name):
        errors.append("plugin name must be stable kebab-case")
    if isinstance(name, str) and len(name) > 64:
        errors.append("plugin name exceeds 64 characters")

    version = manifest.get("version")
    if not isinstance(version, str) or len(version) > 64 or not SEMVER_RE.fullmatch(version):
        errors.append("plugin version must be SemVer and at most 64 characters")

    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("plugin description is required")
    elif len(description) > MAX_PLUGIN_DESCRIPTION:
        errors.append(f"plugin description exceeds {MAX_PLUGIN_DESCRIPTION} characters")

    if manifest.get("skills") != "./skills/":
        errors.append("Divan skills path must be ./skills/")

    if manifest.get("requires_local_executor") is not True:
        errors.append("requires_local_executor must be true")

    forbidden = [field for field in ("mcpServers", "apps", "hooks") if field in manifest]
    if forbidden:
        errors.append(f"skills-only Divan must not include MCP/app fields: {', '.join(forbidden)}")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin interface metadata is required")
        return

    display = interface.get("displayName")
    if not isinstance(display, str) or not display.strip() or len(display) > MAX_DISPLAY_NAME:
        errors.append(f"interface.displayName must be 1-{MAX_DISPLAY_NAME} characters")

    short = interface.get("shortDescription")
    if not isinstance(short, str) or not short.strip() or "\n" in short or len(short) > MAX_SHORT_DESCRIPTION_FINAL:
        errors.append(f"interface.shortDescription must be one line and <= {MAX_SHORT_DESCRIPTION_FINAL} characters")

    long_description = interface.get("longDescription")
    if not isinstance(long_description, str) or not long_description.strip() or len(long_description) > MAX_LONG_DESCRIPTION:
        errors.append(f"interface.longDescription must be 1-{MAX_LONG_DESCRIPTION} characters")

    developer = interface.get("developerName")
    if not isinstance(developer, str) or not developer.strip():
        errors.append("interface.developerName is required")

    capabilities = interface.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("interface.capabilities must be a non-empty list")
    elif len(capabilities) > MAX_CAPABILITIES:
        errors.append(f"interface.capabilities exceeds {MAX_CAPABILITIES}")

    prompts = interface.get("defaultPrompt")
    if not isinstance(prompts, list) or not prompts:
        errors.append("interface.defaultPrompt must be a non-empty list")
    else:
        if len(prompts) > MAX_DEFAULT_PROMPTS:
            errors.append(f"interface.defaultPrompt exceeds {MAX_DEFAULT_PROMPTS}")
        normalized: set[str] = set()
        for prompt in prompts:
            if not isinstance(prompt, str) or not prompt.strip():
                errors.append("starter prompts must be non-empty strings")
                continue
            if "\n" in prompt or len(prompt) > MAX_DEFAULT_PROMPT_LENGTH:
                errors.append(f"starter prompt must be one line and <= {MAX_DEFAULT_PROMPT_LENGTH} characters")
            if "@" in prompt:
                errors.append("starter prompts must not contain @mentions")
            key = " ".join(prompt.split()).casefold()
            if key in normalized:
                errors.append("starter prompts must be unique")
            normalized.add(key)


def _validate_marketplace(repo: Path, errors: list[str]) -> None:
    path = repo / ".agents" / "plugins" / "marketplace.json"
    market = _load_json(path, errors)
    if not market:
        return
    interface = market.get("interface")
    if not isinstance(interface, dict) or not isinstance(interface.get("displayName"), str) or not interface["displayName"].strip():
        errors.append("marketplace interface.displayName is required")

    plugins = market.get("plugins")
    if not isinstance(plugins, list):
        errors.append("marketplace.plugins must be a list")
        return
    divan = next((item for item in plugins if isinstance(item, dict) and item.get("name") == "divan"), None)
    if divan is None:
        errors.append("marketplace must expose divan")
        return
    source = divan.get("source")
    if not isinstance(source, dict) or source.get("source") != "local" or source.get("path") != "./plugins/divan":
        errors.append("marketplace Divan source must be local ./plugins/divan")


def _validate_repo_hygiene(repo: Path, errors: list[str]) -> None:
    for relative in FORBIDDEN_PROCESS_PATHS:
        if (repo / relative).exists():
            errors.append(f"internal process artifact must not ship: {relative}")
    if not (repo / REQUIRED_QUALITY_REFERENCE).is_file():
        errors.append(f"missing required product quality reference: {REQUIRED_QUALITY_REFERENCE}")


def validate_repository(repo: Path) -> list[str]:
    repo = repo.resolve()
    errors: list[str] = []
    plugin_root = repo / "plugins" / "divan"
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    manifest = _load_json(manifest_path, errors)
    if manifest:
        _validate_manifest(manifest, errors)

    skills_root = plugin_root / "skills"
    if not skills_root.is_dir():
        errors.append(f"missing skills directory: {skills_root}")
    else:
        seen: set[str] = set()
        discovery_chars = 0
        for child in sorted(skills_root.iterdir()):
            if not child.is_dir():
                errors.append(f"skills/ may contain only skill directories: {child}")
                continue
            name, description = _parse_skill_frontmatter(child / "SKILL.md", errors)
            if not name:
                continue
            if not PLUGIN_NAME_RE.fullmatch(name):
                errors.append(f"skill name must be kebab-case: {name}")
            if name != child.name:
                errors.append(f"skill name {name!r} must match folder {child.name!r}")
            if name in seen:
                errors.append(f"duplicate skill name: {name}")
            seen.add(name)
            relative = (child / "SKILL.md").relative_to(repo).as_posix()
            discovery_chars += len(name) + len(description) + len(relative)

        if len(seen) != EXPECTED_ALPHA_SKILLS:
            errors.append(f"Divan alpha must contain exactly 7 skills, found {len(seen)}")
        if discovery_chars > SKILL_DISCOVERY_SOFT_BUDGET:
            errors.append(f"skill discovery soft budget exceeded: {discovery_chars} > {SKILL_DISCOVERY_SOFT_BUDGET}")
        _validate_skill_links(plugin_root, errors)
        _validate_skill_licenses(plugin_root, errors)

    forbidden_artifacts = [plugin_root / "hooks", plugin_root / ".mcp.json", plugin_root / ".app.json"]
    present = [path.relative_to(plugin_root).as_posix() for path in forbidden_artifacts if path.exists()]
    if present:
        errors.append(f"skills-only published alpha must not contain: {', '.join(present)}")

    _validate_marketplace(repo, errors)
    _validate_repo_hygiene(repo, errors)
    return errors


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    errors = validate_repository(repo)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Divan V2 plugin validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
