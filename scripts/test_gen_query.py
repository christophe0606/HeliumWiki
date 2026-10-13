#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["PyYAML>=6.0"]
# ///
"""Run from the repository root: uv run scripts/test_gen_query.py."""

import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote

import gen_query


class GenQueryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo_root = Path(self.temporary.name) / "repo"
        self.root = self.repo_root / "helium-wiki"
        for folder in ("hardware", "languages", "patterns", "techniques"):
            (self.root / "wiki" / folder).mkdir(parents=True)
        (self.repo_root / "data").mkdir()
        (self.repo_root / "data" / "tags.yaml").write_text(
            "hardware_features: [mve, cache]\n", encoding="utf-8"
        )
        self.hardware = self.page("hardware/mve.md", "hardware-mve", "MVE", features=["mve"], tags=["mve"])
        self.technique = self.page("techniques/fuse.md", "techniques-fuse", "Fuse operations",
            tags=["mve", "optimization"], architectures=["armv8.1-m", "cortex-m55"],
            confidence="source-reported", reproducibility="snippet")
        self.language = self.page("languages/c.md", "languages-c", "C language", hardware_features=["mve"])

    def page(self, path, page_id, title, **fields):
        file = self.root / "wiki" / path
        file.parent.mkdir(parents=True, exist_ok=True)
        header = {"id": page_id, "title": title, **fields}
        file.write_text("---\n" + gen_query.yaml.safe_dump(header, sort_keys=False) + "---\n\nBody.\n", encoding="utf-8")
        return file

    def output(self, folder):
        return (self.root / "queries" / f"by-{folder}.md").read_text(encoding="utf-8")

    def run_main(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(gen_query, "REPO_ROOT", self.repo_root), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = gen_query.main([])
        return result, stdout.getvalue(), stderr.getvalue()

    def test_every_immediate_folder_gets_an_index_including_empty_folders(self):
        outputs = gen_query.generate(self.repo_root)
        self.assertEqual([file.name for file in outputs],
            ["by-hardware.md", "by-languages.md", "by-patterns.md", "by-techniques.md"])
        self.assertIn("| Page ID | Related information |", self.output("patterns"))
        self.assertIn("No matching pages yet.", self.output("patterns"))

    def test_technique_indexes_start_with_a_link_and_include_metadata_columns(self):
        gen_query.generate(self.repo_root)
        self.assertIn("| Technique | Tags | Architecture | Confidence | Reproducibility |", self.output("techniques"))
        self.assertIn("| [Fuse operations](../wiki/techniques/fuse.md) | mve, optimization | "
            "armv8.1-m, cortex-m55 | source-reported | snippet |", self.output("techniques"))
        self.assertNotIn("| techniques-fuse |", self.output("techniques"))
        self.assertNotIn("C language", self.output("techniques"))

    def test_language_indexes_use_canonical_language_names(self):
        self.page("techniques/assembly.md", "techniques-assembly", "Assembly technique", language="assembly")
        self.page("techniques/cpp.md", "techniques-cpp", "C++ technique", languages=["C++"])
        self.page("patterns/c.md", "patterns-c", "C pattern", tags=["C"])
        gen_query.generate(self.repo_root)
        output = self.output("languages")
        self.assertIn("| Language | Related information |", output)
        self.assertIn("| asm | [Assembly technique](../wiki/techniques/assembly.md) |", output)
        self.assertIn("| c | [C language](../wiki/languages/c.md)<br>[C pattern](../wiki/patterns/c.md) |", output)
        self.assertIn("| cpp | [C++ technique](../wiki/techniques/cpp.md) |", output)
        self.assertNotIn("| languages-c |", output)

    def test_language_page_id_prefixes_and_related_pages_are_grouped(self):
        self.page("languages/float16.md", "languages-c-float16", "C Float16", related=["techniques-fuse"])
        self.page("techniques/related.md", "techniques-related", "Related C technique", related=["languages-c"])
        gen_query.generate(self.repo_root)
        output = self.output("languages")
        c_row = next(line for line in output.splitlines() if line.startswith("| c |"))
        self.assertIn("[C Float16](../wiki/languages/float16.md)", c_row)
        self.assertIn("[Fuse operations](../wiki/techniques/fuse.md)", c_row)
        self.assertIn("[Related C technique](../wiki/techniques/related.md)", c_row)
        self.assertEqual(c_row.count("[C language]"), 1)
        self.assertIn("| asm | — |", output)
        self.assertIn("| cpp | — |", output)

    def test_technique_rows_handle_optional_metadata_and_singular_architecture(self):
        self.page("techniques/minimal.md", "techniques-minimal", "Minimal", architecture="cortex-m85")
        gen_query.generate(self.repo_root)
        self.assertIn("| [Minimal](../wiki/techniques/minimal.md) | — | cortex-m85 | — | — |", self.output("techniques"))

    def test_other_folder_indexes_keep_page_ids_and_linked_titles(self):
        self.page("patterns/pattern.md", "patterns-memory", "Memory pattern")
        gen_query.generate(self.repo_root)
        self.assertIn("| patterns-memory | [Memory pattern](../wiki/patterns/pattern.md) |", self.output("patterns"))

    def test_hardware_features_group_pages_across_folders_and_deduplicate(self):
        gen_query.generate(self.repo_root)
        output = self.output("hardware")
        self.assertIn("| Hardware feature | Related information |", output)
        self.assertIn("| mve | [C language](../wiki/languages/c.md)<br>"
            "[Fuse operations](../wiki/techniques/fuse.md)<br>[MVE](../wiki/hardware/mve.md) |", output)
        self.assertEqual(output.count("[MVE]"), 1)
        self.assertNotIn("| optimization |", output)

    def test_related_hardware_ids_work_in_both_directions(self):
        self.page("hardware/cache.md", "hardware-cache", "Cache", related=["techniques-cache"])
        self.page("techniques/cache.md", "techniques-cache", "Enable cache")
        self.page("techniques/prefetch.md", "techniques-prefetch", "Prefetch", related=["hardware-cache"])
        gen_query.generate(self.repo_root)
        cache_row = next(line for line in self.output("hardware").splitlines() if line.startswith("| cache |"))
        self.assertIn("[Cache](../wiki/hardware/cache.md)", cache_row)
        self.assertIn("[Enable cache](../wiki/techniques/cache.md)", cache_row)
        self.assertIn("[Prefetch](../wiki/techniques/prefetch.md)", cache_row)

    def test_feature_fields_support_scalar_values_and_case_insensitive_grouping(self):
        self.page("techniques/second.md", "techniques-second", "Second", hardware_feature="MVE")
        gen_query.generate(self.repo_root)
        output = self.output("hardware")
        self.assertIn("[Second](../wiki/techniques/second.md)", output)
        self.assertEqual(output.count("| mve |"), 1)
        self.assertNotIn("| MVE |", output)

    def test_new_folders_and_nested_pages_are_discovered_automatically(self):
        self.page("kernels/attention/nested.md", "kernel-attention", "Attention")
        gen_query.generate(self.repo_root)
        self.assertIn("| kernel-attention | [Attention](../wiki/kernels/attention/nested.md) |", self.output("kernels"))
        self.assertFalse((self.root / "queries" / "by-attention.md").exists())

    def test_headerless_indexes_are_ignored_and_only_headers_are_read(self):
        (self.root / "wiki" / "techniques" / "README.md").write_text("# Concepts\n", encoding="utf-8")
        with self.technique.open("ab") as stream:
            stream.write(b"\xff invalid UTF-8 body, not metadata")
        gen_query.generate(self.repo_root)
        self.assertIn("[Fuse operations](../wiki/techniques/fuse.md)", self.output("techniques"))
        self.assertNotIn("README", self.output("techniques"))

    def test_markdown_escaping_and_encoded_links_resolve_to_real_pages(self):
        self.page("techniques/a [b] (#1).md", "techniques-pipe|id", "A [B] | C <D>\nnext", tags=["tag|name"])
        gen_query.generate(self.repo_root)
        output = self.output("techniques")
        self.assertIn(r"tag\|name", output)
        self.assertIn(r"[A \[B\] \| C &lt;D&gt; next]", output)
        self.assertIn("a%20%5Bb%5D%20%28%231%29.md", output)
        for file in (self.root / "queries").glob("by-*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
                self.assertTrue((file.parent / unquote(target)).resolve().is_file(), target)

    def test_refresh_is_deterministic_and_preserves_unrelated_files(self):
        gen_query.generate(self.repo_root)
        generated = self.root / "queries" / "by-techniques.md"
        before, stamp = generated.read_bytes(), generated.stat().st_mtime_ns
        unrelated = self.root / "queries" / "notes.md"
        unrelated.write_text("Keep this.\n", encoding="utf-8")
        gen_query.generate(self.repo_root)
        self.assertEqual(generated.read_bytes(), before)
        self.assertEqual(generated.stat().st_mtime_ns, stamp)
        self.page("techniques/new.md", "techniques-new", "New technique")
        gen_query.generate(self.repo_root)
        self.assertIn("New technique", self.output("techniques"))
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "Keep this.\n")

    def test_invalid_metadata_does_not_replace_existing_indexes(self):
        gen_query.generate(self.repo_root)
        old = {file: file.read_bytes() for file in (self.root / "queries").glob("by-*.md")}
        (self.root / "wiki" / "techniques" / "bad.md").write_text("---\nid: [broken\n---\n", encoding="utf-8")
        result, _, errors = self.run_main()
        self.assertEqual(result, 2)
        self.assertIn("techniques/bad.md", errors)
        self.assertEqual({file: file.read_bytes() for file in old}, old)

    def test_missing_ids_duplicate_ids_and_invalid_feature_lists_are_rejected(self):
        bad = self.root / "wiki" / "techniques" / "bad.md"
        for header in ({"title": "Missing ID"}, {"id": "hardware-mve", "title": "Duplicate"},
                       {"id": "bad", "title": "Bad features", "hardware_features": [42]}):
            with self.subTest(header=header):
                bad.write_text("---\n" + gen_query.yaml.safe_dump(header) + "---\n", encoding="utf-8")
                with self.assertRaises(ValueError):
                    gen_query.generate(self.repo_root)
                self.assertFalse((self.root / "queries").exists())

    def test_explicit_features_and_hardware_ids_work_without_a_vocabulary_file(self):
        (self.repo_root / "data" / "tags.yaml").unlink()
        self.page("hardware/cache.md", "hardware-cache", "Cache")
        gen_query.generate(self.repo_root)
        output = self.output("hardware")
        self.assertIn("| cache | [Cache](../wiki/hardware/cache.md) |", output)
        self.assertIn("[C language]", output)

    def test_hardware_tags_can_generate_rows_even_when_hardware_folder_is_empty(self):
        self.hardware.unlink()
        gen_query.generate(self.repo_root)
        output = self.output("hardware")
        self.assertIn("| mve |", output)
        self.assertIn("[Fuse operations]", output)
        self.assertNotIn("[MVE]", output)

    def test_local_generation_outputs_paths_without_network_access(self):
        self.page("patterns/url.md", "patterns-url", "Local page", sources=["https://example.test/source"])
        with patch("socket.create_connection", side_effect=AssertionError("Network access")) as create, patch(
            "socket.socket.connect", side_effect=AssertionError("Network access")
        ) as connect:
            result, output, errors = self.run_main()
        self.assertEqual(result, 0)
        self.assertEqual(errors, "")
        self.assertIn("queries/by-techniques.md", output)
        create.assert_not_called()
        connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
