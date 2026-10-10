#!/usr/bin/env python3
"""Validate skill evaluations and print their score deltas as Markdown."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HASH_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
FRONTMATTER_KEYS = ("name", "description")
ROOT_KEYS = ("skill", "cases", "comparison")
CASE_KEYS = ("id", "prompt", "criteria")
COMPARISON_KEYS = (
    "suite_hash",
    "environment",
    "base",
    "current",
    "cases",
    "confirmed_by",
    "confirmed_at",
)
COMPARISON_CASE_KEYS = ("id", "base", "current", "rationale")


@dataclass(frozen=True)
class Skill:
    name: str
    path: Path
    files: tuple[tuple[bytes, bytes], ...]

    @property
    def hash(self) -> str:
        return skill_hash(self.files)


@dataclass
class AuditResult:
    rows: list[tuple[str, str]]
    warnings: list[str]
    errors: list[str]
    base_available: bool = True


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def skill_hash(files: list[tuple[str | bytes, bytes]] | tuple[tuple[bytes, bytes], ...]) -> str:
    framed: dict[bytes, bytes] = {}
    for relative_path, content in files:
        path = (
            relative_path
            if isinstance(relative_path, bytes)
            else relative_path.encode("utf-8", "surrogateescape")
        )
        if path in framed:
            raise ValueError(f"duplicate package path {path!r}")
        framed[path] = content

    digest = hashlib.sha256()
    for path in sorted(framed):
        content = framed[path]
        digest.update(len(path).to_bytes(8, "big"))
        digest.update(path)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def canonical_cases_hash(cases: list[Any]) -> str:
    payload = json.dumps(
        cases, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _digest(payload)


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "README.md").is_file() and (candidate / "skills").is_dir():
            return candidate
    raise RuntimeError("could not locate a repository root containing README.md and skills/")


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


def _load_skills(root: Path, errors: list[str]) -> list[Skill]:
    directory = root / "skills"
    paths = sorted(directory.rglob("SKILL.md")) if directory.is_dir() else []
    if not paths:
        errors.append("skills/: no installable SKILL.md files found")
        return []

    skills: list[Skill] = []
    seen: dict[str, Path] = {}
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
        if name in seen:
            errors.append(
                f"{label}: duplicate skill name {name!r}; first declared by "
                f"{_label(root, seen[name])}"
            )
            continue
        seen[name] = path
        skills.append(Skill(name, path, files))
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


def _hash(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        errors.append(f"{label}: must be 'sha256:' followed by 64 lowercase hex digits")
        return False
    return True


def _score(value: Any, label: str, errors: list[str]) -> bool:
    if type(value) is not int or not 0 <= value <= 100:
        errors.append(f"{label}: must be an integer from 0 to 100")
        return False
    return True


def _validate_cases(value: Any, label: str, errors: list[str]) -> tuple[list[str], bool]:
    start = len(errors)
    if not isinstance(value, list) or not value:
        errors.append(f"{label}: must be a nonempty array")
        return [], False

    ids: list[str] = []
    seen: set[str] = set()
    for index, case in enumerate(value):
        case_label = f"{label}[{index}]"
        if not _keys(case, CASE_KEYS, case_label, errors):
            if not isinstance(case, dict):
                continue
        case_id = case.get("id")
        if _text(case_id, f"{case_label}.id", errors):
            if case_id in seen:
                errors.append(f"{case_label}.id: duplicate case id {case_id!r}")
            else:
                seen.add(case_id)
                ids.append(case_id)
        _text(case.get("prompt"), f"{case_label}.prompt", errors)
        criteria = case.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"{case_label}.criteria: must be a nonempty array")
        else:
            for criterion_index, criterion in enumerate(criteria):
                _text(
                    criterion,
                    f"{case_label}.criteria[{criterion_index}]",
                    errors,
                )
    return ids, len(errors) == start


def _score_record(
    value: Any, label: str, errors: list[str]
) -> tuple[str | None, int | None]:
    if not _keys(value, ("skill_hash", "score"), label, errors):
        if not isinstance(value, dict):
            return None, None
    hash_value = value.get("skill_hash")
    score_value = value.get("score")
    return (
        hash_value if _hash(hash_value, f"{label}.skill_hash", errors) else None,
        score_value if _score(score_value, f"{label}.score", errors) else None,
    )


def _validate_comparison(
    value: Any,
    suite_ids: list[str],
    suite_valid: bool,
    label: str,
    errors: list[str],
) -> bool:
    start = len(errors)
    if not _keys(value, COMPARISON_KEYS, label, errors):
        if not isinstance(value, dict):
            return False

    _hash(value.get("suite_hash"), f"{label}.suite_hash", errors)
    environment = value.get("environment")
    if _keys(environment, ("agent", "model"), f"{label}.environment", errors):
        _text(environment.get("agent"), f"{label}.environment.agent", errors)
        _text(environment.get("model"), f"{label}.environment.model", errors)

    base = value.get("base")
    base_score: int | None = None
    if base is not None:
        _, base_score = _score_record(base, f"{label}.base", errors)
    _, current_score = _score_record(value.get("current"), f"{label}.current", errors)
    _text(value.get("confirmed_by"), f"{label}.confirmed_by", errors)
    _text(value.get("confirmed_at"), f"{label}.confirmed_at", errors)

    entries = value.get("cases")
    current_scores: dict[str, int] = {}
    base_scores: dict[str, int] = {}
    comparison_ids: list[str] = []
    duplicate_id = False
    if not isinstance(entries, list):
        errors.append(f"{label}.cases: must be an array")
    else:
        seen: set[str] = set()
        for index, entry in enumerate(entries):
            entry_label = f"{label}.cases[{index}]"
            if not _keys(entry, COMPARISON_CASE_KEYS, entry_label, errors):
                if not isinstance(entry, dict):
                    continue
            case_id = entry.get("id")
            id_valid = _text(case_id, f"{entry_label}.id", errors)
            if id_valid:
                if case_id in seen:
                    duplicate_id = True
                    errors.append(f"{entry_label}.id: duplicate case id {case_id!r}")
                else:
                    seen.add(case_id)
                    comparison_ids.append(case_id)
            case_current = entry.get("current")
            if _score(case_current, f"{entry_label}.current", errors) and id_valid and case_id not in current_scores:
                current_scores[case_id] = case_current
            case_base = entry.get("base")
            if base is None:
                if case_base is not None:
                    errors.append(f"{entry_label}.base: must be null when comparison.base is null")
            elif _score(case_base, f"{entry_label}.base", errors) and id_valid and case_id not in base_scores:
                base_scores[case_id] = case_base
            _text(entry.get("rationale"), f"{entry_label}.rationale", errors)

    coverage_valid = False
    if suite_valid and isinstance(entries, list):
        suite_set = set(suite_ids)
        comparison_set = set(comparison_ids)
        missing = sorted(suite_set - comparison_set)
        extra = sorted(comparison_set - suite_set)
        if missing:
            errors.append(f"{label}.cases: missing suite ids {missing!r}")
        if extra:
            errors.append(f"{label}.cases: unknown suite ids {extra!r}")
        coverage_valid = (
            not missing
            and not extra
            and not duplicate_id
            and len(comparison_ids) == len(suite_ids)
        )

    count = len(suite_ids)
    if coverage_valid and count and len(current_scores) == count and current_score is not None:
        aggregate = (sum(current_scores.values()) + count // 2) // count
        if current_score != aggregate:
            errors.append(
                f"{label}.current.score: aggregate must be {aggregate}, got {current_score}"
            )
    if (
        base is not None
        and coverage_valid
        and count
        and len(base_scores) == count
        and base_score is not None
    ):
        aggregate = (sum(base_scores.values()) + count // 2) // count
        if base_score != aggregate:
            errors.append(f"{label}.base.score: aggregate must be {aggregate}, got {base_score}")
    return len(errors) == start


def validate_eval(data: Any, expected_skill: str, label: str, errors: list[str]) -> bool:
    start = len(errors)
    if not _keys(data, ROOT_KEYS, label, errors):
        if not isinstance(data, dict):
            return False

    declared_skill = data.get("skill")
    if _text(declared_skill, f"{label}.skill", errors) and declared_skill != expected_skill:
        errors.append(
            f"{label}.skill: must exactly match frontmatter name {expected_skill!r}, "
            f"got {declared_skill!r}"
        )
    suite_ids, suite_valid = _validate_cases(data.get("cases"), f"{label}.cases", errors)
    comparison = data.get("comparison")
    if comparison is not None:
        _validate_comparison(
            comparison,
            suite_ids,
            suite_valid,
            f"{label}.comparison",
            errors,
        )
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


def _base_hashes(
    root: Path, ref: str, skills: list[Skill], errors: list[str]
) -> dict[str, str | None] | None:
    try:
        verified = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        errors.append(f"git: cannot resolve base {ref!r} ({exc})")
        return None
    if verified.returncode:
        detail = verified.stderr.decode("utf-8", "replace").strip().replace("\n", " ")
        suffix = f" ({detail})" if detail else ""
        errors.append(f"git: base ref {ref!r} is not a commit{suffix}")
        return None

    listed = subprocess.run(
        ["git", "ls-tree", "-r", "-z", "--full-tree", ref, "--", "skills"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if listed.returncode:
        detail = listed.stderr.decode("utf-8", "replace").strip().replace("\n", " ")
        errors.append(f"git: cannot list skills at base {ref!r} ({detail})")
        return None

    regular_files: list[bytes] = []
    for entry in listed.stdout.split(b"\0"):
        if not entry:
            continue
        try:
            header, path = entry.split(b"\t", 1)
            mode, object_type, _ = header.split(b" ", 2)
        except ValueError:
            errors.append(f"git: malformed ls-tree entry at base {ref!r}")
            return None
        if object_type == b"blob" and mode.startswith(b"100"):
            regular_files.append(path)

    cache: dict[bytes, bytes] = {}

    def show(path: bytes) -> bytes | None:
        if path in cache:
            return cache[path]
        path_text = path.decode("utf-8", "surrogateescape")
        shown = subprocess.run(
            ["git", "show", "--no-ext-diff", "--no-textconv", f"{ref}:{path_text}"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if shown.returncode:
            detail = shown.stderr.decode("utf-8", "replace").strip().replace("\n", " ")
            errors.append(f"git: cannot read {ref}:{path_text} ({detail})")
            return None
        cache[path] = shown.stdout
        return shown.stdout

    directories: dict[str, bytes] = {}
    sources: dict[str, bytes] = {}
    skill_paths = [
        path
        for path in regular_files
        if path == b"skills/SKILL.md" or path.endswith(b"/SKILL.md")
    ]
    for path in skill_paths:
        content = show(path)
        if content is None:
            return None
        path_text = path.decode("utf-8", "surrogateescape")
        metadata = _frontmatter(content, f"{ref}:{path_text}", errors)
        if metadata is None:
            continue
        name = metadata["name"]
        if name in directories:
            errors.append(
                f"{ref}:{path_text}: duplicate base skill name {name!r}; first declared by "
                f"{ref}:{sources[name].decode('utf-8', 'surrogateescape')}"
            )
            continue
        directories[name] = path.rsplit(b"/", 1)[0]
        sources[name] = path

    hashes: dict[str, str | None] = {}
    for skill in skills:
        directory = directories.get(skill.name)
        if directory is None:
            hashes[skill.name] = None
            continue
        prefix = directory + b"/"
        package: list[tuple[bytes, bytes]] = []
        for path in regular_files:
            if not path.startswith(prefix):
                continue
            content = show(path)
            if content is None:
                return None
            package.append((path[len(prefix) :], content))
        hashes[skill.name] = skill_hash(package)
    return hashes


def audit(root: Path, base: str | None = None) -> AuditResult:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    skills = _load_skills(root, errors)
    by_name = {skill.name: skill for skill in skills}
    _validate_readme(root, set(by_name), errors)

    eval_dir = root / "evals"
    files = sorted(eval_dir.rglob("*.json")) if eval_dir.is_dir() else []
    expected_paths = {eval_dir / f"{name}.json": name for name in by_name}
    for path in files:
        if path not in expected_paths:
            errors.append(f"{_label(root, path)}: orphan evaluation file")

    records: dict[str, dict[str, Any]] = {}
    for path, name in sorted(expected_paths.items(), key=lambda item: item[1]):
        if not path.is_file():
            errors.append(f"{_label(root, path)}: missing evaluation file for skill {name!r}")
            continue
        record = _read_eval(path, root, name, errors)
        if record is not None:
            records[name] = record

    stale: dict[str, list[str]] = {name: [] for name in by_name}
    for name, record in records.items():
        comparison = record["comparison"]
        if comparison is None:
            continue
        if comparison["suite_hash"] != canonical_cases_hash(record["cases"]):
            stale[name].append("suite hash does not match cases")
        if comparison["current"]["skill_hash"] != by_name[name].hash:
            stale[name].append("current skill hash does not match skill directory")

    base_hashes: dict[str, str | None] | None = None
    selected = sorted(by_name)
    if base is not None:
        base_hashes = _base_hashes(root, base, skills, errors)
        if base_hashes is None:
            selected = []
        else:
            selected = sorted(
                name
                for name, skill in by_name.items()
                if base_hashes[name] is None or base_hashes[name] != skill.hash
            )
            for name in selected:
                record = records.get(name)
                if record is None or record["comparison"] is None:
                    continue
                recorded_base = record["comparison"]["base"]
                old_hash = base_hashes[name]
                if old_hash is None:
                    if recorded_base is not None:
                        stale[name].append("new skill records a non-null base")
                elif recorded_base is None:
                    stale[name].append("changed skill has no recorded base")
                elif recorded_base["skill_hash"] != old_hash:
                    stale[name].append("base skill hash does not match the requested ref")

    for name in sorted(by_name):
        record = records.get(name)
        if record is None:
            continue
        if record["comparison"] is None:
            warnings.append(f"{name}: comparison is missing")
        elif stale[name]:
            warnings.append(f"{name}: comparison is stale ({'; '.join(stale[name])})")

    rows: list[tuple[str, str]] = []
    for name in selected:
        record = records.get(name)
        if record is None:
            rows.append((name, "invalid evaluation"))
            continue
        comparison = record["comparison"]
        if comparison is None:
            rows.append((name, "comparison missing"))
            continue
        if stale[name]:
            rows.append((name, "comparison stale"))
            continue
        previous = comparison["base"]
        current = comparison["current"]["score"]
        if previous is None:
            rows.append((name, f"new → {current}"))
            continue
        previous_score = previous["score"]
        delta = current - previous_score
        score = f"{previous_score} → {current} ({delta:+d})"
        rows.append((name, score))
        if delta < 0:
            warnings.append(f"{name}: regression {score}")

    return AuditResult(rows, warnings, errors, base is None or base_hashes is not None)


def _table_cell(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|")


def render_report(result: AuditResult, base: str | None = None) -> str:
    lines = ["## Skill evaluation report", ""]
    if base is not None:
        safe_base = base.replace("`", "'").replace("\n", " ")
        lines.extend([f"Base: `{safe_base}`", ""])

    if result.rows:
        lines.extend(["| Skill | Score |", "| --- | --- |"])
        for name, score in result.rows:
            lines.append(f"| `{_table_cell(name)}` | {_table_cell(score)} |")
    elif base is not None and not result.base_available:
        lines.append("_Score deltas unavailable because the base ref could not be read._")
    elif base is not None:
        lines.append("_No skills changed from the base ref._")
    else:
        lines.append("_No skills available to report._")

    if result.warnings:
        lines.extend(["", "### Warnings", ""])
        lines.extend(f"- {warning}" for warning in result.warnings)
    if result.errors:
        lines.extend(["", "### Errors", ""])
        lines.extend(f"- {error}" for error in result.errors)
    if not result.warnings and not result.errors:
        lines.extend(["", "Validation passed."])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Git ref used to identify and verify changed skills")
    args = parser.parse_args(argv)

    try:
        root = find_repo_root()
        result = audit(root, args.base)
    except RuntimeError as exc:
        result = AuditResult([], [], [str(exc)], base_available=False)
    report = render_report(result, args.base)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as stream:
                stream.write(report + "\n")
        except OSError as exc:
            result.errors.append(f"GITHUB_STEP_SUMMARY: cannot append report ({exc})")
            report = render_report(result, args.base)

    print(report)
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
