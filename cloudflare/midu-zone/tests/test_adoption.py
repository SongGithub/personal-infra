import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("adoption", Path(__file__).parents[1] / "check_adoption.py")
adoption = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adoption)


class AdoptionGuardTest(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "complete": True,
            "resource_changes": [
                {"address": a, "mode": "managed", "change": {"actions": ["no-op"], "importing": {"id": "existing"}}}
                for a in sorted(adoption.EXPECTED)
            ],
        }

    def test_accepts_complete_import(self):
        adoption.check(self.plan)

    def test_accepts_subsequent_noop(self):
        for resource in self.plan["resource_changes"]:
            resource["change"].pop("importing")
        adoption.check(self.plan)

    def test_rejects_every_mutation(self):
        for actions in (["create"], ["update"], ["delete"], ["delete", "create"], ["create", "delete"]):
            with self.subTest(actions=actions), self.assertRaises(ValueError):
                plan = copy.deepcopy(self.plan)
                plan["resource_changes"][0]["change"]["actions"] = actions
                adoption.check(plan)

    def test_rejects_partial_plan(self):
        self.plan["resource_changes"].pop()
        with self.assertRaises(ValueError):
            adoption.check(self.plan)

    def test_rejects_failed_or_deferred_plan(self):
        for extra in ({"errored": True}, {"complete": False}, {"deferred_changes": [{}]}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                adoption.check(self.plan | extra)

    def test_rejects_failed_or_unknown_check(self):
        for status in ("fail", "unknown", "error"):
            with self.subTest(status=status), self.assertRaises(ValueError):
                adoption.check(self.plan | {"checks": [{"status": status}]})


if __name__ == "__main__":
    unittest.main()
