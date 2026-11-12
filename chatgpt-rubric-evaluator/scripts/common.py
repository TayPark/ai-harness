"""Shared packet and report checks for chatgpt-rubric-evaluator."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PACKET_VERSION = "1.0"
MAX_TEXT_BYTES = 1_000_000
EXCLUDED_DIRS = {
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv",
    "__pycache__", "build", "dist", "node_modules", ".work",
}
SECRET_FILENAME = re.compile(
    r"^(?:\.env(?:\..*)?|id_(?:rsa|dsa|ecdsa|ed25519)(?:\..*)?|"
    r".*\.(?:pem|p12|pfx|key)|.*(?:credentials?|secrets?)(?:\.[^.]+)?)$",
    re.IGNORECASE,
)
SECRET_TEXT_PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----")),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")),
    ("credential_assignment", re.compile(
        r"(?i)\b(api[_-]?key|access[_-]?key|client[_-]?secret|secret|password|passwd|token|authorization)"
        r"(\s*[:=]\s*)(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;]+)"
    )),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("national_id", re.compile(r"\b\d{6}-?[1-8]\d{6}\b")),
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)


def normalize_timestamp(value: str | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("collected-at must be an ISO 8601 timestamp with a timezone") from exc
    if parsed.tzinfo is None:
        raise ValueError("collected-at must include a timezone")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_rubric(rubric: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(rubric, dict):
        return ["rubric must be a JSON object"]
    if set(rubric) != {"rubric_id", "version", "score_scale", "passing_threshold", "score_guide", "target_types"}:
        errors.append("rubric must contain only rubric_id, version, score_scale, passing_threshold, score_guide, target_types")
    for key in ("rubric_id", "version"):
        if not isinstance(rubric.get(key), str) or not rubric[key].strip():
            errors.append(f"rubric.{key} must be a non-empty string")
    scale = rubric.get("score_scale")
    if not isinstance(scale, dict) or set(scale) != {"min", "max"} or type(scale.get("min")) is not int or type(scale.get("max")) is not int or scale != {"min": 0, "max": 4}:
        errors.append("rubric.score_scale must be exactly {min: 0, max: 4}")
    threshold = rubric.get("passing_threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not 0 <= threshold <= 100:
        errors.append("rubric.passing_threshold must be a number from 0 through 100")
    guide = rubric.get("score_guide")
    if not isinstance(guide, dict) or set(guide) != {str(n) for n in range(5)} or not all(
        isinstance(value, str) and value.strip() for value in guide.values()
    ):
        errors.append("rubric.score_guide must define non-empty guidance for scores 0 through 4")
    target_types = rubric.get("target_types")
    if not isinstance(target_types, dict) or not target_types:
        errors.append("rubric.target_types must be a non-empty object")
        return errors
    for type_id, spec in target_types.items():
        if not isinstance(type_id, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", type_id):
            errors.append(f"invalid target type id: {type_id}")
        if not isinstance(spec, dict) or set(spec) != {"dimensions", "critical_conditions"}:
            errors.append(f"target type {type_id} must contain only dimensions and critical_conditions")
            continue
        dimensions = spec.get("dimensions")
        conditions = spec.get("critical_conditions")
        if not isinstance(dimensions, list) or not dimensions:
            errors.append(f"target type {type_id} needs at least one dimension")
            dimensions = []
        if not isinstance(conditions, list) or not conditions:
            errors.append(f"target type {type_id} needs at least one critical condition")
            conditions = []
        ids: set[str] = set()
        total_weight = 0
        for item in dimensions:
            if not isinstance(item, dict) or set(item) != {"id", "name", "weight", "applicability", "criterion", "required_evidence"}:
                errors.append(f"target type {type_id} has an invalid dimension")
                continue
            ident = item.get("id")
            if not isinstance(ident, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", ident) or ident in ids:
                errors.append(f"target type {type_id} has an invalid or duplicate dimension id: {ident}")
            else:
                ids.add(ident)
            for field in ("name", "criterion", "required_evidence"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    errors.append(f"dimension {ident} requires non-empty {field}")
            weight = item.get("weight")
            if isinstance(weight, bool) or not isinstance(weight, int) or not 1 <= weight <= 100:
                errors.append(f"dimension {ident} weight must be an integer from 1 through 100")
            else:
                total_weight += weight
            if item.get("applicability") not in ("required", "optional"):
                errors.append(f"dimension {ident} applicability must be required or optional")
        if dimensions and total_weight != 100:
            errors.append(f"target type {type_id} dimension weights must sum to 100; got {total_weight}")
        condition_ids: set[str] = set()
        for item in conditions:
            if not isinstance(item, dict) or set(item) != {"id", "description", "applicability"}:
                errors.append(f"target type {type_id} has an invalid critical condition")
                continue
            ident = item.get("id")
            if not isinstance(ident, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", ident) or ident in condition_ids:
                errors.append(f"target type {type_id} has an invalid or duplicate critical condition id: {ident}")
            else:
                condition_ids.add(ident)
            if not isinstance(item.get("description"), str) or not item["description"].strip():
                errors.append(f"critical condition {ident} needs a description")
            if item.get("applicability") not in ("required", "optional"):
                errors.append(f"critical condition {ident} applicability must be required or optional")
    return errors


def _redact(text: str) -> tuple[str, list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    for label, pattern in SECRET_TEXT_PATTERNS:
        text, count = pattern.subn(
            lambda match: (match.group(1) + match.group(2) + '"[REDACTED_SECRET]"')
            if label == "credential_assignment" else f"[REDACTED_{label.upper()}]",
            text,
        )
        if count:
            results.append({"type": label, "count": count})
    return text, results


def _is_secret_filename(relative_path: str) -> bool:
    return any(SECRET_FILENAME.fullmatch(part) for part in Path(relative_path).parts)


def _read_and_hash(path: Path) -> tuple[str, int, str | None]:
    before = path.stat()
    hasher = hashlib.sha256()
    chunks: list[bytes] | None = [] if before.st_size <= MAX_TEXT_BYTES else None
    size = 0
    with path.open("rb") as source:
        while chunk := source.read(65536):
            hasher.update(chunk)
            size += len(chunk)
            if chunks is not None:
                if size <= MAX_TEXT_BYTES:
                    chunks.append(chunk)
                else:
                    chunks = None
    after = path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise RuntimeError(f"target changed while packet was being created: {path.name}")
    data = b"".join(chunks) if chunks is not None else None
    return hasher.hexdigest(), size, data.decode("utf-8") if data is not None else None


def _collect_paths(root: Path, scope_kind: str) -> tuple[list[tuple[str, Path | None, str | None]], list[dict[str, str]]]:
    entries: list[tuple[str, Path | None, str | None]] = []
    exclusions: list[dict[str, str]] = []
    if scope_kind == "file":
        entries.append((root.name, root, None))
        return entries, exclusions
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for name in sorted(dirnames):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                exclusions.append({
                    "path": relative, "reason": "symbolic_link_directory",
                    "sha256": digest(os.fsencode(os.readlink(path))),
                })
            elif name in EXCLUDED_DIRS:
                exclusions.append({"path": relative, "reason": "generated_or_dependency_directory", "sha256": None})
            else:
                kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                entries.append((relative, path, "symbolic_link"))
            elif not stat.S_ISREG(path.lstat().st_mode):
                entries.append((relative, None, "special_file"))
            else:
                entries.append((relative, path, None))
    entries.sort(key=lambda item: item[0])
    exclusions.sort(key=lambda item: item["path"])
    return entries, exclusions


def make_evidence(root: Path, scope_kind: str, collected_at: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths, exclusions = _collect_paths(root, scope_kind)
    evidence: list[dict[str, Any]] = []
    for index, (relative, path, omission) in enumerate(paths, start=1):
        record: dict[str, Any] = {
            "id": f"E{index:04d}", "path": relative, "location": relative,
            "sha256": None, "size_bytes": None, "collected_at": collected_at,
            "content_status": "OMITTED", "omission_reason": None,
            "inspection": {"content_type": None, "redactions": []}, "content": None,
        }
        if omission:
            record["omission_reason"] = omission
            if omission == "symbolic_link":
                link_data = os.fsencode(os.readlink(path)) if path is not None else b""
                record["sha256"], record["size_bytes"] = digest(link_data), len(link_data)
                record["inspection"]["content_type"] = "SYMLINK"
            else:
                record["inspection"]["content_type"] = "SPECIAL_FILE"
        else:
            assert path is not None
            file_hash, size, decoded = _read_and_hash(path)
            record["sha256"], record["size_bytes"] = file_hash, size
            if _is_secret_filename(relative):
                record["omission_reason"] = "sensitive_filename"
                record["inspection"]["content_type"] = "OMITTED_BY_FILENAME_POLICY"
            elif decoded is None:
                record["omission_reason"] = "file_over_1000000_bytes"
                record["inspection"]["content_type"] = "SIZE_LIMIT"
            else:
                try:
                    decoded.encode("utf-8", errors="strict")
                except UnicodeEncodeError:
                    record["omission_reason"] = "not_utf8_text"
                    record["inspection"]["content_type"] = "NON_UTF8"
                else:
                    sanitized, redactions = _redact(decoded)
                    record["content_status"] = "INCLUDED"
                    record["inspection"] = {"content_type": "UTF8_TEXT", "redactions": redactions}
                    record["content"] = sanitized
        evidence.append(record)
    scope = {
        "kind": scope_kind,
        "root_label": root.name,
        "files_discovered": len(evidence),
        "files_included": sum(item["content_status"] == "INCLUDED" for item in evidence),
        "files_omitted": sum(item["content_status"] == "OMITTED" for item in evidence),
        "excluded_directories": exclusions,
    }
    return evidence, scope


def make_packet(target: Path, target_type: str, task: str, rubric: dict[str, Any], collected_at: str | None = None) -> dict[str, Any]:
    rubric_errors = validate_rubric(rubric)
    if rubric_errors:
        raise ValueError("invalid rubric: " + "; ".join(rubric_errors))
    if not isinstance(target_type, str) or target_type not in rubric["target_types"]:
        raise ValueError(f"target type is not defined by rubric: {target_type}")
    if not isinstance(task, str) or not task.strip():
        raise ValueError("task must be a non-empty string")
    root = target.expanduser().resolve(strict=True)
    if not root.is_file() and not root.is_dir():
        raise ValueError("target must be a regular file or directory")
    scope_kind = "file" if root.is_file() else "directory"
    timestamp = normalize_timestamp(collected_at)
    evidence, scope = make_evidence(root, scope_kind, timestamp)
    packet: dict[str, Any] = {
        "packet_schema_version": PACKET_VERSION,
        "packet_id": "",
        "created_at": timestamp,
        "task": task.strip(),
        "target_type": target_type,
        "rubric": rubric,
        "rubric_sha256": digest(canonical_json(rubric)),
        "target": scope,
        "evidence": evidence,
    }
    unsigned = dict(packet)
    unsigned.pop("packet_id")
    packet["packet_id"] = "pkt_" + digest(canonical_json(unsigned))
    return packet


def packet_errors(packet: Any) -> list[str]:
    if not isinstance(packet, dict):
        return ["packet must be a JSON object"]
    required = {"packet_schema_version", "packet_id", "created_at", "task", "target_type", "rubric", "rubric_sha256", "target", "evidence"}
    errors = ["packet has missing or unknown fields"] if set(packet) != required else []
    if packet.get("packet_schema_version") != PACKET_VERSION:
        errors.append("unsupported packet schema version")
    if not isinstance(packet.get("packet_id"), str) or not packet["packet_id"].startswith("pkt_"):
        errors.append("invalid packet_id")
    if not isinstance(packet.get("created_at"), str):
        errors.append("invalid packet created_at")
    else:
        try:
            normalize_timestamp(packet["created_at"])
        except ValueError:
            errors.append("invalid packet created_at")
    if not isinstance(packet.get("task"), str) or not packet["task"].strip():
        errors.append("invalid packet task")
    errors.extend(validate_rubric(packet.get("rubric")))
    rubric = packet.get("rubric")
    if isinstance(rubric, dict):
        target_type = packet.get("target_type")
        if not isinstance(target_type, str) or target_type not in rubric.get("target_types", {}):
            errors.append("packet target_type is not defined in its rubric")
        if packet.get("rubric_sha256") != digest(canonical_json(rubric)):
            errors.append("packet rubric hash mismatch")
    target = packet.get("target")
    if not isinstance(target, dict) or set(target) != {"kind", "root_label", "files_discovered", "files_included", "files_omitted", "excluded_directories"}:
        errors.append("invalid packet target scope")
    elif target.get("kind") not in ("file", "directory") or not isinstance(target.get("root_label"), str):
        errors.append("invalid packet target scope")
    evidence = packet.get("evidence")
    if not isinstance(evidence, list):
        errors.append("packet evidence must be an array")
    else:
        ids: set[str] = set()
        for item in evidence:
            if not isinstance(item, dict) or set(item) != {
                "id", "path", "location", "sha256", "size_bytes", "collected_at", "content_status",
                "omission_reason", "inspection", "content",
            }:
                errors.append("invalid packet evidence entry")
                continue
            ident = item.get("id")
            path = item.get("path")
            if not isinstance(ident, str) or not re.fullmatch(r"E\d{4,}", ident) or ident in ids:
                errors.append(f"invalid or duplicate evidence id: {ident}")
            else:
                ids.add(ident)
            if not isinstance(path, str) or "\\" in path or Path(path).is_absolute() or ".." in Path(path).parts or item.get("location") != path:
                errors.append(f"invalid evidence location: {path}")
            if item.get("content_status") not in ("INCLUDED", "OMITTED"):
                errors.append(f"invalid content status for {ident}")
            if item.get("content_status") == "INCLUDED" and not isinstance(item.get("content"), str):
                errors.append(f"included evidence has no text: {ident}")
            if item.get("content_status") == "OMITTED" and item.get("content") is not None:
                errors.append(f"omitted evidence must not contain text: {ident}")
            if item.get("sha256") is not None and not re.fullmatch(r"[0-9a-f]{64}", str(item["sha256"])):
                errors.append(f"invalid evidence hash: {ident}")
    if not errors:
        unsigned = dict(packet)
        stored_id = unsigned.pop("packet_id")
        if stored_id != "pkt_" + digest(canonical_json(unsigned)):
            errors.append("packet id does not match packet contents")
    return errors


def packet_snapshot_matches(packet: dict[str, Any], target: Path) -> bool:
    root = target.expanduser().resolve(strict=True)
    kind = "file" if root.is_file() else "directory" if root.is_dir() else ""
    if not kind or kind != packet["target"]["kind"]:
        return False
    evidence, scope = make_evidence(root, kind, packet["created_at"])
    return scope == packet["target"] and evidence == packet["evidence"]


def _valid_refs(refs: Any, evidence_by_id: dict[str, dict[str, Any]], require_one: bool, label: str, errors: list[str]) -> None:
    if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs) or len(refs) != len(set(refs)):
        errors.append(f"{label} evidence_refs must be a unique string array")
        return
    if require_one and not refs:
        errors.append(f"{label} must cite at least one evidence item")
    for ref in refs:
        item = evidence_by_id.get(ref)
        if item is None:
            errors.append(f"{label} cites unknown evidence: {ref}")
        elif item["content_status"] != "INCLUDED":
            errors.append(f"{label} cites evidence without included content: {ref}")


def evaluate_report(packet: dict[str, Any], report: Any) -> tuple[list[str], float | None, str | None]:
    errors: list[str] = []
    if not isinstance(report, dict) or set(report) != {
        "packet_id", "rubric_version", "target_type", "dimensions", "critical_conditions", "summary"
    }:
        return ["report must contain only the required report fields"], None, None
    rubric = packet["rubric"]
    if report.get("packet_id") != packet["packet_id"]:
        errors.append("report packet_id does not match packet")
    if report.get("rubric_version") != rubric["version"]:
        errors.append("report rubric_version does not match packet rubric")
    if report.get("target_type") != packet["target_type"]:
        errors.append("report target_type does not match packet")
    spec = rubric["target_types"][packet["target_type"]]
    evidence_by_id = {item["id"]: item for item in packet["evidence"]}
    dimensions = report.get("dimensions")
    expected_dims = {item["id"]: item for item in spec["dimensions"]}
    seen_dims: set[str] = set()
    scored: list[tuple[int, int]] = []
    required_insufficient = False
    if not isinstance(dimensions, list):
        errors.append("report dimensions must be an array")
        dimensions = []
    for item in dimensions:
        if not isinstance(item, dict) or set(item) != {"id", "status", "score", "evidence_refs", "rationale"}:
            errors.append("invalid report dimension entry")
            continue
        ident = item.get("id")
        if not isinstance(ident, str):
            errors.append(f"invalid report dimension id: {ident}")
            continue
        rule = expected_dims.get(ident)
        if rule is None or ident in seen_dims:
            errors.append(f"unknown or duplicate report dimension: {ident}")
            continue
        seen_dims.add(ident)
        status = item.get("status")
        rationale = item.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"dimension {ident} needs a rationale")
        if status == "SCORED":
            score = item.get("score")
            if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 4:
                errors.append(f"dimension {ident} score must be an integer from 0 through 4")
            else:
                scored.append((score, rule["weight"]))
            _valid_refs(item.get("evidence_refs"), evidence_by_id, True, f"dimension {ident}", errors)
        elif status == "INSUFFICIENT_EVIDENCE":
            if item.get("score") is not None:
                errors.append(f"dimension {ident} with insufficient evidence must have a null score")
            _valid_refs(item.get("evidence_refs"), evidence_by_id, False, f"dimension {ident}", errors)
            required_insufficient |= rule["applicability"] == "required"
        elif status == "NOT_APPLICABLE":
            if rule["applicability"] != "optional":
                errors.append(f"required dimension {ident} cannot be NOT_APPLICABLE")
            if item.get("score") is not None or item.get("evidence_refs") != []:
                errors.append(f"dimension {ident} marked NOT_APPLICABLE must have null score and no evidence refs")
        else:
            errors.append(f"dimension {ident} has invalid status")
    missing_dims = set(expected_dims) - seen_dims
    if missing_dims:
        errors.append(f"report is missing dimensions: {sorted(missing_dims)}")

    conditions = report.get("critical_conditions")
    expected_conditions = {item["id"]: item for item in spec["critical_conditions"]}
    seen_conditions: set[str] = set()
    triggered = False
    critical_insufficient = False
    if not isinstance(conditions, list):
        errors.append("report critical_conditions must be an array")
        conditions = []
    for item in conditions:
        if not isinstance(item, dict) or set(item) != {"id", "status", "evidence_refs", "rationale"}:
            errors.append("invalid critical condition entry")
            continue
        ident = item.get("id")
        if not isinstance(ident, str):
            errors.append(f"invalid critical condition id: {ident}")
            continue
        rule = expected_conditions.get(ident)
        if rule is None or ident in seen_conditions:
            errors.append(f"unknown or duplicate critical condition: {ident}")
            continue
        seen_conditions.add(ident)
        if not isinstance(item.get("rationale"), str) or not item["rationale"].strip():
            errors.append(f"critical condition {ident} needs a rationale")
        status = item.get("status")
        if status == "CLEAR" or status == "TRIGGERED":
            _valid_refs(item.get("evidence_refs"), evidence_by_id, True, f"critical condition {ident}", errors)
            triggered |= status == "TRIGGERED"
        elif status == "INSUFFICIENT_EVIDENCE":
            _valid_refs(item.get("evidence_refs"), evidence_by_id, False, f"critical condition {ident}", errors)
            critical_insufficient = True
        elif status == "NOT_APPLICABLE":
            if rule["applicability"] != "optional":
                errors.append(f"required critical condition {ident} cannot be NOT_APPLICABLE")
            if item.get("evidence_refs") != []:
                errors.append(f"critical condition {ident} marked NOT_APPLICABLE must have no evidence refs")
        else:
            errors.append(f"critical condition {ident} has invalid status")
    missing_conditions = set(expected_conditions) - seen_conditions
    if missing_conditions:
        errors.append(f"report is missing critical conditions: {sorted(missing_conditions)}")

    weight_total = sum(weight for _, weight in scored)
    weighted_score = round(sum(score * weight for score, weight in scored) / (4 * weight_total) * 100, 2) if weight_total else None
    if triggered:
        decision = "FAIL"
    elif critical_insufficient or required_insufficient or weighted_score is None:
        decision = "INCONCLUSIVE"
    else:
        decision = "PASS" if weighted_score >= rubric["passing_threshold"] else "FAIL"
    summary = report.get("summary")
    if not isinstance(summary, dict) or set(summary) != {"weighted_score", "decision"}:
        errors.append("report summary must contain weighted_score and decision only")
    else:
        claimed = summary.get("weighted_score")
        if weighted_score is None:
            if claimed is not None:
                errors.append("summary weighted_score must be null when no dimension has a score")
        elif isinstance(claimed, bool) or not isinstance(claimed, (int, float)) or abs(claimed - weighted_score) > 0.000001:
            errors.append(f"summary weighted_score must equal locally calculated {weighted_score}")
        if summary.get("decision") != decision:
            errors.append(f"summary decision must equal locally calculated {decision}")
    return errors, weighted_score, decision
