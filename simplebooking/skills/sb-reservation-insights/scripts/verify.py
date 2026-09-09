#!/usr/bin/env python3
"""
Check the arithmetic this skill has to do by hand.

`run_reservation_aggregation` returns buckets. Everything downstream of them —
ADR, coverage, numeric bands, the STLY subtraction — is arithmetic the model
performs itself, and an error there produces a table that looks right. This
script is the check that catches it.

Feed it a JSON file describing the figures you derived. It re-derives them and
exits non-zero if they do not hold. Blocking failures are [ERROR]; things worth
a second look are [WARN].

    python3 scripts/verify.py claims.json

Every block is optional: include only what the answer actually relies on.
See references/verify-contract.md for the full input shape.
"""
import json
import sys

# Currency amounts: a cent of rounding is not a discrepancy, a euro is.
MONEY_TOL = 0.01
# Coverage and shares, expressed 0..1.
RATIO_TOL = 0.005

errors: list[str] = []
warnings: list[str] = []


def _err(msg: str) -> None:
    errors.append(msg)


def _warn(msg: str) -> None:
    warnings.append(msg)


def _num(block: dict, key: str, where: str):
    """Read a required number, reporting the path when it is missing or unusable."""
    if key not in block:
        _err(f"{where}: missing '{key}'")
        return None
    v = block[key]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        _err(f"{where}: '{key}' is not a number ({v!r})")
        return None
    return float(v)


# ── 1. Revenue identity ─────────────────────────────────────────────────────
# TotalStay + TotalReservationServicesRevenue = TotalReservationRevenue (the
# JSON keys below stay total_stay/total_services/total_reservation_revenue,
# this contract's own names). When it fails, the usual cause is a figure
# copied from the wrong bucket level.
def check_revenue(block: dict, where: str) -> None:
    stay = _num(block, "total_stay", where)
    serv = _num(block, "total_services", where)
    total = _num(block, "total_reservation_revenue", where)
    if None in (stay, serv, total):
        return
    if abs(stay + serv - total) > MONEY_TOL:
        _err(f"{where}: revenue identity broken — "
             f"total_stay {stay:.2f} + total_services {serv:.2f} = {stay + serv:.2f}, "
             f"but total_reservation_revenue is {total:.2f} "
             f"(off by {stay + serv - total:+.2f})")

    channel = block.get("channel_type")
    if channel == "Indirect" and serv != 0:
        _err(f"{where}: total_services is {serv:.2f} on an Indirect perimeter, "
             f"but an OTA cannot sell booking-engine services — it must be exactly zero. "
             f"The perimeter is probably not what you think it is.")


# ── 2. ADR ──────────────────────────────────────────────────────────────────
# ADR is TotalStay over RoomNights, never TotalReservationRevenue over anything.
def check_adr(block: dict, where: str) -> None:
    stay = _num(block, "total_stay", where)
    nights = _num(block, "room_nights", where)
    claimed = _num(block, "adr", where)
    if None in (stay, nights, claimed):
        return
    if nights <= 0:
        _err(f"{where}: room_nights is {nights:.0f} — ADR is undefined, do not report one")
        return
    expected = stay / nights
    if abs(expected - claimed) > MONEY_TOL:
        _err(f"{where}: adr {claimed:.2f} does not match total_stay / room_nights "
             f"= {expected:.2f}. If you divided total_reservation_revenue instead, "
             f"the figure is inflated by the ancillary services.")


# ── 3. Coverage ─────────────────────────────────────────────────────────────
# Unpopulated rows do not appear in keyword buckets, so coverage is
# sum(buckets) / parent. A ranking without it describes an unknown minority.
def check_coverage(block: dict, where: str) -> None:
    parent = _num(block, "parent_count", where)
    buckets = block.get("buckets")
    if parent is None:
        return
    if not isinstance(buckets, list) or not buckets:
        _err(f"{where}: 'buckets' must be a non-empty list of counts")
        return
    try:
        covered = float(sum(buckets))
    except TypeError:
        _err(f"{where}: 'buckets' must contain numbers only")
        return
    if parent <= 0:
        _err(f"{where}: parent_count is {parent:.0f} — nothing to compare against")
        return
    if covered > parent + 0.5:
        _err(f"{where}: buckets sum to {covered:.0f} but the parent holds {parent:.0f}. "
             f"On a non-additive facet (RoomType, RatePlan, Offer) this is expected and "
             f"coverage is not the right reading — use ranking and ADR instead.")
        return

    actual = covered / parent
    if (claimed := block.get("claimed_coverage")) is not None:
        if abs(actual - float(claimed)) > RATIO_TOL:
            _err(f"{where}: stated coverage {float(claimed):.1%} but buckets over parent "
                 f"is {actual:.1%}")
    if actual < 0.25:
        _warn(f"{where}: coverage is {actual:.1%} — any percentage split here describes "
              f"a minority of the business. Say so in the answer.")


# ── 4. Numeric bands ────────────────────────────────────────────────────────
# There is no histogram: bands are separate calls, and they only mean something
# if they are exhaustive and disjoint.
def check_bands(block: dict, where: str) -> None:
    total = _num(block, "period_total", where)
    bands = block.get("bands")
    if total is None:
        return
    if not isinstance(bands, list) or not bands:
        _err(f"{where}: 'bands' must be a non-empty list")
        return

    parsed = []
    for i, b in enumerate(bands):
        if not isinstance(b, dict):
            _err(f"{where}: band {i} is not an object")
            return
        lo, hi = b.get("from"), b.get("to")
        cnt = b.get("count")
        label = b.get("label", f"band {i}")
        if not isinstance(cnt, (int, float)) or isinstance(cnt, bool):
            _err(f"{where}: band '{label}' has no numeric count")
            return
        if lo is None or not isinstance(lo, (int, float)):
            _err(f"{where}: band '{label}' has no numeric 'from'")
            return
        hi = float("inf") if hi is None else hi
        if not isinstance(hi, (int, float)):
            _err(f"{where}: band '{label}' has a non-numeric 'to'")
            return
        if float(hi) < float(lo):
            _err(f"{where}: band '{label}' runs backwards ({lo} to {hi})")
            return
        parsed.append((float(lo), float(hi), float(cnt), label))

    covered = sum(p[2] for p in parsed)
    if abs(covered - total) > 0.5:
        _err(f"{where}: bands hold {covered:.0f} reservations but the period has "
             f"{total:.0f} — they are not exhaustive "
             f"({total - covered:+.0f} unaccounted for)")

    # Bounds are inclusive on both ends, so the next band must start after the
    # previous one ends. Touching bounds double-count the boundary value.
    parsed.sort(key=lambda p: p[0])
    for (lo1, hi1, _, l1), (lo2, hi2, _, l2) in zip(parsed, parsed[1:]):
        if lo2 <= hi1:
            _err(f"{where}: bands '{l1}' ({lo1:g}–{hi1:g}) and '{l2}' ({lo2:g}–{hi2:g}) "
                 f"overlap — a reservation at {lo2:g} is counted twice")
        elif lo2 > hi1 + 1:
            _warn(f"{where}: gap between '{l1}' (ends {hi1:g}) and '{l2}' (starts {lo2:g}) "
                  f"— values in between fall outside every band")


# ── 5. STLY ─────────────────────────────────────────────────────────────────
# On-the-books as it stood a year ago = booked by the snapshot minus cancelled
# by the snapshot. Filtering Active on last year is the classic error.
def check_stly(block: dict, where: str) -> None:
    gross = _num(block, "booked_by_snapshot", where)
    cancelled = _num(block, "cancelled_by_snapshot", where)
    claimed = _num(block, "stly_otb", where)
    if None in (gross, cancelled, claimed):
        return
    if cancelled > gross:
        _err(f"{where}: cancelled_by_snapshot {cancelled:.0f} exceeds "
             f"booked_by_snapshot {gross:.0f} — the two queries do not share a perimeter")
        return
    expected = gross - cancelled
    if abs(expected - claimed) > 0.5:
        _err(f"{where}: stly_otb {claimed:.0f} does not equal "
             f"booked {gross:.0f} − cancelled {cancelled:.0f} = {expected:.0f}")

    snap, today = block.get("snapshot_date"), block.get("today")
    if snap and today:
        try:
            sy, sm, sd = (int(x) for x in str(snap).split("-"))
            ty, tm, td = (int(x) for x in str(today).split("-"))
        except ValueError:
            _err(f"{where}: dates must be YYYY-MM-DD (got {snap!r} and {today!r})")
        else:
            if (sm, sd) != (tm, td) or ty - sy != 1:
                _err(f"{where}: snapshot {snap} is not exactly one year before {today}. "
                     f"A misaligned snapshot barely moves the comparison percentages "
                     f"while badly distorting the residual pick-up estimate.")


# ── 6. Currency ─────────────────────────────────────────────────────────────
# Amounts are summed across currencies with no signal in the output.
def check_currency(block: dict, where: str) -> None:
    codes = block.get("currencies")
    if not isinstance(codes, list):
        _err(f"{where}: 'currencies' must be a list of the codes the perimeter returned")
        return
    distinct = sorted({str(c) for c in codes})
    if len(distinct) > 1 and block.get("amounts_summed", True):
        _err(f"{where}: amounts were summed over {len(distinct)} currencies "
             f"({', '.join(distinct)}). The total is meaningless — filter CurrencyCode, "
             f"or compare shares instead of amounts.")


CHECKS = {
    "revenue":  check_revenue,
    "adr":      check_adr,
    "coverage": check_coverage,
    "bands":    check_bands,
    "stly":     check_stly,
    "currency": check_currency,
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
        # A block may be one object or a list of them, for several perimeters.
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
              f"Do not publish these numbers.")
        return 1
    print(f"\n{ran} check(s) passed"
          + (f", {len(warnings)} warning(s) to mention in the answer." if warnings
             else ". Nothing to flag."))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
