# Tests des améliorations items 7-11 : rapport, i18n, apprentissage, exit codes.

import json
import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import load_rules, score  # noqa: E402
import verify_bounty  # noqa: E402
from i18n import auth_label, expl_label, t  # noqa: E402


def _base(**kw):
    data = {
        "full_name": "unknown/clean-repo", "issue_number": 42,
        "issue_title": "Add a config option", "issue_state": "open",
        "issue_labels": ["bounty", "$50"], "issue_body_sample": "",
        "reward_verified": None, "repo_fork": False, "repo_stars": 120,
        "repo_archived": False, "repo_license": "MIT",
        "repo_created": "2023-01-01T10:00:00Z", "repo_pushed_at": "2026-08-10T10:00:00Z",
        "open_reward_issues": 3, "paid_history": True,
        "claims": 0, "open_pr_count": 0, "merged_pr_for_issue": False,
        "owner_login": "unknown", "owner_created": "2020-01-01T10:00:00Z",
    }
    data.update(kw)
    return data


class TestI18n(unittest.TestCase):
    """Item 11 : libellés bilingues FR/EN."""

    def test_auth_label_fr(self):
        self.assertEqual(auth_label("fr", "PAIEUR_PROUVE"), "PAYEUR PROUVÉ")
        self.assertEqual(auth_label("fr", "SANS_PREUVE"), "SANS PREUVE")

    def test_auth_label_en(self):
        self.assertEqual(auth_label("en", "PAIEUR_PROUVE"), "PROVEN PAYER")
        self.assertEqual(auth_label("en", "PIEGE"), "TRAP")

    def test_expl_label(self):
        self.assertEqual(expl_label("fr", "CONTESTE"), "CONTESTÉ")
        self.assertEqual(expl_label("en", "LIBRE"), "OPEN")

    def test_translation_retombe_sur_fr(self):
        self.assertEqual(t("de", "target"), "Cible")


class TestRapport(unittest.TestCase):
    """Item 9 : génération d'un rapport Markdown."""

    def test_rapport_ecrit(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "audit.md"
            verify_bounty.write_report(_base(), score(_base(), load_rules()), str(out), lang="fr")
            content = out.read_text(encoding="utf-8")
            self.assertIn("Rapport d'audit", content)
            self.assertIn("AUTHENTICITÉ", content)
            self.assertIn("| Check | Poids | Résultat |", content)

    def test_rapport_en(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "audit_en.md"
            verify_bounty.write_report(_base(), score(_base(), load_rules()), str(out), lang="en")
            content = out.read_text(encoding="utf-8")
            self.assertIn("Vérif'Bounty audit report", content)
            self.assertIn("AUTHENTICITY", content)


class TestApprentissage(unittest.TestCase):
    """Item 8 : --learn écrit les pièges confirmés dans known.json."""

    def setUp(self):
        self.known_path = Path(__file__).resolve().parent.parent / "known.json"
        self.original = self.known_path.read_text(encoding="utf-8")

    def tearDown(self):
        self.known_path.write_text(self.original, encoding="utf-8")

    def test_piege_confirme_appris(self):
        data = _base(
            owner_login="usinex", owner_created="2026-08-18T10:00:00Z",
            repo_stars=0, issue_number=1, issue_title="🎯 Fix: x",
            issue_labels=["opire", "$10"], paid_history=False,
        )
        result = score(data, load_rules())
        self.assertEqual(result["authenticity"]["status"], "PIEGE")
        ok = verify_bounty.learn_from_piege(data, result)
        self.assertTrue(ok)
        known = json.loads(self.known_path.read_text(encoding="utf-8"))
        self.assertIn("usinex", known["known_traps"])

    def test_payeur_jamais_appris_comme_piege(self):
        data = _base(owner_login="o2sdev")  # payeur connu
        result = score(data, load_rules())
        self.assertEqual(result["authenticity"]["status"], "PAIEUR_PROUVE")
        ok = verify_bounty.learn_from_piege(data, result)
        self.assertFalse(ok)

    def test_piege_confiance_faible_pas_appris(self):
        """Un piège à faible fiabilité ne doit pas être appris automatiquement."""
        data = _base(
            owner_login="lowconf", owner_created="2026-08-18T10:00:00Z",
            repo_stars=0, issue_number=1,
            issue_labels=["opire", "$10"], paid_history=False,
        )
        # On retire des champs critiques pour baisser la fiabilité (< 6)
        del data["issue_title"]
        del data["repo_pushed_at"]
        del data["repo_created"]
        result = score(data, load_rules())
        self.assertEqual(result["authenticity"]["status"], "PIEGE")
        self.assertLess(result["confidence"]["confidence"], 6)
        ok = verify_bounty.learn_from_piege(data, result)
        self.assertFalse(ok)


class TestQuota(unittest.TestCase):
    """Item 7 : check_quota retourne (remaining, limit) sans planter."""

    def test_quota_retourne_valeurs(self):
        remaining, limit = verify_bounty.check_quota(verbose=False)
        # peut échouer hors réseau : alors (None, None)
        self.assertIsNotNone(limit)


class TestExitCodes(unittest.TestCase):
    """Item 10 : exit codes stables (0 OK, 2 erreurs en batch)."""

    def test_exit_zero_sur_succes(self):
        import io
        import contextlib
        from unittest import mock
        fix = str(Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "o2sdev-openselfservice-issue-354.json")
        buf = io.StringIO()
        argv = ["verify_bounty.py", "--fixture", fix]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(buf):
            code = verify_bounty.main()
        self.assertEqual(code, 0)

    def test_json_embarque_version(self):
        import io
        import contextlib
        from unittest import mock
        fix = str(Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "o2sdev-openselfservice-issue-354.json")
        buf = io.StringIO()
        argv = ["verify_bounty.py", "--fixture", fix, "--json"]
        with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(buf):
            code = verify_bounty.main()
        self.assertEqual(code, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["version"], "2")


if __name__ == "__main__":
    unittest.main()
