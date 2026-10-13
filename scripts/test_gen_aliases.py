#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML>=6.0"]
# ///
"""Run from the repository root: uv run scripts/test_gen_aliases.py."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gen_aliases

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "helium-wiki" / "scripts"))
import query


class GenAliasesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo_root = Path(self.temporary.name) / "repo"
        self.wiki = self.repo_root / "helium-wiki" / "wiki"
        (self.wiki / "techniques").mkdir(parents=True)
        self.output = self.repo_root / "helium-wiki" / "data" / "aliases.yaml"

    def page(self, filename, page_id, aliases=None, **fields):
        file = self.wiki / "techniques" / filename
        header = {"id": page_id, "title": page_id.title(), **fields}
        if aliases is not None:
            header["aliases"] = aliases
        file.write_text("---\n" + gen_aliases.yaml.safe_dump(header, sort_keys=False) + "---\nBody.\n", encoding="utf-8")
        return file

    def data(self):
        return gen_aliases.yaml.safe_load(self.output.read_text(encoding="utf-8"))

    def test_generated_file_maps_yaml_page_ids_to_their_aliases(self):
        self.page("different-filename.md", "techniques-vector", ["Vector code", "SIMD optimization"])
        self.page("no-aliases.md", "techniques-empty")
        self.assertEqual(gen_aliases.generate(self.repo_root), self.output)
        self.assertEqual(self.data(), {
            "techniques-empty": [], "techniques-vector": ["SIMD optimization", "Vector code"],
        })

    def test_aliases_are_sorted_trimmed_and_deduplicated_case_insensitively(self):
        self.page("example.md", "page-one", ["zebra", " Beta ", "beta", "PAGE-ONE", "éclair", "Alpha"])
        gen_aliases.generate(self.repo_root)
        self.assertEqual(self.data()["page-one"], ["Alpha", "Beta", "zebra", "éclair"])

    def test_generated_aliases_are_consumed_by_the_installed_query_script(self):
        self.page("first.md", "first", ["Shared nickname", "UniqueOne"])
        self.page("second.md", "second", ["Shared nickname", "UniqueTwo"])
        gen_aliases.generate(self.repo_root)
        aliases = query.load_aliases(self.output)
        pages = [query.Page(self.wiki / "techniques" / f"{name}.md", {"id": name, "title": name}) for name in ("first", "second")]
        results = query.search_pages(pages, "UniqueOne", {}, aliases)
        self.assertEqual([result.page.id for result in results], ["first"])
        results = query.search_pages(pages, "Shared nickname", {}, aliases)
        self.assertEqual({result.page.id for result in results}, {"first", "second"})

    def test_regeneration_removes_deleted_pages_aliases_and_manual_entries(self):
        first = self.page("first.md", "first", ["Old alias"])
        self.page("second.md", "second", ["Keep"])
        gen_aliases.generate(self.repo_root)
        self.output.write_text(self.output.read_text(encoding="utf-8") + "manual: [Invented]\n", encoding="utf-8")
        first.unlink()
        self.page("second.md", "second", ["Updated"])
        gen_aliases.generate(self.repo_root)
        self.assertEqual(self.data(), {"second": ["Updated"]})

    def test_unchanged_generation_is_deterministic_and_does_not_rewrite(self):
        self.page("example.md", "example", ["Alias"])
        gen_aliases.generate(self.repo_root)
        content, timestamp = self.output.read_bytes(), self.output.stat().st_mtime_ns
        gen_aliases.generate(self.repo_root)
        self.assertEqual(self.output.read_bytes(), content)
        self.assertEqual(self.output.stat().st_mtime_ns, timestamp)

    def test_invalid_aliases_leave_existing_output_untouched(self):
        self.page("good.md", "good", ["Good alias"])
        gen_aliases.generate(self.repo_root)
        old = self.output.read_bytes()
        for aliases in ([42], [""], {"bad": "shape"}):
            with self.subTest(aliases=aliases):
                self.page("bad.md", "bad", aliases)
                with self.assertRaisesRegex(ValueError, "aliases"):
                    gen_aliases.generate(self.repo_root)
                self.assertEqual(self.output.read_bytes(), old)

    def test_duplicate_ids_and_malformed_headers_are_rejected(self):
        self.page("first.md", "first", ["Alias"])
        self.page("second.md", "first", ["Duplicate"])
        with self.assertRaisesRegex(ValueError, "duplicate page id"):
            gen_aliases.generate(self.repo_root)
        (self.wiki / "techniques" / "second.md").write_text("---\nid: [broken\n---\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            gen_aliases.generate(self.repo_root)
        self.assertFalse(self.output.exists())

    def test_headerless_docs_and_body_contents_do_not_affect_aliases(self):
        (self.wiki / "techniques" / "README.md").write_text("# Index\n", encoding="utf-8")
        file = self.page("example.md", "example", ["Alias"])
        with file.open("ab") as stream:
            stream.write(b"\xff aliases: [not-header-data]\n")
        gen_aliases.generate(self.repo_root)
        self.assertEqual(self.data(), {"example": ["Alias"]})

    def test_empty_wiki_generates_an_empty_map_accepted_by_query(self):
        gen_aliases.generate(self.repo_root)
        self.assertEqual(self.data(), {})
        self.assertEqual(query.load_aliases(self.output).page_aliases, {})

    def test_local_generation_reports_its_output_path_without_network_access(self):
        self.page("example.md", "example", ["Alias"], sources=["https://example.test/source"])
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(gen_aliases, "REPO_ROOT", self.repo_root), patch(
            "socket.create_connection", side_effect=AssertionError("Network access")
        ) as create, patch("socket.socket.connect", side_effect=AssertionError("Network access")) as connect, contextlib.redirect_stdout(
            stdout
        ), contextlib.redirect_stderr(stderr):
            result = gen_aliases.main([])
        self.assertEqual(result, 0)
        self.assertEqual(stdout.getvalue(), "helium-wiki/data/aliases.yaml\n")
        self.assertEqual(stderr.getvalue(), "")
        create.assert_not_called()
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
