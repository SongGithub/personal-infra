"""Accept only a complete Terraform adoption/no-op plan; never print plan values."""

import json
import sys

EXPECTED = {"cloudflare_zone.midu"}


def check(plan):
    if plan.get("errored") or plan.get("complete") is False or plan.get("deferred_changes"):
        raise ValueError("Plan is failed, incomplete or deferred.")
    resources = plan.get("resource_changes", [])
    managed = [r for r in resources if r.get("mode") == "managed"]
    if {r["address"] for r in managed} != EXPECTED or len(managed) != len(EXPECTED):
        raise ValueError("Plan must include the one managed zone; do not use -target.")
    if any(r["change"]["actions"] != ["no-op"] for r in resources):
        raise ValueError("Adoption must contain no creates, updates, deletes or replacements.")
    if any(c.get("status") != "pass" for c in plan.get("checks", [])):
        raise ValueError("Plan contains an unresolved or failed check.")


if __name__ == "__main__":
    try:
        check(json.load(sys.stdin))
    except (ValueError, KeyError, TypeError) as error:
        sys.exit(f"REFUSED: {error}")
    print("PASS: the shared zone is import-only or unchanged; no live mutations planned.")
