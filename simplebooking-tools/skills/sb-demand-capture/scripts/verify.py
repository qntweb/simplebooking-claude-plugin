#!/usr/bin/env python3
"""
Check the arithmetic of a cross-lens comparison before it goes into an answer.

sb-demand-capture never touches raw MCP data: it takes one number from sb-revenue-lens
and one from sb-reservation-insights and computes a gap, a share difference or an
intersection between them. That arithmetic is exactly the kind of thing that looks right
in a sentence and is wrong in the delta. This script re-derives it and exits non-zero if
it does not hold.

    python3 scripts/verify.py claims.json

Every block is optional: include only what the answer actually relies on. Blocks map to
the cross-lenses in references/cross-lenses.md — "gap" for X1/X3/X6, "share" for X5,
"intersection" for X2. A block may be one object or a list of them.
"""
import json
import sys

# Percentage points / ratios: a rounding sliver is not a discrepancy, a full point is.
PP_TOL = 0.05
RATIO_TOL = 0.005

errors: list[str] = []
warnings: list[str] = []


def _err(msg: str) -> None:
    errors.append(msg)


def _warn(msg: str) -> None:
    warnings.append(msg)


def _num(block: dict, key: str, where: str):
    if key not in block:
        _err(f"{where}: missing '{key}'")
        return None
    v = block[key]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        _err(f"{where}: '{key}' is not a number ({v!r})")
        return None
    return float(v)


def _classify(gap_pp: float, aligned_pp: float, notable_pp: float) -> str:
    mag = abs(gap_pp)
    if mag <= aligned_pp:
        return "in linea"
    if mag <= notable_pp:
        return "da verificare"
    return "scostamento marcato"


# ── gap — X1 (pace), X3 (prezzo/parità), X6 (pacing) ────────────────────────
# gap_pp = sales_side_pct - demand_side_pct (same sign convention across the three lenses:
# demand_side_pct is L1/L2 growth for X1, parity price for X3, demand daysAhead for X6).
def check_gap(block: dict, where: str) -> None:
    demand_side = _num(block, "demand_side_pct", where)
    sales_side = _num(block, "sales_side_pct", where)
    claimed_gap = _num(block, "claimed_gap_pp", where)
    if None in (demand_side, sales_side, claimed_gap):
        return
    expected_gap = sales_side - demand_side
    if abs(expected_gap - claimed_gap) > PP_TOL:
        _err(f"{where}: claimed_gap_pp {claimed_gap:.2f} does not match "
             f"sales_side_pct {sales_side:.2f} - demand_side_pct {demand_side:.2f} "
             f"= {expected_gap:.2f}")
        return

    aligned_pp = _num(block, "aligned_pp", where) if "aligned_pp" in block else 5.0
    notable_pp = _num(block, "notable_pp", where) if "notable_pp" in block else 15.0
    if aligned_pp is None or notable_pp is None:
        return
    if aligned_pp >= notable_pp:
        _err(f"{where}: aligned_pp ({aligned_pp}) must be smaller than notable_pp ({notable_pp})")
        return

    expected_class = _classify(claimed_gap, aligned_pp, notable_pp)
    claimed_class = block.get("claimed_classification")
    if claimed_class is not None and claimed_class != expected_class:
        _err(f"{where}: claimed_classification '{claimed_class}' but the gap "
             f"{claimed_gap:+.2f}pp classifies as '{expected_class}' "
             f"(aligned<= {aligned_pp}pp, notable<= {notable_pp}pp)")

    if abs(claimed_gap) <= aligned_pp and abs(demand_side) > 20 and abs(sales_side) > 20 \
            and (demand_side < 0) == (sales_side < 0):
        _warn(f"{where}: demand and sales move together in the same direction "
              f"(demand {demand_side:+.1f}%, sales {sales_side:+.1f}%) — likely "
              f"seasonality, say so before flagging a problem")

    # A thin STLY base can produce a gap that is arithmetically correct but practically
    # meaningless — a swing of a handful of bookings on a thin base. Below this floor, the
    # percentage must be reported alongside the raw counts, never alone.
    base_n = block.get("sales_base_n")
    if base_n is not None:
        base_n = _num(block, "sales_base_n", where)
        if base_n is not None:
            min_base_n = float(block.get("min_gap_base_n", 20))
            if base_n < min_base_n:
                _warn(f"{where}: sales_side_pct is computed on a base of only "
                      f"{base_n:.0f} (below the {min_base_n:.0f} floor) — report the raw "
                      f"counts alongside the percentage, a swing of a few bookings "
                      f"produces a large, unstable delta on a base this thin")

    # The RoomNights basis and the reservationsCount basis can classify the same week
    # differently ("to verify" vs "marked deviation"). When a caller checks both, surface
    # disagreement instead of silently reporting only the more convenient one.
    other_class = block.get("other_basis_classification")
    if other_class is not None and other_class != expected_class:
        _warn(f"{where}: classifies as '{expected_class}' on this basis but "
              f"'{other_class}' on the other basis ({block.get('other_basis_label', 'n/a')}) "
              f"— report both bases and the disagreement, do not pick one silently")

    # X6's YoY-delta fix assumes the structural search-vs-booking population bias
    # (sales_side / demand_side, in absolute terms, before taking deltas) stays roughly
    # constant year over year. That assumption can hold tightly on one property and drift
    # a lot on another — same corrected formula, same clean arithmetic, very different
    # reliability of the underlying assumption. When both ratios are supplied, flag a large
    # drift so the classification is read with the right amount of caution instead of at
    # face value.
    ratio_a = block.get("basis_ratio_a")
    ratio_b = block.get("basis_ratio_b")
    if ratio_a is not None and ratio_b is not None:
        ratio_a = _num(block, "basis_ratio_a", where)
        ratio_b = _num(block, "basis_ratio_b", where)
        if ratio_a is not None and ratio_b is not None and ratio_a != 0:
            drift_pct = (ratio_b / ratio_a - 1) * 100
            max_drift_pct = float(block.get("max_ratio_drift_pct", 15))
            if abs(drift_pct) > max_drift_pct:
                _warn(f"{where}: the absolute sales/demand ratio moved {drift_pct:+.1f}% "
                      f"between the two periods ({ratio_a:.2f}x -> {ratio_b:.2f}x) — the "
                      f"YoY-cancellation this lens relies on assumes that ratio is stable, "
                      f"which does not hold cleanly here. Report the gap as a hypothesis to "
                      f"verify, not a confirmed reading.")


# ── share — X5 (mercati e segmenti) ─────────────────────────────────────────
def check_share(block: dict, where: str) -> None:
    demand_share = _num(block, "demand_share_pct", where)
    sales_share = _num(block, "sales_share_pct", where)
    claimed_gap = _num(block, "claimed_gap_pp", where)
    if None in (demand_share, sales_share, claimed_gap):
        return
    if not (0 <= demand_share <= 100):
        _err(f"{where}: demand_share_pct {demand_share} is not a percentage in [0,100]")
    if not (0 <= sales_share <= 100):
        _err(f"{where}: sales_share_pct {sales_share} is not a percentage in [0,100]")
    expected_gap = sales_share - demand_share
    if abs(expected_gap - claimed_gap) > PP_TOL:
        _err(f"{where}: claimed_gap_pp {claimed_gap:.2f} does not match "
             f"sales_share_pct {sales_share:.2f} - demand_share_pct {demand_share:.2f} "
             f"= {expected_gap:.2f}")

    coverage = block.get("sales_field_coverage")
    if coverage is not None:
        try:
            coverage = float(coverage)
        except (TypeError, ValueError):
            _err(f"{where}: sales_field_coverage must be a number in [0,1]")
        else:
            min_coverage = float(block.get("min_field_coverage", 0.25))
            if coverage < min_coverage:
                _warn(f"{where}: real-side field coverage is {coverage:.1%}, below the "
                      f"{min_coverage:.0%} floor — this share compares a minority of "
                      f"real bookings against the full destination demand. Say so.")


# ── intersection — X2 (freni alla conversione) ──────────────────────────────
# A confirmed brake is a date flagged by BOTH the market side (L3 restrictions) and the
# real side (low sales / high cancellations). Dates in only one set are a hypothesis.
def check_intersection(block: dict, where: str) -> None:
    market_dates = block.get("market_flagged_dates")
    sales_dates = block.get("sales_flagged_dates")
    claimed_confirmed = block.get("claimed_confirmed_dates")
    if not isinstance(market_dates, list) or not isinstance(sales_dates, list):
        _err(f"{where}: 'market_flagged_dates' and 'sales_flagged_dates' must both be lists")
        return
    if claimed_confirmed is None:
        _err(f"{where}: missing 'claimed_confirmed_dates'")
        return
    if not isinstance(claimed_confirmed, list):
        _err(f"{where}: 'claimed_confirmed_dates' must be a list")
        return

    expected = sorted(set(market_dates) & set(sales_dates))
    claimed_sorted = sorted(set(claimed_confirmed))
    if claimed_sorted != expected:
        _err(f"{where}: claimed_confirmed_dates {claimed_sorted} does not match the "
             f"intersection of market- and sales-flagged dates {expected}")
        return

    market_only = sorted(set(market_dates) - set(sales_dates))
    sales_only = sorted(set(sales_dates) - set(market_dates))
    if market_only or sales_only:
        _warn(f"{where}: {len(market_only)} date(s) flagged by the market side only and "
              f"{len(sales_only)} by the real-sales side only — these are hypotheses, "
              f"not confirmed brakes, keep them labeled as such")


CHECKS = {
    "gap": check_gap,
    "share": check_share,
    "intersection": check_intersection,
}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as fh:
            claims = json.load(fh)
    except FileNotFoundError:
        print(f"ERROR: {argv[1]} not found", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: {argv[1]} is not valid JSON — {exc}", file=sys.stderr)
        return 2

    if not isinstance(claims, dict):
        print("ERROR: the top level must be an object keyed by check name", file=sys.stderr)
        return 2

    unknown = sorted(set(claims) - set(CHECKS))
    if unknown:
        print(f"ERROR: unknown block(s): {', '.join(unknown)}. "
              f"Valid: {', '.join(CHECKS)}", file=sys.stderr)
        return 2
    if not claims:
        print("ERROR: nothing to verify — the file declares no blocks", file=sys.stderr)
        return 2

    ran = 0
    for name, fn in CHECKS.items():
        if name not in claims:
            continue
        block = claims[name]
        items = block if isinstance(block, list) else [block]
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                _err(f"{name}[{i}]: expected an object")
                continue
            where = item.get("label") or (f"{name}[{i}]" if len(items) > 1 else name)
            fn(item, where)
            ran += 1

    for w in warnings:
        print(f"[WARN]  {w}")
    for e in errors:
        print(f"[ERROR] {e}")

    if errors:
        print(f"\n{len(errors)} blocking problem(s) across {ran} check(s). "
              f"Do not publish this comparison.")
        return 1
    print(f"\n{ran} check(s) passed"
          + (f", {len(warnings)} warning(s) to mention in the answer." if warnings
             else ". Nothing to flag."))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
