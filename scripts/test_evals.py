import json
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    from scripts import evals
except ImportError:  # Direct execution: python3 scripts/test_evals.py
    import evals


def skill_md(body, name="example"):
    return f"---\nname: {name}\ndescription: An example skill.\n---\n\n{body}\n"


CASE = {
    "id": "answer",
    "prompt": "Give a useful answer.",
    "tests": "Answers usefully.",
    "traps": [],
    "expectations": ["Addresses the request.", "Stays short."],
}
OTHER_ROW = "| `other` | Another skill. |\n"


class FakeOmp:
    """Answers with the skill body it finds; judges by a per-body verdict table."""

    def __init__(self, verdicts, judge_text=None):
        self.verdicts = verdicts  # skill body -> list of pass booleans
        self.judge_text = judge_text
        self.calls = 0

    def __call__(self, prompt, cwd, system, tools, log):
        self.calls += 1
        if tools:
            body = (cwd / "SKILL.md").read_text().split("---\n")[-1].strip()
            return f"ANSWER[{body}]", "fake/model"
        if self.judge_text is not None:
            return self.judge_text, "fake/model"
        body = prompt.split("ANSWER[", 1)[1].split("]", 1)[0]
        return json.dumps(
            [{"n": n, "pass": ok, "reason": f"{body} #{n}"} for n, ok in enumerate(self.verdicts[body], 1)]
        ), "fake/model"


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.write(skill_md("v1"), [CASE])
        self.git("init", "-q", "-b", "master")
        self.git("add", ".")
        self.commit("base")

    def tearDown(self):
        self.directory.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def commit(self, message):
        self.git("-c", "user.name=T", "-c", "user.email=t@example.com", "commit", "-qm", message)

    def write(self, skill, cases, readme_extra=""):
        (self.root / "skills" / "example").mkdir(parents=True, exist_ok=True)
        (self.root / "skills" / "example" / "SKILL.md").write_text(skill)
        (self.root / "evals").mkdir(exist_ok=True)
        (self.root / "evals" / "example.json").write_text(
            json.dumps({"skill": "example", "cases": cases})
        )
        (self.root / "README.md").write_text(
            "## Skills\n\n| Skill | Purpose |\n| --- | --- |\n"
            f"| `example` | An example skill. |\n{readme_extra}"
        )

    def stage(self, skill=skill_md("v1"), cases=(CASE,), readme_extra=""):
        self.write(skill, list(cases), readme_extra)
        self.git("add", ".")

    def commit_other_skill(self):
        """Add a second skill, `other`, to master."""
        (self.root / "skills" / "other").mkdir()
        (self.root / "skills" / "other" / "SKILL.md").write_text(skill_md("o1", name="other"))
        (self.root / "evals" / "other.json").write_text(
            json.dumps({"skill": "other", "cases": [CASE]})
        )
        self.stage(readme_extra=OTHER_ROW)
        self.commit("other")

    def test_score_drop_blocks_and_lists_changed_results(self):
        self.stage(skill_md("v2"))
        fake = FakeOmp({"v1": [True, True], "v2": [True, False]})
        report, blocked = evals.check(self.root, runner=fake)
        self.assertTrue(blocked)
        self.assertIn("master 2/2 → staged 1/2", report)
        self.assertIn("- answer #2 (pass → fail): Stays short.\n  Staged judge: v2 #2", report)
        self.assertIn("Model: fake/model", report)

    def test_equal_or_better_score_passes(self):
        for staged in ([True, True], [False, True]):
            with self.subTest(staged=staged):
                self.stage(skill_md("v2"))
                report, blocked = evals.check(
                    self.root, runner=FakeOmp({"v1": [False, True], "v2": staged})
                )
                self.assertFalse(blocked, report)

    def test_case_edit_alone_blocks_without_runs(self):
        changed = dict(CASE, expectations=["Addresses the request.", "Cites a source."])
        added = dict(CASE, id="extra")
        self.stage(cases=[changed, added])
        fake = FakeOmp({})
        report, blocked = evals.check(self.root, runner=fake)
        self.assertTrue(blocked)
        self.assertIn("- answer: expectations changed", report)
        self.assertIn("- extra: added", report)
        self.assertEqual(fake.calls, 0)

    def test_review_note_edit_passes_without_runs(self):
        self.stage(cases=[dict(CASE, tests="Reworded.", traps=["New trap note."])])
        fake = FakeOmp({})
        report, blocked = evals.check(self.root, runner=fake)
        self.assertFalse(blocked, report)
        self.assertEqual(fake.calls, 0)
        self.assertIn("no runs", report)

    def test_change_outside_skills_and_evals_skips_model_runs(self):
        self.stage(readme_extra="\nMore text.\n")
        fake = FakeOmp({})
        report, blocked = evals.check(self.root, runner=fake)
        self.assertFalse(blocked, report)
        self.assertEqual(fake.calls, 0)

    def test_only_the_changed_skill_runs(self):
        self.commit_other_skill()
        self.stage(skill_md("v2"), readme_extra=OTHER_ROW)
        fake = FakeOmp({"v1": [True, True], "v2": [True, True]})
        report, blocked = evals.check(self.root, runner=fake)
        self.assertFalse(blocked, report)
        self.assertEqual(fake.calls, 4)  # example's one case x 2 versions x (run + judge)
        self.assertNotIn("## other", report)

    def test_removing_a_skill_blocks_without_runs(self):
        self.commit_other_skill()
        self.git("rm", "-rq", "skills/other", "evals/other.json")
        self.stage()
        fake = FakeOmp({})
        report, blocked = evals.check(self.root, runner=fake)
        self.assertTrue(blocked, report)
        self.assertIn("- answer: removed", report)
        self.assertEqual(fake.calls, 0)

    def test_unparseable_judge_output_is_a_failed_run(self):
        self.stage(skill_md("v2"))
        for text in ("All good!", '[{"n": 1, "pass": true, "reason": "ok"}]'):
            with self.subTest(text=text):
                report, blocked = evals.check(self.root, runner=FakeOmp({}, judge_text=text))
                self.assertTrue(blocked)
                self.assertIn("Failures:", report)
                self.assertIn("a run or judgment failed", report)

    def test_new_skill_reports_staged_score_alone(self):
        self.git("rm", "-rq", "--cached", "skills", "evals")
        self.commit("empty")
        self.stage()
        report, _ = evals.check(self.root, runner=FakeOmp({"v1": [True, False]}))
        self.assertIn("Score: staged 1/2 (master has no example)", report)


class IsolationTests(unittest.TestCase):
    def test_reads_must_stay_inside_the_run_directory(self):
        cwd = Path("/tmp/run")
        for path in ("SKILL.md", "sub/a.md:5-9", "/tmp/run/SKILL.md", "*.md"):
            self.assertTrue(evals._path_inside(path, cwd), path)
        for path in ("../staged/SKILL.md", "/tmp/other", "~/.agents/skills", "skill://x", "a.md;/etc"):
            self.assertFalse(evals._path_inside(path, cwd), path)


class FrontmatterTests(unittest.TestCase):
    def test_rejects_unquoted_non_string_scalars(self):
        for scalar in ("null", "~", "false", "42", "-1.5e2", "[example]", "{name: example}"):
            with self.subTest(scalar=scalar):
                errors = []
                content = f"---\nname: {scalar}\ndescription: valid\n---\n".encode()
                self.assertIsNone(evals._frontmatter(content, "SKILL.md", errors))
                self.assertTrue(errors)
        for quoted in ('"null"', "'false'", '"42"', "'[example]'"):
            with self.subTest(quoted=quoted):
                errors = []
                content = f"---\nname: {quoted}\ndescription: valid\n---\n".encode()
                self.assertIsNotNone(evals._frontmatter(content, "SKILL.md", errors))
                self.assertFalse(errors)


if __name__ == "__main__":
    unittest.main()
