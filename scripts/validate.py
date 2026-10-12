#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML>=6.0"]
# ///
"""Validate wiki YAML frontmatter using data/schemas.yaml and data/tags.yaml.

Usage: uv run scripts/validate.py <wiki.md> <.flow/errors.md>
A bare report filename is placed in the project's .flow directory. Exit codes:
0 = valid; 1 = invalid page; 2 = configuration, dependency, or output error.
Only the header is validated. Types are checked for controlled vocabulary fields;
no additional type constraints are imposed on fields absent from tags.yaml.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Problem:
    message: str
    fix: str
    field: str | None = None
    line: int | None = None


if yaml is not None:
    class UniqueKeyLoader(yaml.SafeLoader):
        """Reject repeated explicit mapping keys instead of silently overwriting."""

        def construct_mapping(self, node, deep=False):
            seen = {}
            for key_node, _ in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":
                    continue
                key = self.construct_object(key_node, deep=deep)
                try:
                    if key in seen:
                        raise yaml.constructor.ConstructorError(
                            f"Duplicate mapping key {key!r}; first defined here",
                            seen[key], "Each mapping key must appear only once",
                            key_node.start_mark,
                        )
                    seen[key] = key_node.start_mark
                except TypeError:
                    raise yaml.constructor.ConstructorError(
                        "While reading a mapping", node.start_mark,
                        "Mapping keys must be scalar values", key_node.start_mark,
                    ) from None
            return super().construct_mapping(node, deep=deep)


def yaml_problem(error, label, offset=0):
    mark = getattr(error, "problem_mark", None)
    detail = getattr(error, "problem", None) or str(error)
    context = getattr(error, "context", None)
    if context:
        detail = f"{context}: {detail}"
    if mark:
        detail += f" (line {mark.line + 1}, column {mark.column + 1})" if offset is None else f" (column {mark.column + 1})"
    return Problem(
        f"{label} is not valid YAML: {detail}.",
        "Correct the YAML syntax, indentation, or duplicate keys and validate again.",
        line=mark.line + 1 + offset if mark and offset is not None else None,
    )


def load_configuration():
    def read(name):
        try:
            return yaml.load((ROOT / "data" / name).read_text(encoding="utf-8-sig"), Loader=UniqueKeyLoader)
        except yaml.YAMLError as error:
            error.configuration_path = "data/" + name
            raise

    schemas = read("schemas.yaml")
    if not isinstance(schemas, dict) or not isinstance(schemas.get("wiki"), dict):
        raise ValueError("data/schemas.yaml must define a 'wiki' mapping")
    required = schemas["wiki"].get("required")
    optional = schemas["wiki"].get("optional", [])
    for name, fields in (("required", required), ("optional", optional)):
        if not isinstance(fields, list) or any(not isinstance(f, str) or not f.strip() for f in fields):
            raise ValueError(f"wiki.{name} must be a list of nonempty field names")
        if len(set(fields)) != len(fields):
            raise ValueError(f"wiki.{name} contains duplicate field names")
    if set(required) & set(optional):
        raise ValueError("A schema field cannot be both required and optional")
    vocabularies = read("tags.yaml")
    if not isinstance(vocabularies, dict):
        raise ValueError("data/tags.yaml must be a mapping of vocabulary names to lists")
    for name, values in vocabularies.items():
        if not isinstance(name, str):
            raise ValueError("Vocabulary names must be strings")
        if values is None:
            vocabularies[name] = []  # Empty YAML categories allow no values.
        elif not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError(f"Vocabulary '{name}' must be a list of nonempty strings")
    if "architectures" in required + optional and "architectures" not in vocabularies:
        raise ValueError("data/tags.yaml must define the 'architectures' vocabulary")
    return required, optional, vocabularies


def read_header(page):
    try:
        lines = page.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        return None, {}, [Problem(f"Cannot read the wiki Markdown file: {error}.", "Check the file path, permissions, and UTF-8 encoding.")]
    if not lines or lines[0].rstrip() != "---":
        return None, {}, [Problem("The file must start with a YAML opening delimiter (---).", "Put the YAML header at the beginning of the file, between delimiter lines.", line=1)]
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip() in ("---", "...")), None)
    if end is None:
        return None, {}, [Problem("The YAML header has no closing delimiter.", "Add a line containing --- after the header and before the Markdown body.", line=1)]
    loader = UniqueKeyLoader("\n".join(lines[1:end]))
    try:
        node = loader.get_single_node()
        header = loader.construct_document(node) if node is not None else None
        locations = {}
        if isinstance(node, yaml.MappingNode):
            locations = {k.value: k.start_mark.line + 2 for k, _ in node.value if k.tag == "tag:yaml.org,2002:str"}
    except yaml.YAMLError as error:
        return None, {}, [yaml_problem(error, "The frontmatter", offset=1)]
    finally:
        loader.dispose()
    if not isinstance(header, dict):
        return None, {}, [Problem("The YAML header must be a mapping of field names to values.", "Use entries such as 'title: Example' instead of an empty header, scalar, or list.", line=2)]
    return header, locations, []


def values_hint(allowed, category):
    if allowed:
        return "Allowed values: " + ", ".join(sorted(allowed)) + "."
    return f"The '{category}' vocabulary in data/tags.yaml is empty. Use [] or add the intended value to that vocabulary."


def validate_header(header, locations, required, optional, vocabularies):
    problems = []
    permitted = set(required + optional)
    for field in required:
        if field not in header:
            problems.append(Problem(f"Required field '{field}' is missing.", "Add this field as required by data/schemas.yaml.", field))
        elif header[field] is None or (isinstance(header[field], str) and not header[field].strip()):
            problems.append(Problem(f"Required field '{field}' has no value.", "Provide a value; use [] explicitly for a list with no entries.", field, locations.get(field)))
    all_tags = {v for values in vocabularies.values() for v in values}
    for field, value in header.items():
        line = locations.get(field)
        if not isinstance(field, str) or field not in permitted:
            problems.append(Problem(f"Field {field!r} is not declared in the wiki schema.", "Use only these fields: " + ", ".join(required + optional) + ".", str(field), line))
            continue
        if field != "tags" and field not in vocabularies:
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            if field not in required:
                problems.append(Problem(f"Field '{field}' has no controlled value.", "Omit the optional field or provide a registered value.", field, line))
            continue
        allowed = all_tags if field == "tags" else set(vocabularies[field])
        if field in ("tags", "architectures"):
            if not isinstance(value, list):
                problems.append(Problem(f"Field '{field}' must be a YAML list of strings; received {type(value).__name__}.", f"Use '{field}: []' or a list of registered values.", field, line))
                continue
            values = list(enumerate(value, start=1))
        else:
            values = [(None, value)]
        for index, item in values:
            position = f" (item {index})" if index is not None else ""
            if not isinstance(item, str) or not item.strip():
                problems.append(Problem(f"Field '{field}'{position} must contain a nonempty string; received {item!r}.", values_hint(allowed, field), field, line))
            elif item not in allowed:
                matches = difflib.get_close_matches(item, sorted(allowed), n=1)
                hint = values_hint(allowed, field)
                if matches:
                    hint = f"Did you mean '{matches[0]}'? " + hint
                problems.append(Problem(f"Unknown value {item!r} in field '{field}'{position}.", hint, field, line))
    return problems


def report_path(argument):
    requested = Path(argument)
    if not requested.is_absolute() and len(requested.parts) == 1:
        requested = ROOT / ".flow" / requested
    destination = requested.resolve()
    flow = (ROOT / ".flow").resolve()
    try:
        destination.relative_to(flow)
    except ValueError:
        raise ValueError(f"The output error file must be inside {flow}") from None
    if destination.suffix.lower() != ".md":
        raise ValueError("The output error file must have a .md extension")
    return destination


def write_report(destination, page, problems):
    def escape(value):
        value = str(value).replace("\\", "\\\\").replace("\r", " ").replace("\n", " ").replace("<", "&lt;")
        for character in (chr(96), "*", "_", "[", "#"):
            value = value.replace(character, "\\" + character)
        return value

    lines = ["# Wiki YAML header validation failed", "", f"**Wiki file:** {escape(page)}", "", f"**Problems found:** {len(problems)}", "", "Validation rules: data/schemas.yaml and data/tags.yaml.", ""]
    for number, problem in enumerate(problems, start=1):
        lines += [f"## Problem {number}", "", escape(problem.message), ""]
        if problem.field is not None:
            lines += [f"**Field:** {escape(problem.field)}", ""]
        if problem.line is not None:
            lines += [f"**Line in wiki file:** {problem.line}", ""]
        lines += [f"**How to fix:** {escape(problem.fix)}", ""]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("wiki_markdown", type=Path, help="Path to the wiki Markdown file")
    parser.add_argument("output_error_file", help="Markdown report path inside .flow, or a bare filename")
    args = parser.parse_args(argv)
    page = args.wiki_markdown.resolve()
    try:
        destination = report_path(args.output_error_file)
        if destination == page:
            raise ValueError("The output error file must differ from the wiki Markdown file")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    status = 1
    if yaml is None:
        status = 2
        problems = [Problem("The PyYAML dependency is not installed.", "Run 'uv pip install -r requirements.txt' from the project directory and retry.")]
    else:
        try:
            required, optional, vocabularies = load_configuration()
        except yaml.YAMLError as error:
            status = 2
            problems = [yaml_problem(error, f"Configuration file {error.configuration_path}", offset=None)]
        except (OSError, UnicodeError, ValueError) as error:
            status = 2
            problems = [Problem(f"Cannot load the validation configuration: {error}.", "Correct data/schemas.yaml or data/tags.yaml and retry.")]
        else:
            header, locations, problems = read_header(page)
            if not problems:
                problems = validate_header(header, locations, required, optional, vocabularies)
    try:
        if problems:
            write_report(destination, page, problems)
        else:
            destination.unlink(missing_ok=True)
    except (OSError, UnicodeError) as error:
        print(f"Error: Cannot update the validation report at {destination}: {error}", file=sys.stderr)
        return 2
    if problems:
        print(f"Validation failed: {len(problems)} problem(s). Report: {destination}", file=sys.stderr)
        return status
    print(f"Validation passed: {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
