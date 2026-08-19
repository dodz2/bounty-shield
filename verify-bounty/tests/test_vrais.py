# Tests unitaires — les VRAIS bounties doivent passer (note <= 2.0).
# Fixtures réelles : openselfservice #354 (payé) et trovu #329 (reward Opire).
# Ces deux dépôts sont dans known.json (payeurs fiables) : le test vérifie que
# le forçage mémoire terrain les protège malgré les autres checks.

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import load_rules, score  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


class TestVrais(unittest.TestCase):
    def test_les_vrais_bounties_passent(self):
        rules = load_rules()
        checked = 0
        for f in sorted(FIXTURES.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("kind") != "vrai":
                continue
            with self.subTest(fixture=f.name):
                result = score(data, rules)
                self.assertLessEqual(
                    result["note"], 2.0,
                    f"{f.name}: note {result['note']} alors qu'il faut <= 2.0"
                )
                self.assertEqual(result["verdict"], "VRAI")
            checked += 1
        self.assertGreaterEqual(checked, 2, "Il faut au moins 2 fixtures vrais")


if __name__ == "__main__":
    unittest.main()