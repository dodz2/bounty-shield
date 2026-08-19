# Tests unitaires — les PIÈGES doivent être détectés (note >= 5.0).
# Fixtures réelles capturées via l'API GitHub le 2026-08-18.
# NOTE : seuls trapuser01 est listé dans known.json (test du forçage) ;
# les 4 autres pièges NE SONT PAS dans la liste : ils doivent être détectés
# par les 7 autres checks à eux seuls (test de robustesse).

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import load_rules, score  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


class TestPieges(unittest.TestCase):
    def test_tous_les_pieges_sont_detectes(self):
        rules = load_rules()
        checked = 0
        for f in sorted(FIXTURES.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("kind") != "piege":
                continue
            with self.subTest(fixture=f.name):
                result = score(data, rules)
                self.assertGreaterEqual(
                    result["note"], 5.0,
                    f"{f.name}: note {result['note']} alors qu'il faut >= 5.0"
                )
                self.assertEqual(result["verdict"], "PIEGE")
            checked += 1
        self.assertGreaterEqual(checked, 4, "Il faut au moins 4 fixtures pièges")

    def test_pieges_hors_liste_detectes_sans_force(self):
        """Les pièges non listés dans known.json ne doivent pas dépendre du forçage."""
        rules = load_rules()
        known = json.loads(
            (Path(__file__).resolve().parent.parent / "known.json").read_text(encoding="utf-8")
        )
        traps = [str(x).lower() for x in known.get("known_traps", [])]
        for f in sorted(FIXTURES.glob("*.json")):
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("kind") != "piege":
                continue
            owner = str(data.get("owner_login") or "").lower()
            if owner in traps:
                continue  # forçage mémoire terrain, hors scope de ce test
            with self.subTest(fixture=f.name):
                result = score(data, rules)
                self.assertIsNone(result.get("forced"), f"{f.name}: ne doit pas être forcé")
                self.assertEqual(result["verdict"], "PIEGE")


if __name__ == "__main__":
    unittest.main()