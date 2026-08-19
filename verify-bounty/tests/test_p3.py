# Tests des améliorations P3 : cas limites, rapport de confiance, veille multi-repos.

import json
import unittest
from pathlib import Path
from unittest import mock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import load_rules, score  # noqa: E402
import verify_bounty  # noqa: E402
from tools import veille  # noqa: E402


class TestCasLimites(unittest.TestCase):
    """P3-9 : cas limites construits (synthetiques, marques comme tels)."""

    BASE = {
        "full_name": "unknown/legit-looking",
        "issue_number": 45,
        "issue_title": "Add dark mode support",
        "issue_labels": ["feature"],
        "issue_body_sample": "",
        "reward_verified": None,
        "repo_fork": False,
        "repo_stars": 100,
        "repo_archived": False,
        "repo_license": "MIT",
        "repo_created": "2024-01-01T10:00:00Z",
        "paid_history": True,
        "owner_login": "unknown",
        "owner_created": "2019-04-01T10:00:00Z",
    }

    def test_vrai_frele_petit_montant_passe_vrai(self):
        """Vrai jeune dépôt légitime : compte ancien, quelques étoiles = VRAI."""
        data = dict(self.BASE)
        data.update({"repo_stars": 3, "issue_number": 2, "issue_labels": ["💰 Reward"],
                     "issue_body_sample": "/reward 15", "paid_history": False})
        result = score(data, load_rules())
        self.assertEqual(result["verdict"], "VRAI", result)

    def test_vrai_0_etoile_jamais_piege(self):
        """Un vrai dépôt à 0 étoile reste au pire À VÉRIFIER, jamais PIÈGE."""
        data = dict(self.BASE)
        data.update({"repo_stars": 0, "issue_number": 2, "issue_labels": ["💰 Reward"],
                     "issue_body_sample": "/reward 15", "paid_history": False})
        result = score(data, load_rules())
        self.assertNotEqual(result["verdict"], "PIEGE", result)

    def test_piege_sophistique_detecte(self):
        """Piège sophistiqué : montant dans le corps, titre normal, mais taille/cadence suspectes."""
        data = dict(self.BASE)
        data.update({"owner_created": "2026-08-17T10:00:00Z", "repo_created": "2026-08-17T11:00:00Z",
                     "repo_stars": 0, "issue_number": 1, "issue_labels": ["opire", "$10"]})
        result = score(data, load_rules())
        self.assertEqual(result["verdict"], "PIEGE", result)


class TestConfidence(unittest.TestCase):
    """P3-10 : build_confidence doit qualifier le verdict."""

    KNOWN = Path(__file__).resolve().parent.parent / "known.json"

    def setUp(self):
        self._orig = self.KNOWN.read_text(encoding="utf-8")

    def tearDown(self):
        self.KNOWN.write_text(self._orig, encoding="utf-8")

    def _seed(self, traps=None, payers=None):
        self.KNOWN.write_text(json.dumps(
            {"known_traps": traps or [], "known_payers": payers or [], "comment": "test"},
            ensure_ascii=False, indent=2), encoding="utf-8")

    def test_piege_net_haute_confiance(self):
        data = {
            "full_name": "someuser/x", "issue_number": 1,
            "issue_title": "🎯 Fix: q", "issue_labels": ["opire", "$10"],
            "issue_body_sample": "", "reward_verified": None,
            "repo_fork": False, "repo_stars": 0,
            "repo_created": "2026-08-18T11:00:00Z", "paid_history": False,
            "owner_login": "someuser", "owner_created": "2026-08-18T10:00:00Z",
        }
        result = score(data, load_rules())
        conf = result["confidence"]
        self.assertEqual(result["verdict"], "PIEGE")
        self.assertGreaterEqual(conf["confidence"], 8)
        self.assertIn("Ne pas engager de travail", conf["recommendation"])

    def test_a_verifier_confiance_plafonnee_et_signal_manquant(self):
        """Clone très proche (1 j) + issue #1 + petit prix, compte jeune (79 j) :
        A_VERIFIER, confiance plafonnée, et la recommandation signale le signal
        fort absent (account_age gradué => 0.2, donc stars_check est manquant)."""
        data = {
            "full_name": "someuser/young-repo", "issue_number": 1,
            "issue_title": "Add a config field", "issue_labels": ["feature"],
            "issue_body_sample": "costs $15", "reward_verified": None,
            "repo_fork": False, "repo_stars": 5,
            "repo_created": "2026-06-02T10:00:00Z", "paid_history": None,
            "owner_login": "someuser", "owner_created": "2026-06-01T10:00:00Z",
        }
        result = score(data, load_rules())
        conf = result["confidence"]
        self.assertEqual(result["verdict"], "A_VERIFIER", result)
        self.assertLessEqual(conf["confidence"], 6)
        self.assertIn("Signal fort manquant", conf["recommendation"])
        self.assertIn("stars_check", conf["recommendation"])

    def test_forcage_memoire_confiance_max(self):
        self._seed(payers=["o2sdev/openselfservice"])
        data = {"full_name": "o2sdev/openselfservice", "issue_number": 500,
                "issue_title": "🎯 Fix", "issue_labels": ["bounty", "$10"],
                "owner_login": "o2sdev"}
        result = score(data, load_rules())
        self.assertEqual(result["forced"], "VRAI")
        self.assertEqual(result["confidence"]["confidence"], 10)


class TestVeille(unittest.TestCase):
    """P3-12 : la veille liste les issues Reward ouvertes des repos surveillés."""

    def test_find_open_reward_issues_parse_l_api(self):
        fake_json = {"items": [
            {"html_url": "https://github.com/o2sdev/openselfservice/issues/500"},
            {"html_url": "https://github.com/o2sdev/openselfservice/issues/501"},
        ]}
        with mock.patch("tools.veille.fetch_json", return_value=fake_json) as m:
            urls = veille.find_open_reward_issues("o2sdev", "openselfservice")
        self.assertEqual(len(urls), 2)
        m.assert_called_once()

    def test_run_watch_generer_rapports_json(self):
        """Avec des URLs factices, chaque issue collectée doit être scorée."""
        # watchlist temporaire (le watchlist.json du repo est gitignoré)
        import tempfile
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump({"repos": ["o2sdev/openselfservice"]}, tmp)
        tmp.close()
        watch = tmp.name
        urls = [("https://github.com/o2sdev/openselfservice/issues/500", 1),
                ("https://github.com/o2sdev/openselfservice/issues/501", 2)]
        with mock.patch.object(veille, "find_open_reward_issues", return_value=[u for u, _ in urls]), \
             mock.patch.object(veille, "collect_from_url",
                               side_effect=lambda u: {
                                   "full_name": "o2sdev/openselfservice",
                                   "issue_number": next(n for x, n in urls if x == u),
                                   "issue_title": "test",
                                   "issue_labels": ["💰 Reward"],
                                   "issue_body_sample": "",
                                   "reward_verified": True,
                                   "repo_fork": False, "repo_stars": 180,
                                   "repo_created": "2025-03-04T17:06:29Z", "paid_history": True,
                                   "owner_login": "o2sdev", "owner_created": "2025-02-25T10:00:00Z"}):
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = veille.run_watch(str(watch), as_json=False)
            out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("PAIEUR_PROUVE", out)
        self.assertIn("o2sdev/openselfservice", out)


if __name__ == "__main__":
    unittest.main()