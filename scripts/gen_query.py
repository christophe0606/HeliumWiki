#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML>=6.0"]
# ///
"""Generate helium-wiki/queries/by-<folder>.md from wiki frontmatter.

Run from the repository root during wiki generation:
    uv run scripts/gen_query.py

Hardware rows use features such as helium, with links to related wiki pages.
Features come from hardware_features/hardware_feature frontmatter, hardware
tags listed in data/tags.yaml, and related hardware-page IDs. Hardware pages
can also use feature/features; their page ID without a hardware- prefix is
the fallback feature identifier.

Language rows use asm, c, or cpp, with links to related wiki pages. Languages
come from language/languages fields, language tags, language-page IDs such as
languages-c-float16, and related language-page IDs. Assembly and C++ names
are normalized to asm and cpp. Both grouped indexes include pages from all
wiki folders, including nested pages.

Technique rows start with a linked page title, followed by tags, architecture,
confidence and reproducibility. Other folder indexes map page IDs to titles.

Markdown links are relative to queries/, e.g. ../wiki/techniques/example.md.
Empty folders still receive an index. Headerless README/index files are ignored.
Generation reads local YAML headers only, never makes network requests, and
resolves paths from this script's location. Existing indexes are refreshed;
unchanged files and other query files are left as they are. Invalid pages stop
generation before any indexes are written.
Exit codes: 0 = success, 2 = invalid metadata/configuration or a filesystem error.
"""

from __future__ import annotations

import argparse
import html
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOT = REPO_ROOT / "helium-wiki"
LANGUAGE_NAMES = {
    "asm": "asm", "assembly": "asm", "assembler": "asm",
    "c": "c", "cpp": "cpp", "c++": "cpp", "cplusplus": "cpp",
}


@dataclass
class Page:
    path: Path
    folder: str
    header: dict

    @property
    def id(self) -> str:
        return self.header["id"]

    @property
    def title(self) -> str:
        return self.header["title"]


def string_list(value, field: str) -> list[str]:
    if value is None:
        return []
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
        raise ValueError(f"{field} must be a string or a list of nonempty strings")
    return [item.strip() for item in values]


def read_header(file: Path) -> dict | None:
    with file.open("rb") as stream:
        if stream.readline().decode("utf-8-sig").rstrip() != "---":
            return None
        lines = []
        for raw_line in stream:
            line = raw_line.decode("utf-8")
            if line.rstrip() in ("---", "..."):
                break
            lines.append(line)
        else:
            raise ValueError("missing YAML frontmatter closing delimiter")
    header = yaml.safe_load("".join(lines))
    if not isinstance(header, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    for field in ("id", "title"):
        if not isinstance(header.get(field), str) or not header[field].strip():
            raise ValueError(f"frontmatter {field} must be a nonempty string")
    return header


def load_pages(wiki_root: Path) -> tuple[list[str], list[Page]]:
    if not wiki_root.is_dir():
        raise ValueError(f"wiki directory does not exist: {wiki_root}")
    folders = sorted(folder.name for folder in wiki_root.iterdir() if folder.is_dir() and not folder.name.startswith("."))
    pages, ids = [], {}
    for folder in folders:
        directory = wiki_root / folder
        if not directory.resolve().is_relative_to(wiki_root.resolve()):
            raise ValueError(f"{directory}: folder must stay inside wiki/")
        for file in sorted(directory.rglob("*.md")):
            try:
                if not file.resolve().is_relative_to(wiki_root.resolve()):
                    raise ValueError("page must stay inside wiki/")
                header = read_header(file)
                if header is None:
                    continue
                key = header["id"].casefold()
                if key in ids:
                    raise ValueError(f"duplicate page id {header['id']!r}; also used by {ids[key]}")
                ids[key] = file.relative_to(wiki_root).as_posix()
                pages.append(Page(file, folder, header))
            except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
                raise ValueError(f"{file.relative_to(wiki_root).as_posix()}: {error}") from error
    return folders, pages


def load_hardware_tags(file: Path) -> dict[str, str]:
    if not file.is_file():
        return {}  # Explicit feature fields and hardware-page IDs still work.
    configuration = yaml.safe_load(file.read_text(encoding="utf-8-sig"))
    if not isinstance(configuration, dict):
        raise ValueError("data/tags.yaml must contain a YAML mapping")
    tags = string_list(configuration.get("hardware_features"), "hardware_features vocabulary")
    return {tag.casefold(): tag for tag in tags}


def hardware_groups(pages: list[Page], vocabulary: dict[str, str]) -> dict[str, list[Page]]:
    features_by_page = {}
    names = dict(vocabulary)
    for page in pages:
        features = []
        for field in ("hardware_features", "hardware_feature"):
            features.extend(string_list(page.header.get(field), field))
        if page.folder.casefold() == "hardware":
            for field in ("features", "feature"):
                features.extend(string_list(page.header.get(field), field))
        for tag in string_list(page.header.get("tags"), "tags"):
            if tag.casefold() in vocabulary:
                features.append(vocabulary[tag.casefold()])
        if page.folder.casefold() == "hardware" and not features:
            features.append(page.id[len("hardware-") :] if page.id.casefold().startswith("hardware-") else page.id)
        keys = set()
        for feature in features:
            key = feature.casefold()
            names.setdefault(key, feature)
            keys.add(key)
        features_by_page[page.id.casefold()] = keys

    return related_groups(pages, features_by_page, "hardware", names)


def related_groups(
    pages: list[Page], identifiers_by_page: dict[str, set[str]], folder: str, names: dict[str, str]
) -> dict[str, list[Page]]:
    """Use tags/fields and links to category pages to associate relevant pages."""
    groups = defaultdict(dict)
    page_ids = {page.id.casefold(): page for page in pages}
    category_ids = {page.id.casefold() for page in pages if page.folder.casefold() == folder}
    for page in pages:
        keys = set(identifiers_by_page[page.id.casefold()])
        related = string_list(page.header.get("related"), "related")
        for reference in related:
            if reference.casefold() in category_ids:
                keys.update(identifiers_by_page[reference.casefold()])
        for key in keys:
            groups[key][page.path] = page
        if page.id.casefold() in category_ids:
            for reference in related:
                other = page_ids.get(reference.casefold())
                if other is not None:
                    for key in identifiers_by_page[page.id.casefold()]:
                        groups[key][other.path] = other
    return {
        names[key]: sorted(group.values(), key=lambda page: (page.title.casefold(), page.id.casefold()))
        for key, group in sorted(groups.items())
    }


def language_groups(pages: list[Page]) -> dict[str, list[Page]]:
    languages_by_page = {}
    for page in pages:
        values = []
        for field in ("language", "languages", "tags"):
            values.extend(string_list(page.header.get(field), field))
        languages = {LANGUAGE_NAMES[value.casefold()] for value in values if value.casefold() in LANGUAGE_NAMES}
        if page.folder.casefold() == "languages":
            page_id = page.id.casefold()
            for prefix in ("languages-", "language-"):
                for name, language in LANGUAGE_NAMES.items():
                    if page_id == prefix + name or page_id.startswith(prefix + name + "-"):
                        languages.add(language)
        languages_by_page[page.id.casefold()] = languages
    groups = related_groups(pages, languages_by_page, "languages", {name: name for name in ("asm", "c", "cpp")})
    return {name: groups.get(name, []) for name in ("asm", "c", "cpp")}


def markdown_text(value: str) -> str:
    text = html.escape(" ".join(value.split()), quote=False)
    for character in ("\\", "|", "[", "]", "*", "_", "`"):
        text = text.replace(character, "\\" + character)
    return text


def page_link(page: Page, output_directory: Path) -> str:
    relative = Path(os.path.relpath(page.path, output_directory)).as_posix()
    return f"[{markdown_text(page.title)}]({quote(relative, safe='/.-_~')})"


def render_table(folder: str, columns: list[str], rows: list[list[str]]) -> str:
    lines = [f"# By {markdown_text(folder)}", "", "<!-- Generated by scripts/gen_query.py. -->", "",
             "| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    if not rows:
        lines.extend(["", "No matching pages yet."])
    return "\n".join(lines) + "\n"


def render_index(folder: str, rows: list[tuple[str, list[Page]]], output_directory: Path) -> str:
    identifier = {"hardware": "Hardware feature", "languages": "Language"}.get(folder.casefold(), "Page ID")
    cells = []
    for key, pages in rows:
        links = "<br>".join(page_link(page, output_directory) for page in pages) or "—"
        cells.append([markdown_text(key), links])
    return render_table(folder, [identifier, "Related information"], cells)


def metadata_cell(page: Page, *fields: str) -> str:
    values = [value for field in fields for value in string_list(page.header.get(field), field)]
    return ", ".join(markdown_text(value) for value in dict.fromkeys(values)) or "—"


def render_techniques(folder: str, pages: list[Page], output_directory: Path) -> str:
    rows = [
        [page_link(page, output_directory), metadata_cell(page, "tags"),
         metadata_cell(page, "architectures", "architecture"), metadata_cell(page, "confidence"),
         metadata_cell(page, "reproducibility")]
        for page in sorted(pages, key=lambda page: (page.title.casefold(), page.id.casefold()))
        if page.folder == folder
    ]
    return render_table(folder, ["Technique", "Tags", "Architecture", "Confidence", "Reproducibility"], rows)


def generate(repo_root: Path = REPO_ROOT) -> list[Path]:
    repo_root = repo_root.resolve()
    skill_root = repo_root / "helium-wiki"
    wiki_root, output_directory = skill_root / "wiki", skill_root / "queries"
    if not wiki_root.resolve().is_relative_to(skill_root) or not output_directory.resolve().is_relative_to(skill_root):
        raise ValueError("wiki/ and queries/ must stay inside the skill folder")
    folders, pages = load_pages(wiki_root)
    vocabulary = load_hardware_tags(repo_root / "data" / "tags.yaml")
    hardware = hardware_groups(pages, vocabulary)
    languages = language_groups(pages)
    outputs = {}
    for folder in folders:
        file = output_directory / f"by-{folder}.md"
        if not file.resolve().is_relative_to(output_directory.resolve()):
            raise ValueError(f"{file}: output must stay inside queries/")
        if folder.casefold() == "techniques":
            outputs[file] = render_techniques(folder, pages, output_directory)
        else:
            if folder.casefold() == "hardware":
                rows = list(hardware.items())
            elif folder.casefold() == "languages":
                rows = list(languages.items())
            else:
                rows = [
                    (page.id, [page]) for page in sorted(pages, key=lambda page: (page.id.casefold(), page.path.as_posix()))
                    if page.folder == folder
                ]
            outputs[file] = render_index(folder, rows, output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)
    for file, content in outputs.items():
        if not file.is_file() or file.read_text(encoding="utf-8") != content:
            file.write_text(content, encoding="utf-8", newline="\n")
    return list(outputs)


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    if yaml is None:
        print("Error: PyYAML is required. Run this script with uv run.", file=sys.stderr)
        return 2
    try:
        outputs = generate(REPO_ROOT)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    for file in outputs:
        print(file.relative_to(REPO_ROOT.resolve()).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
