#!/usr/bin/env python3
"""Check skill evals before a commit.

Usage: scripts/evals.py [SKILL ...]

After the structure checks, checks each skill whose folder or eval file is staged, or
each named skill. Only a skill whose folder is staged (or named) and differs from master
gets model runs: every staged case is answered once by its master version and once by
its staged version on this machine's default omp model, and an LLM judge marks each
expectation. Blocks (exits 1) on a structure error, a failed run or judgment, a lower
staged score, or a case prompt or expectation that was added, changed or removed,
including by removing a skill.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable

MASTER_REF = "master"
FRONTMATTER_KEYS = ("name", "description")
ROOT_KEYS = ("skill", "cases")
CASE_KEYS = ("id", "prompt", "tests", "traps", "expectations")
CONCURRENCY = 8
TIMEOUT = 1200  # seconds per omp session

# Keeps memory, context files, MCP servers and user/project config sources out of runs,
# and stops omp from silently retrying on another model.
OMP_OVERLAY = """\
memory:
  backend: "off"
retry:
  modelFallback: false
disabledProviders: [native, claude, codex, gemini, opencode, github, agents, agents-md, claude-md, custom-context]
"""
OMP_FLAGS = (
    "-p", "--mode", "json", "--no-session", "--no-skills", "--no-rules",
    "--no-extensions", "--no-lsp", "--no-title",
)
# The last sentence stops sessions that look up the user's files from answering for an empty project.
RUN_SYSTEM = (
    "Your working directory is a copy of the `{name}` skill. Read SKILL.md first and "
    "follow it to handle the user's request, reading the companion files it points to. "
    "Read only files inside the working directory. It holds only the skill: answer as you "
    "would in the user's own session, where the project, files and earlier conversation "
    "the request mentions exist as described."
)
JUDGE_PROMPT = """\
Grade the answer below against each numbered expectation. An expectation passes only \
when the answer observably meets it.

Reply with only a JSON array holding one object per expectation, in order: \
{"n": <expectation number>, "pass": true or false, "reason": "<one line>"}.

<request>
%s
</request>

<expectations>
%s
</expectations>

<answer>
%s
</answer>
"""


class CheckError(Exception):
    """A run, judgment or git step that failed."""


# runner(prompt, cwd, system, tools, log) -> (final answer text, model label)
Runner = Callable[[str, Path, "str | None", bool, Path], "tuple[str, str]"]
Case = dict[str, Any]  # one entry of an eval file's "cases"


@dataclass(frozen=True)
class Skill:
    """One version of a skill. A version the skill is missing from has no files or cases."""

    name: str
    folder: str  # repository-relative, e.g. skills/productivity/zoom-out
    files: tuple[tuple[bytes, bytes], ...]
    cases: tuple[Case, ...] = ()


# ---------------------------------------------------------------- structure checks


def _label(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _yaml_scalar(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    if raw.startswith('"'):
        try:
            value, end = json.JSONDecoder().raw_decode(raw)
        except json.JSONDecodeError:
            return None
        remainder = raw[end:].strip()
        return value if isinstance(value, str) and (not remainder or remainder.startswith("#")) else None
    if raw.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", raw)
        return match.group(1).replace("''", "'") if match else None
    value = re.split(r"\s+#", raw, maxsplit=1)[0].rstrip()
    lowered = value.lower().lstrip("+-")
    if (
        not value
        or value[0] in "[{"
        or lowered in {"null", "~", "true", "false", "yes", "no", "on", "off", ".inf", ".nan"}
        or re.fullmatch(
            r"[+-]?(?:0b[01_]+|0o[0-7_]+|0x[0-9a-f_]+|"
            r"(?:[0-9][0-9_]*)(?:\.[0-9_]*)?(?:e[+-]?[0-9_]+)?|"
            r"\.[0-9_]+(?:e[+-]?[0-9_]+)?|"
            r"[0-9]+(?::[0-5]?[0-9])+(?:\.[0-9_]+)?)",
            value,
            re.IGNORECASE,
        )
    ):
        return None
    return value


def _frontmatter(content: bytes, label: str, errors: list[str]) -> dict[str, str] | None:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        errors.append(f"{label}: SKILL.md is not UTF-8 ({exc})")
        return None
    if not lines or lines[0].strip() != "---":
        errors.append(f"{label}: missing opening frontmatter delimiter")
        return None
    try:
        end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        errors.append(f"{label}: missing closing frontmatter delimiter")
        return None

    values: dict[str, str] = {}
    body = lines[1:end]
    i = 0
    while i < len(body):
        line = body[i]
        if line and not line[0].isspace() and ":" in line:
            key, raw = line.split(":", 1)
            if key in FRONTMATTER_KEYS:
                if key in values:
                    errors.append(f"{label}: duplicate frontmatter key {key!r}")
                marker = raw.strip()
                if marker in {">", ">-", ">+", "|", "|-", "|+"}:
                    block: list[str] = []
                    i += 1
                    while i < len(body) and (not body[i] or body[i][0].isspace()):
                        if body[i].strip():
                            block.append(body[i].strip())
                        i += 1
                    separator = " " if marker.startswith(">") else "\n"
                    value = separator.join(block) or None
                    if value is not None:
                        values[key] = value
                    continue
                value = _yaml_scalar(raw)
                if value is not None:
                    values[key] = value
        i += 1

    for key in FRONTMATTER_KEYS:
        if not values.get(key, "").strip():
            errors.append(f"{label}: frontmatter {key!r} must be a nonempty string")
    return values if all(values.get(key, "").strip() for key in FRONTMATTER_KEYS) else None


def _package_files(
    directory: Path, root: Path, errors: list[str]
) -> tuple[tuple[bytes, bytes], ...] | None:
    files: list[tuple[bytes, bytes]] = []
    try:
        for path in directory.rglob("*"):
            if not stat.S_ISREG(path.lstat().st_mode):
                continue
            relative = path.relative_to(directory).as_posix().encode(
                "utf-8", "surrogateescape"
            )
            files.append((relative, path.read_bytes()))
    except OSError as exc:
        errors.append(f"{_label(root, directory)}: cannot read skill package ({exc})")
        return None
    return tuple(sorted(files, key=lambda item: item[0]))


def _load_skills(root: Path, errors: list[str]) -> dict[str, Skill]:
    directory = root / "skills"
    paths = sorted(directory.rglob("SKILL.md")) if directory.is_dir() else []
    if not paths:
        errors.append("skills/: no installable SKILL.md files found")
        return {}

    skills: dict[str, Skill] = {}
    for path in paths:
        label = _label(root, path)
        files = _package_files(path.parent, root, errors)
        if files is None:
            continue
        content = dict(files).get(b"SKILL.md")
        if content is None:
            errors.append(f"{label}: SKILL.md must be a regular file")
            continue
        metadata = _frontmatter(content, label, errors)
        if metadata is None:
            continue
        name = metadata["name"]
        if name in skills:
            errors.append(
                f"{label}: duplicate skill name {name!r}; first declared by "
                f"{skills[name].folder}/SKILL.md"
            )
            continue
        skills[name] = Skill(name, _label(root, path.parent), files)
    return skills


def _validate_readme(root: Path, skill_names: set[str], errors: list[str]) -> None:
    path = root / "README.md"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"README.md: cannot read file ({exc})")
        return

    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == "## Skills") + 1
    except StopIteration:
        errors.append("README.md: missing '## Skills' section")
        return
    end = next(
        (i for i in range(start, len(lines)) if re.match(r"^##\s+", lines[i])),
        len(lines),
    )
    row_re = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|\s*$")
    listed: dict[str, int] = {}
    for line_number, line in enumerate(lines[start:end], start + 1):
        match = row_re.match(line)
        if not match:
            continue
        name, purpose = match.groups()
        if name in listed:
            errors.append(
                f"README.md:{line_number}: duplicate skill listing {name!r}; "
                f"first listed on line {listed[name]}"
            )
        else:
            listed[name] = line_number
        if not purpose.strip():
            errors.append(f"README.md:{line_number}: skill {name!r} has no purpose")

    for name in sorted(skill_names - listed.keys()):
        errors.append(f"README.md: skill {name!r} is not listed in '## Skills'")
    for name in sorted(listed.keys() - skill_names):
        errors.append(f"README.md: lists unknown skill {name!r}")


def _keys(value: Any, expected: tuple[str, ...], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label}: must be an object")
        return False
    actual = set(value)
    wanted = set(expected)
    missing = sorted(wanted - actual)
    extra = sorted(actual - wanted)
    if missing:
        errors.append(f"{label}: missing keys {missing!r}")
    if extra:
        errors.append(f"{label}: unexpected keys {extra!r}")
    return not missing and not extra


def _text(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: must be a nonempty string")
        return False
    return True


def _texts(value: Any, label: str, errors: list[str], *, nonempty: bool) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        errors.append(f"{label}: must be {'a nonempty' if nonempty else 'an'} array")
        return
    for index, item in enumerate(value):
        _text(item, f"{label}[{index}]", errors)


def _validate_cases(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{label}: must be a nonempty array")
        return
    seen: set[str] = set()
    for index, case in enumerate(value):
        case_label = f"{label}[{index}]"
        if not _keys(case, CASE_KEYS, case_label, errors) and not isinstance(case, dict):
            continue
        case_id = case.get("id")
        if _text(case_id, f"{case_label}.id", errors):
            if case_id in seen:
                errors.append(f"{case_label}.id: duplicate case id {case_id!r}")
            seen.add(case_id)
        _text(case.get("prompt"), f"{case_label}.prompt", errors)
        _text(case.get("tests"), f"{case_label}.tests", errors)
        _texts(case.get("traps"), f"{case_label}.traps", errors, nonempty=False)
        _texts(case.get("expectations"), f"{case_label}.expectations", errors, nonempty=True)


def validate_eval(data: Any, expected_skill: str, label: str, errors: list[str]) -> bool:
    start = len(errors)
    if not _keys(data, ROOT_KEYS, label, errors) and not isinstance(data, dict):
        return False
    declared_skill = data.get("skill")
    if _text(declared_skill, f"{label}.skill", errors) and declared_skill != expected_skill:
        errors.append(
            f"{label}.skill: must exactly match frontmatter name {expected_skill!r}, "
            f"got {declared_skill!r}"
        )
    _validate_cases(data.get("cases"), f"{label}.cases", errors)
    return len(errors) == start


class _DuplicateKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(f"duplicate key {key!r}")
        result[key] = value
    return result


def _read_eval(path: Path, root: Path, expected_skill: str, errors: list[str]) -> dict[str, Any] | None:
    label = _label(root, path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, _DuplicateKey) as exc:
        errors.append(f"{label}: invalid JSON ({exc})")
        return None
    return data if validate_eval(data, expected_skill, label, errors) else None


def structure(root: Path) -> tuple[dict[str, Skill], list[str]]:
    """Run the structure checks on a tree; return its skills, with valid cases, and errors."""
    errors: list[str] = []
    skills = _load_skills(root, errors)
    _validate_readme(root, set(skills), errors)

    eval_dir = root / "evals"
    expected_paths = {eval_dir / f"{name}.json": name for name in skills}
    for path in sorted(eval_dir.rglob("*.json")) if eval_dir.is_dir() else []:
        if path not in expected_paths:
            errors.append(f"{_label(root, path)}: orphan evaluation file")

    for path, name in sorted(expected_paths.items(), key=lambda item: item[1]):
        if not path.is_file():
            errors.append(f"{_label(root, path)}: missing evaluation file for skill {name!r}")
            continue
        record = _read_eval(path, root, name, errors)
        if record is not None:
            skills[name] = replace(skills[name], cases=tuple(record["cases"]))
    return skills, errors


# ---------------------------------------------------------------- git snapshots


def _git(root: Path, *args: str, stdin: bytes | None = None) -> bytes:
    done = subprocess.run(["git", *args], cwd=root, input=stdin, capture_output=True)
    if done.returncode:
        detail = done.stderr.decode("utf-8", "replace").strip()
        raise CheckError(f"git {' '.join(args)}: {detail}")
    return done.stdout


def snapshot_index(root: Path, dest: Path) -> None:
    """Write the staged README.md, skills/ and evals/ to dest."""
    listed = _git(root, "ls-files", "-z", "--", "README.md", "skills", "evals")
    if listed:
        _git(root, "checkout-index", "-z", "--stdin", f"--prefix={dest}/", stdin=listed)
    dest.mkdir(parents=True, exist_ok=True)


def snapshot_ref(root: Path, ref: str, dest: Path) -> None:
    archive = _git(root, "archive", "--format=tar", ref)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(dest, filter="data")


def staged_paths(root: Path) -> list[str]:
    return [
        path.decode("utf-8", "surrogateescape")
        for path in _git(root, "diff", "--cached", "--name-only", "-z").split(b"\0")
        if path
    ]


def touched_skills(paths: list[str], skills: dict[str, Skill]) -> dict[str, bool]:
    """Map each skill with a staged folder or eval file change to whether its folder changed.

    A staged eval file whose skill is gone from the index belongs to a removed skill.
    """
    touched = {
        path.removeprefix("evals/").removesuffix(".json"): False
        for path in paths
        if path.startswith("evals/") and path.endswith(".json")
    }
    for name, skill in skills.items():
        if any(path.startswith(f"{skill.folder}/") for path in paths):
            touched[name] = True
    return touched


def _master_cases(path: Path) -> tuple[Case, ...]:
    """Cases from a master eval file; an unreadable file gives none."""
    try:
        cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
        return tuple(case for case in cases if isinstance(case, dict) and "id" in case)
    except (OSError, ValueError, KeyError, TypeError):
        return ()


def changed_cases(staged: tuple[Case, ...], master: tuple[Case, ...]) -> list[str]:
    """Describe every case whose prompt or expectations differ from master."""
    master_by_id = {case["id"]: case for case in master}
    staged_ids = {case["id"] for case in staged}
    changes = []
    for case in staged:
        old = master_by_id.get(case["id"])
        if old is None:
            changes.append(f"{case['id']}: added")
            continue
        parts = [key for key in ("prompt", "expectations") if old.get(key) != case[key]]
        if parts:
            changes.append(f"{case['id']}: {' and '.join(parts)} changed")
    changes.extend(f"{case_id}: removed" for case_id in master_by_id if case_id not in staged_ids)
    return changes


# ---------------------------------------------------------------- runs and judging


def _path_inside(path: str, cwd: Path) -> bool:
    for part in path.split(";"):
        part = part.strip()
        if not part:
            continue
        if "://" in part or part.startswith("~"):
            return False
        if os.path.isabs(part):
            real_cwd = os.path.realpath(cwd)
            if os.path.commonpath([os.path.realpath(part), real_cwd]) != real_cwd:
                return False
        elif ".." in Path(part).parts:
            return False
    return True


def run_omp(prompt: str, cwd: Path, system: str | None, tools: bool, log: Path) -> tuple[str, str]:
    """Run one isolated `omp -p` session in cwd; return its answer and model."""
    overlay = log.with_suffix(".overlay.yml")
    overlay.write_text(OMP_OVERLAY, encoding="utf-8")
    args = ["omp", *OMP_FLAGS, "--config", str(overlay), "--cwd", str(cwd)]
    args += ["--tools", "read,grep,glob"] if tools else ["--no-tools"]
    if system:
        args += ["--append-system-prompt", system]
    args.append(prompt)
    # A hook's GIT_* variables would point the session at this repository.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    try:
        done = subprocess.run(
            args, cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=TIMEOUT
        )
    except FileNotFoundError:
        raise CheckError("omp is not on PATH") from None
    except subprocess.TimeoutExpired:
        raise CheckError(f"omp did not finish within {TIMEOUT}s") from None
    log.write_bytes(done.stdout + (b"\n# stderr\n" + done.stderr if done.stderr else b""))
    if done.returncode:
        detail = done.stderr.decode("utf-8", "replace").strip().splitlines()
        raise CheckError(f"omp exited {done.returncode}: {detail[-1] if detail else 'no output'}")

    final: dict[str, Any] | None = None
    for line in done.stdout.decode("utf-8", "replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "tool_execution_start":
            path = (event.get("args") or {}).get("path")
            if isinstance(path, str) and not _path_inside(path, cwd):
                raise CheckError(f"session read outside its directory: {path}")
        if event.get("type") == "message_end" and event["message"].get("role") == "assistant":
            final = event["message"]
    if final is None:
        raise CheckError("omp produced no answer")
    if final.get("stopReason") != "stop":
        raise CheckError(f"omp stopped with {final.get('stopReason')}: {final.get('errorMessage', '')}")
    text = "".join(part.get("text", "") for part in final["content"] if part.get("type") == "text")
    if not text.strip():
        raise CheckError("omp gave an empty answer")
    return text, _model_label(final)


def _model_label(message: dict[str, Any]) -> str:
    """Provider/model of an omp assistant message, plus its thinking effort when reported."""
    effort = ((message.get("requestControls") or {}).get("effort") or {}).get("topLevel")
    return f"{message.get('provider')}/{message.get('model')}" + (f" ({effort})" if effort else "")


@dataclass(frozen=True)
class Verdict:
    passed: bool
    reason: str


def parse_verdicts(text: str, count: int) -> list[Verdict]:
    start, end = text.find("["), text.rfind("]")
    try:
        items = json.loads(text[start : end + 1]) if start != -1 else None
    except json.JSONDecodeError:
        items = None
    if not isinstance(items, list) or len(items) != count:
        raise CheckError(f"judge output is not a JSON array of {count} verdicts")
    verdicts = []
    for number, item in enumerate(items, 1):
        if (
            not isinstance(item, dict)
            or item.get("n") != number
            or not isinstance(item.get("pass"), bool)
            or not isinstance(item.get("reason"), str)
            or not item["reason"].strip()
        ):
            raise CheckError(f"judge verdict {number} is malformed: {item!r}")
        verdicts.append(Verdict(item["pass"], " ".join(item["reason"].split())))
    return verdicts


@dataclass
class Outcome:
    verdicts: list[Verdict] | None = None
    error: str | None = None
    models: set[str] = field(default_factory=set)
    log: Path | None = None


@dataclass(frozen=True)
class Runs:
    """Where sessions keep their files, the pool they share, and what runs them."""

    out: Path
    pool: ThreadPoolExecutor
    runner: Runner

    def workdir(self) -> Path:
        # Random directory names keep the version out of what each session sees.
        work = self.out / "work"
        work.mkdir(exist_ok=True)
        return Path(tempfile.mkdtemp(dir=work))

    def start(
        self, skill: Skill, cases: tuple[Case, ...], version: str
    ) -> dict[str, Future[Outcome]]:
        """Start one run per case on this version of the skill."""
        return {
            case["id"]: self.pool.submit(
                run_case, case, skill, f"{skill.name}.{case['id']}.{version}", self
            )
            for case in cases
        }


def run_case(case: Case, skill: Skill, tag: str, runs: Runs) -> Outcome:
    """Answer one case with one version of a skill, then judge the answer."""
    outcome = Outcome(log=runs.out / f"{tag}.run.jsonl")
    try:
        workdir = runs.workdir()
        for relative, content in skill.files:
            target = workdir / relative.decode("utf-8", "surrogateescape")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        answer, model = runs.runner(
            case["prompt"], workdir, RUN_SYSTEM.format(name=skill.name), True, outcome.log
        )
        outcome.models.add(model)
        expectations = "\n".join(f"{n}. {text}" for n, text in enumerate(case["expectations"], 1))
        outcome.log = runs.out / f"{tag}.judge.jsonl"
        verdict, model = runs.runner(
            JUDGE_PROMPT % (case["prompt"], expectations, answer),
            runs.workdir(),
            None,
            False,
            outcome.log,
        )
        outcome.models.add(model)
        outcome.verdicts = parse_verdicts(verdict, len(case["expectations"]))
    except CheckError as exc:
        outcome.error = str(exc)
    return outcome


# ---------------------------------------------------------------- check and report


def _score(outcomes: dict[str, Outcome]) -> int:
    return sum(v.passed for o in outcomes.values() if o.verdicts for v in o.verdicts)


def _outcomes(started: dict[str, Future[Outcome]]) -> dict[str, Outcome]:
    return {case_id: run.result() for case_id, run in started.items()}


def _changed_results(
    cases: tuple[Case, ...], master: dict[str, Outcome], staged: dict[str, Outcome]
) -> list[str]:
    """Expectations whose result differs between versions, with the staged judge's reason."""
    lines = []
    for case in cases:
        old, new = master[case["id"]].verdicts, staged[case["id"]].verdicts
        if not (old and new):
            continue
        for number, (expectation, was, now) in enumerate(zip(case["expectations"], old, new), 1):
            if was.passed != now.passed:
                result = "pass → fail" if was.passed else "fail → pass"
                lines.append(f"- {case['id']} #{number} ({result}): {expectation}")
                lines.append(f"  Staged judge: {now.reason}")
    return ["Changed results:", *lines] if lines else []


def _run_versions(staged: Skill, master: Skill, runs: Runs) -> tuple[list[str], list[str]]:
    """Run and judge the staged cases on both versions; return report lines and block reasons.

    A master without the skill gets no runs, and the report gives the staged score alone.
    """
    cases = staged.cases
    total = sum(len(case["expectations"]) for case in cases)
    staged_runs = runs.start(staged, cases, "staged")
    if master.files:
        master_runs = runs.start(master, cases, "master")
        master_out, staged_out = _outcomes(master_runs), _outcomes(staged_runs)
        before, after = _score(master_out), _score(staged_out)
        scores = [f"Score: master {before}/{total} → staged {after}/{total}"]
        scores += _changed_results(cases, master_out, staged_out)
        dropped = after < before
    else:
        master_out, staged_out = {}, _outcomes(staged_runs)
        scores = [f"Score: staged {_score(staged_out)}/{total} (master has no {staged.name})"]
        dropped = False

    versions = (("master", master_out), ("staged", staged_out))
    models = sorted({model for _, out in versions for o in out.values() for model in o.models})
    failures = [
        f"- {case_id} ({version}): {o.error}" + (f" [{o.log}]" if o.log and o.log.exists() else "")
        for version, out in versions
        for case_id, o in out.items()
        if o.error
    ]
    lines = [f"Model: {', '.join(models) or 'unknown (no session finished)'}", *scores]
    if failures:
        return [*lines, "Failures:", *failures], ["a run or judgment failed"]
    return lines, ["the score dropped"] if dropped else []


def compare(
    staged: Skill, master: Skill, folder_staged: bool, runs: Runs
) -> tuple[list[str], bool]:
    """Report one skill and whether it blocks.

    Runs happen only when its folder is staged and differs from master.
    """
    if not staged.files:
        lines, reasons = ["Skill removed; no runs."], []
    elif not folder_staged:
        lines, reasons = ["Skill folder not staged; no runs."], []
    elif staged.files == master.files:
        lines, reasons = ["Staged skill folder matches master; no runs."], []
    else:
        lines, reasons = _run_versions(staged, master, runs)
    changes = changed_cases(staged.cases, master.cases)
    if changes:
        lines += ["Changed cases:", *(f"- {change}" for change in changes)]
        reasons.append("cases changed")
    if reasons:
        lines.append(f"Blocked: {'; '.join(reasons)}.")
    return [f"## {staged.name}", *lines], bool(reasons)


def check(root: Path, names: list[str] | None = None, runner: Runner = run_omp) -> tuple[str, bool]:
    """Check the staged tree; return the report and whether it blocks.

    Works in a scratch folder, kept only when it holds raw session outputs.
    """
    out = Path(tempfile.mkdtemp(prefix="skill-evals-"))
    try:
        with ThreadPoolExecutor(CONCURRENCY) as pool:
            report, blocked = _run_checks(root, names, Runs(out, pool, runner))
    finally:
        if not any(out.glob("*.jsonl")):
            shutil.rmtree(out)
    return (f"{report}\nRaw outputs: {out}" if out.exists() else report), blocked


def _run_checks(root: Path, names: list[str] | None, runs: Runs) -> tuple[str, bool]:
    staged_root, master_root = runs.out / "staged", runs.out / "master"
    snapshot_index(root, staged_root)
    skills, errors = structure(staged_root)
    if errors:
        return "\n".join(["## Structure checks failed", *(f"- {e}" for e in errors)]), True

    if names is None:
        touched = touched_skills(staged_paths(root), skills)
    else:
        unknown = sorted(set(names) - set(skills))
        if unknown:
            return f"Unknown skills: {', '.join(unknown)}", True
        touched = dict.fromkeys(names, True)  # a named skill counts as a staged folder
    if not touched:
        return "Structure checks passed; no skill or eval changes staged.", False

    try:
        snapshot_ref(root, MASTER_REF, master_root)
    except CheckError as exc:
        return f"Cannot read {MASTER_REF}: {exc}", True
    master_skills = {
        name: replace(skill, cases=_master_cases(master_root / "evals" / f"{name}.json"))
        for name, skill in _load_skills(master_root, []).items()
    }

    lines, blocked = [], False
    for name, folder_staged in sorted(touched.items()):
        print(f"evals: checking {name}…", file=sys.stderr, flush=True)
        absent = Skill(name, "", ())
        skill_lines, skill_blocked = compare(
            skills.get(name, absent), master_skills.get(name, absent), folder_staged, runs
        )
        lines += [*skill_lines, ""]
        blocked = blocked or skill_blocked
    return "\n".join(lines), blocked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("skills", nargs="*", help="skill names to check instead of the staged ones")
    args = parser.parse_args(argv)
    try:
        root = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
        report, blocked = check(root, args.skills or None)
    except CheckError as exc:
        report, blocked = str(exc), True
    print(report)
    if blocked:
        print(
            "\nCommit blocked. To approve it, follow 'Approve a block' in AGENTS.md.",
            file=sys.stderr,
        )
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
