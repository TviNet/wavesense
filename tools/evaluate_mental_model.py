#!/usr/bin/env python3
import argparse
import json
import os
import re
import statistics
from pathlib import Path
from typing import Dict, List, Tuple, Optional


ARTIFACTS_DIR = Path("temp_artifacts")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def parse_wave_table(path: Path) -> Optional[Dict[str, List[int]]]:
    """Parse vcdcat-like plaintext table into timeseries per signal.

    Returns a dict mapping short signal names (clk, rst, en, count) to lists aligned by time rows.
    Expects header with index-to-signal mapping, then rows of values.
    Count is parsed as integer (hex accepted). clk/rst/en parsed as 0/1.
    """
    txt = read_text(path)
    if not txt:
        return None

    lines = [ln.rstrip() for ln in txt.splitlines() if ln.strip()]
    # Expect header mapping lines like: "1 TOP.clk"
    idx_to_sig: Dict[int, str] = {}
    for ln in lines:
        if re.match(r"^\d+\s+TOP[.]", ln):
            idx, name = ln.split(None, 1)
            try:
                idx_to_sig[int(idx)] = name.strip()
            except ValueError:
                pass
        # End of header when we see the separator
        if set(ln.strip()) == set("="):
            break

    # Map desired signals to column indices
    sig_to_idx: Dict[str, int] = {}
    for idx, full in idx_to_sig.items():
        if full.endswith(".clk"):
            sig_to_idx["clk"] = idx
        elif full.endswith(".rst"):
            sig_to_idx["rst"] = idx
        elif full.endswith(".en"):
            sig_to_idx["en"] = idx
        elif re.search(r"[.]count(\[7:0\])?$", full):
            sig_to_idx["count"] = idx

    # Find the header separator line index
    try:
        sep_idx = next(i for i, ln in enumerate(lines) if set(ln.strip()) == set("="))
    except StopIteration:
        return None

    # Identify the column order line immediately before the separator
    header_cols_line = lines[sep_idx - 1]
    col_indices: List[int] = [int(x) for x in header_cols_line.split() if x.isdigit()]
    if not col_indices:
        return None

    # Data rows follow separator; expect columns separated by whitespace
    data_rows = lines[sep_idx + 1 :]
    series: Dict[str, List[int]] = {k: [] for k in sig_to_idx}

    for ln in data_rows:
        parts = ln.split()
        if len(parts) < len(col_indices):
            # Skip malformed rows
            continue
        # Map column number (from header) to the textual value in this row
        idx_to_val: Dict[int, str] = {}
        for pos, idx in enumerate(col_indices):
            if pos >= len(parts):
                continue
            idx_to_val[idx] = parts[pos]

        # Extract selected signals
        for sig, idx in sig_to_idx.items():
            val_txt = idx_to_val.get(idx)
            if val_txt is None:
                continue
            try:
                if sig == "count":
                    # Count appears in hex without 0x prefix sometimes; handle hex and decimal
                    v = int(val_txt, 16) if re.search(r"^[0-9a-fA-F]+$", val_txt) else int(val_txt)
                else:
                    v = int(val_txt)
            except ValueError:
                continue
            series[sig].append(v)

    return series


def rising_edges(clk: List[int]) -> List[int]:
    edges = []
    for i in range(1, len(clk)):
        if clk[i - 1] == 0 and clk[i] == 1:
            edges.append(i)
    return edges


def count_toggles(values: List[int]) -> int:
    return sum(1 for i in range(1, len(values)) if values[i] != values[i - 1])


def check_reset_clears(series: Dict[str, List[int]]) -> bool:
    if not all(k in series for k in ("clk", "rst", "count")):
        return False
    edges = rising_edges(series["clk"])
    ok = True
    saw_case = False
    for i in edges:
        if i < len(series["rst"]) and series["rst"][i] == 1:
            saw_case = True
            if i >= len(series["count"]) or series["count"][i] != 0:
                ok = False
                break
    return ok and saw_case


def check_enable_gates(series: Dict[str, List[int]]) -> bool:
    if not all(k in series for k in ("clk", "en", "rst", "count")):
        return False
    edges = rising_edges(series["clk"])
    ok = True
    saw_case = False
    prev_count = None
    for i in edges:
        if series["rst"][i] == 0 and series["en"][i] == 0:
            saw_case = True
            if prev_count is not None and i < len(series["count"]):
                if series["count"][i] != prev_count:
                    ok = False
                    break
        if i < len(series["count"]):
            prev_count = series["count"][i]
    return ok and saw_case


def check_increment_by_one(series: Dict[str, List[int]], width: int = 8) -> bool:
    if not all(k in series for k in ("clk", "en", "rst", "count")):
        return False
    mod = 1 << width
    edges = rising_edges(series["clk"])
    ok = True
    saw_case = False
    prev_val = None
    for i in edges:
        if series["rst"][i] == 0 and series["en"][i] == 1:
            if prev_val is not None and i < len(series["count"]):
                saw_case = True
                expect = (prev_val + 1) % mod
                if series["count"][i] != expect:
                    ok = False
                    break
        if i < len(series["count"]):
            prev_val = series["count"][i]
    return ok and saw_case


def check_wraparound(series: Dict[str, List[int]], width: int = 8) -> bool:
    if "count" not in series:
        return False
    max_val = (1 << width) - 1
    vals = series["count"]
    for i in range(1, len(vals)):
        if vals[i - 1] == max_val and vals[i] == 0:
            return True
    return False


def check_reset_priority(series: Dict[str, List[int]]) -> bool:
    if not all(k in series for k in ("clk", "rst", "en", "count")):
        return False
    edges = rising_edges(series["clk"])
    saw_case = False
    for i in edges:
        if series["rst"][i] == 1 and series["en"][i] == 1:
            saw_case = True
            if series["count"][i] != 0:
                return False
    return saw_case


def check_mid_stream_reset(series: Dict[str, List[int]]) -> bool:
    if not all(k in series for k in ("clk", "rst", "count")):
        return False
    edges = rising_edges(series["clk"])
    # Find a posedge where rst goes high for one edge and then low
    for i in range(1, len(edges) - 1):
        e_prev, e, e_next = edges[i - 1], edges[i], edges[i + 1]
        if series["rst"][e_prev] == 0 and series["rst"][e] == 1 and series["rst"][e_next] == 0:
            # Count at e must be 0, and then should resume incrementing or at least change thereafter
            if series["count"][e] != 0:
                continue
            return True
    return False


UNCERTAINTY_WORDS = {
    "maybe",
    "likely",
    "probably",
    "might",
    "could",
    "unsure",
    "assume",
    "guess",
    "appears",
}


def extract_features_and_refs(mental_model_md: str) -> List[Dict[str, object]]:
    features: List[Dict[str, object]] = []
    for line in mental_model_md.splitlines():
        if line.strip().startswith("- "):
            text = line.strip()[2:]
            refs = re.findall(r"waves/[\w\-]+[.]txt", line)
            features.append({"text": text, "refs": refs})
    return features


def classify_claim(text: str) -> List[str]:
    t = text.lower()
    cats: List[str] = []
    if "wrap" in t or "rollover" in t or "roll over" in t:
        cats.append("wraparound")
    if "+1" in t or "increment" in t or "increase by one" in t:
        cats.append("increment")
    if "enable" in t or "en=0" in t or "gate" in t:
        cats.append("enable_gating")
    if "priority" in t:
        cats.append("reset_priority")
    if "mid-stream" in t or "mid stream" in t:
        cats.append("mid_stream_reset")
    if "reset" in t:
        cats.append("reset_clears")
    return list(dict.fromkeys(cats))  # dedupe, keep order


def evaluate(artifacts_dir: Path) -> Dict[str, object]:
    # Load artifacts
    mm_path = artifacts_dir / "mental_model.md"
    hyp_path = artifacts_dir / "hypotheses.md"
    run_cmd_path = artifacts_dir / "run.cmd"
    waves_dir = artifacts_dir / "waves"

    mm = read_text(mm_path)
    hyp = read_text(hyp_path)

    features = extract_features_and_refs(mm)
    total_features = len(features)

    # Evidence linkage
    features_with_refs = sum(1 for f in features if f["refs"])
    referenced_files = sorted({r for f in features for r in f["refs"]})
    missing_refs = [r for r in referenced_files if not (artifacts_dir / r).exists()]

    # Hypotheses resolution
    validated = len(re.findall(r"VALIDATED", hyp))
    partial = len(re.findall(r"PARTIALLY", hyp))
    not_tested = len(re.findall(r"NOT TESTED", hyp))
    total_cps = validated + partial + not_tested

    # Uncertainty/clarity
    tokens = re.findall(r"\b\w+\b", mm.lower())
    uncertain = sum(1 for t in tokens if t in UNCERTAINTY_WORDS)
    uncertainty_ratio = (uncertain / max(len(tokens), 1))

    # Wave diversity and basic signal coverage
    used_wave_files = [artifacts_dir / r for r in referenced_files]
    parsed_series: Dict[str, Dict[str, List[int]]] = {}
    all_signals: set = set()
    toggles_per_signal: List[int] = []
    for wf in used_wave_files:
        series = parse_wave_table(wf)
        if series:
            parsed_series[wf.name] = series
            all_signals.update(series.keys())
            for sig, vals in series.items():
                toggles_per_signal.append(count_toggles(vals))

    wave_metrics = {
        "referenced_wave_files": [Path(r).name for r in referenced_files],
        "missing_references": missing_refs,
        "unique_signals_seen": sorted(list(all_signals)),
        "avg_signal_toggles": (statistics.mean(toggles_per_signal) if toggles_per_signal else 0.0),
    }

    # Behavioral verification against evidence (heuristic)
    claim_checks = {
        "reset_clears": check_reset_clears,
        "enable_gating": check_enable_gates,
        "increment": check_increment_by_one,
        "wraparound": check_wraparound,
        "reset_priority": check_reset_priority,
        "mid_stream_reset": check_mid_stream_reset,
    }

    verified_claims = 0
    verifiable_claims = 0
    claim_results: List[Dict[str, object]] = []
    for f in features:
        cats = classify_claim(str(f["text"]))
        # Evaluate each category across all referenced waves for this feature
        for cat in cats:
            verifiable_claims += 1
            passed_any = False
            for r in f["refs"]:
                series = parsed_series.get(Path(r).name)
                if not series:
                    continue
                ok = claim_checks[cat](series)
                if ok:
                    passed_any = True
                    break
            verified_claims += 1 if passed_any else 0
            claim_results.append({
                "feature_text": f["text"],
                "category": cat,
                "verified": passed_any,
                "refs": f["refs"],
            })

    # Structural completeness
    structural = {
        "features": total_features,
        "features_with_evidence": features_with_refs,
        "evidence_link_rate": (features_with_refs / total_features) if total_features else 0.0,
        "run_cmd_present": run_cmd_path.exists(),
    }

    # Hypothesis resolution
    hypothesis = {
        "total_coverpoints": total_cps,
        "validated": validated,
        "partial": partial,
        "not_tested": not_tested,
        "validated_ratio": (validated / total_cps) if total_cps else 0.0,
    }

    # Aggregated quality index (tunable weights)
    weights = {
        "structural": 0.2,
        "behavioral": 0.5,
        "hypothesis": 0.2,
        "clarity": 0.1,
    }
    structural_score = structural["evidence_link_rate"] * (1.0 if structural["run_cmd_present"] else 0.8)
    behavioral_score = (verified_claims / verifiable_claims) if verifiable_claims else 0.0
    hypothesis_score = hypothesis["validated_ratio"]
    clarity_score = max(0.0, 1.0 - 5.0 * uncertainty_ratio)  # penalize uncertainty more strongly

    quality_index = (
        weights["structural"] * structural_score
        + weights["behavioral"] * behavioral_score
        + weights["hypothesis"] * hypothesis_score
        + weights["clarity"] * clarity_score
    )

    return {
        "structural": structural,
        "wave_metrics": wave_metrics,
        "behavioral_claim_checks": claim_results,
        "behavioral_verified_rate": behavioral_score,
        "hypothesis": hypothesis,
        "clarity": {"uncertainty_ratio": uncertainty_ratio},
        "quality_index": quality_index,
    }


def render_markdown(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# Mental Model Evaluation Report")
    lines.append("")
    lines.append(f"Quality Index: {report['quality_index']:.3f}")
    lines.append("")
    s = report["structural"]
    lines.append("## Structural")
    lines.append(f"- Features: {s['features']}")
    lines.append(f"- Features with evidence: {s['features_with_evidence']} ({s['evidence_link_rate']:.2%})")
    lines.append(f"- run.cmd present: {s['run_cmd_present']}")
    lines.append("")

    lines.append("## Hypotheses")
    h = report["hypothesis"]
    lines.append(
        f"- Coverpoints: {h['total_coverpoints']} | Validated: {h['validated']} | Partial: {h['partial']} | Not tested: {h['not_tested']}"
    )
    lines.append(f"- Validated ratio: {h['validated_ratio']:.2%}")
    lines.append("")

    lines.append("## Wave Metrics")
    w = report["wave_metrics"]
    lines.append(f"- Referenced waves: {', '.join(w['referenced_wave_files']) if w['referenced_wave_files'] else 'None'}")
    if w["missing_references"]:
        lines.append(f"- Missing references: {', '.join(w['missing_references'])}")
    lines.append(f"- Unique signals seen: {', '.join(w['unique_signals_seen']) if w['unique_signals_seen'] else 'None'}")
    lines.append(f"- Avg signal toggles: {w['avg_signal_toggles']:.2f}")
    lines.append("")

    lines.append("## Behavioral Checks")
    lines.append(f"- Verified rate: {report['behavioral_verified_rate']:.2%}")
    for cr in report["behavioral_claim_checks"]:
        status = "PASS" if cr["verified"] else "FAIL"
        refs = ", ".join(cr["refs"]) if cr["refs"] else "(no refs)"
        lines.append(f"- [{status}] {cr['category']}: {cr['feature_text']} | refs: {refs}")
    lines.append("")

    lines.append("## Clarity")
    lines.append(f"- Uncertainty ratio: {report['clarity']['uncertainty_ratio']:.3%}")
    lines.append("")

    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Evaluate mental_model.md and related artifacts.")
    ap.add_argument("--artifacts", default=str(ARTIFACTS_DIR), help="Path to temp_artifacts directory")
    ap.add_argument("--out-json", default=None, help="Path to write JSON report (default: temp_artifacts/eval_report.json)")
    ap.add_argument("--out-md", default=None, help="Path to write Markdown report (default: temp_artifacts/eval_report.md)")
    args = ap.parse_args()

    art_dir = Path(args.artifacts)
    report = evaluate(art_dir)

    out_json = Path(args.out_json) if args.out_json else (art_dir / "eval_report.json")
    out_md = Path(args.out_md) if args.out_md else (art_dir / "eval_report.md")

    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
