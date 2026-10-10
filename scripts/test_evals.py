import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    from scripts import evals
except ImportError:  # Direct execution: python3 scripts/test_evals.py
    import evals


class EvalReporterTests(unittest.TestCase):
    CASES = [
        {
            "id": "answer",
            "prompt": "Give a useful answer.",
            "criteria": ["The answer addresses the request."],
        }
    ]
    SKILL = b"---\nname: example\ndescription: An example skill.\n---\n\nDo the work.\n"
    COMPANION = b"Companion instructions.\n"

    def comparison(
        self,
        *,
        base_score=90,
        current_score=80,
        aggregate=None,
        suite_hash=None,
        base_hash=None,
        current_hash=None,
    ):
        return {
            "suite_hash": suite_hash or evals.canonical_cases_hash(self.CASES),
            "environment": {"agent": "test-agent", "model": "test-model"},
            "base": {
                "skill_hash": base_hash or "sha256:" + "1" * 64,
                "score": base_score,
            },
            "current": {
                "skill_hash": current_hash
                or evals.skill_hash(
                    [(b"SKILL.md", self.SKILL), (b"guide.txt", self.COMPANION)]
                ),
                "score": current_score if aggregate is None else aggregate,
            },
            "cases": [
                {
                    "id": "answer",
                    "base": base_score,
                    "current": current_score,
                    "rationale": "The current answer remains useful.",
                }
            ],
            "confirmed_by": "tester",
            "confirmed_at": "2026-10-10T12:00:00Z",
        }

    def make_repo(self, root, comparison):
        skill_dir = root / "skills" / "example"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_bytes(self.SKILL)
        (skill_dir / "guide.txt").write_bytes(self.COMPANION)
        (root / "README.md").write_text(
            "# Test\n\n## Skills\n\n"
            "| Skill | Purpose |\n"
            "| --- | --- |\n"
            "| `example` | An example skill. |\n",
            encoding="utf-8",
        )
        eval_dir = root / "evals"
        eval_dir.mkdir()
        (eval_dir / "example.json").write_text(
            json.dumps(
                {"skill": "example", "cases": self.CASES, "comparison": comparison},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def test_canonical_hashes(self):
        cases = [{"prompt": "Café", "criteria": ["Clear"], "id": "one"}]
        canonical = '[{"criteria":["Clear"],"id":"one","prompt":"Café"}]'.encode()
        self.assertEqual(
            evals.canonical_cases_hash(cases),
            "sha256:" + hashlib.sha256(canonical).hexdigest(),
        )
        files = [(b"z.txt", b"last"), (b"a/one.txt", b"\x00first")]
        framed = b"".join(
            len(path).to_bytes(8, "big")
            + path
            + len(content).to_bytes(8, "big")
            + content
            for path, content in sorted(files)
        )
        expected = "sha256:" + hashlib.sha256(framed).hexdigest()
        self.assertEqual(evals.skill_hash(files), expected)
        self.assertEqual(evals.skill_hash(list(reversed(files))), expected)
        self.assertNotEqual(
            evals.skill_hash(files),
            evals.skill_hash([(b"z.txt", b"last"), (b"a/two.txt", b"\x00first")]),
        )
        self.assertNotEqual(
            evals.skill_hash(files),
            evals.skill_hash([(b"z.txt", b"last"), (b"a/one.txt", b"\x00changed")]),
        )

    def test_frontmatter_rejects_unquoted_non_string_scalars(self):
        invalid = ("null", "~", "false", "42", "-1.5e2", "[example]", "{name: example}")
        for key in ("name", "description"):
            for scalar in invalid:
                with self.subTest(key=key, scalar=scalar):
                    values = {
                        "name": "example",
                        "description": "An example skill.",
                    }
                    values[key] = scalar
                    errors = []
                    metadata = evals._frontmatter(
                        (
                            f"---\nname: {values['name']}\n"
                            f"description: {values['description']}\n---\n"
                        ).encode(),
                        "SKILL.md",
                        errors,
                    )
                    self.assertIsNone(metadata)
                    self.assertTrue(errors)

        for quoted in ('"null"', "'false'", '"42"', "'[example]'"):
            with self.subTest(quoted=quoted):
                errors = []
                metadata = evals._frontmatter(
                    f"---\nname: {quoted}\ndescription: valid\n---\n".encode(),
                    "SKILL.md",
                    errors,
                )
                self.assertIsNotNone(metadata)
                self.assertFalse(errors)

    def test_invalid_aggregate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root, self.comparison(aggregate=81))
            result = evals.audit(root)
        self.assertTrue(any("aggregate must be 80" in error for error in result.errors))

    def test_missing_and_stale_comparisons_warn(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root, None)
            missing = evals.audit(root)
        self.assertFalse(missing.errors)
        self.assertTrue(any("comparison is missing" in warning for warning in missing.warnings))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(
                root,
                self.comparison(suite_hash="sha256:" + "0" * 64),
            )
            stale = evals.audit(root)
        self.assertFalse(stale.errors)
        self.assertTrue(any("comparison is stale" in warning for warning in stale.warnings))

    def test_regression_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root, self.comparison(base_score=90, current_score=80))
            result = evals.audit(root)
            report = evals.render_report(result)
        self.assertFalse(result.errors)
        self.assertIn("90 → 80 (-10)", report)
        self.assertTrue(any("regression" in warning for warning in result.warnings))

    @unittest.skipUnless(shutil.which("git"), "git is required")
    def test_git_base_finds_moved_skill_and_companion_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_repo(root, None)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-qm",
                    "base",
                ],
                cwd=root,
                check=True,
            )
            base = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            base_hash = evals.skill_hash(
                [(b"SKILL.md", self.SKILL), (b"guide.txt", self.COMPANION)]
            )

            old_directory = root / "skills" / "example"
            new_directory = root / "skills" / "moved"
            old_directory.rename(new_directory)
            changed_companion = b"Changed companion instructions.\n"
            (new_directory / "guide.txt").write_bytes(changed_companion)
            current_hash = evals.skill_hash(
                [(b"SKILL.md", self.SKILL), (b"guide.txt", changed_companion)]
            )
            (root / "evals" / "example.json").write_text(
                json.dumps(
                    {
                        "skill": "example",
                        "cases": self.CASES,
                        "comparison": self.comparison(
                            base_hash=base_hash,
                            current_hash=current_hash,
                        ),
                    }
                ),
                encoding="utf-8",
            )

            result = evals.audit(root, base)

        self.assertFalse(result.errors)
        self.assertEqual(result.rows, [("example", "90 → 80 (-10)")])


if __name__ == "__main__":
    unittest.main()
