# Tests des améliorations P1 : pondération, forçage mémoire, lien de récompense.

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import load_rules, score  # noqa: E402


class TestPonderation(unittest.TestCase):
    def test_deux_signaux_forts_seuls_restent_a_verifier(self):
        """Compte créé hier + 0 étoile seulement = A_VERIFIER (prudence, pas de preuve)."""
        data = {
            "full_name": "someuser/legit-looking",
            "issue_number": 45,
            "issue_title": "Add dark mode support",
            "issue_labels": ["feature"],
            "issue_body_sample": "",
            "repo_fork": False,
            "repo_stars": 0,
            "repo_archived": False,
            "repo_license": "MIT",
            "owner_login": "someuser",
            "owner_created": "2026-08-17T10:00:00Z",
        }
        result = score(data, load_rules())
        self.assertEqual(result["verdict"], "A_VERIFIER")

    def test_piege_sophistique_pattern_usine_detecte(self):
        """Compte récent + 0 étoile + issue #1 = PIEGE, même avec titre normal et $100."""
        data = {
            "full_name": "someuser/legit-looking",
            "issue_number": 1,
            "issue_title": "Add dark mode support",
            "issue_labels": ["feature"],
            "issue_body_sample": "",
            "repo_fork": False,
            "repo_stars": 0,
            "repo_archived": False,
            "repo_license": "MIT",
            "owner_login": "someuser",
            "owner_created": "2026-08-17T10:00:00Z",
        }
        result = score(data, load_rules())
        self.assertEqual(result["verdict"], "PIEGE")

    def test_vrai_inconnu_non_detecte_comme_piege(self):
        """Compte âgé + étoiles + issue normale = VRAI sans être dans la liste connue."""
        data = {
            "full_name": "unknown/real-project",
            "issue_number": 120,
            "issue_title": "Improve error messages on login",
            "issue_labels": ["enhancement"],
            "issue_body_sample": "",
            "repo_fork": False,
            "repo_stars": 95,
            "repo_archived": False,
            "repo_license": "MIT",
            "owner_login": "unknown",
            "owner_created": "2019-04-01T10:00:00Z",
        }
        result = score(data, load_rules())
        self.assertEqual(result["verdict"], "VRAI")


class TestForcageMemoire(unittest.TestCase):
    """Teste le forçage mémoire avec un known.json TEMPORAIRE (auto-suffisant).

    Le repo public embarque un known.json VIDE (template). Ces tests créent
    leur propre mémoire de test et la restaurent — indépendants des données
    privées Daedalus.
    """

    KNOWN = Path(__file__).resolve().parent.parent / "known.json"

    def setUp(self):
        self._orig = self.KNOWN.read_text(encoding="utf-8")

    def tearDown(self):
        self.KNOWN.write_text(self._orig, encoding="utf-8")

    def _seed(self, traps=None, payers=None):
        self.KNOWN.write_text(json.dumps(
            {"known_traps": traps or [], "known_payers": payers or [], "comment": "test"},
            ensure_ascii=False, indent=2), encoding="utf-8")

    def test_payeur_connu_force_vrai(self):
        self._seed(payers=["o2sdev/openselfservice"])
        data = {
            "full_name": "o2sdev/openselfservice",
            "issue_number": 500,
            "issue_title": "🎯 Fix something",
            "issue_labels": ["bounty", "opire", "$10"],
            "issue_body_sample": "",
            "owner_login": "o2sdev",
        }
        result = score(data, load_rules())
        self.assertEqual(result["forced"], "VRAI")
        self.assertEqual(result["verdict"], "VRAI")

    def test_piege_connu_force_piege(self):
        self._seed(traps=["trapuser01"])
        data = {
            "full_name": "trapuser01/caddy",
            "issue_number": 1,
            "issue_title": "🎯 Fix: something",
            "issue_labels": ["bounty", "opire", "$10"],
            "issue_body_sample": "",
            "owner_login": "trapuser01",
        }
        result = score(data, load_rules())
        self.assertEqual(result["forced"], "PIEGE")
        self.assertEqual(result["verdict"], "PIEGE")
        self.assertEqual(result["note"], 10.0)


class TestLienRecompense(unittest.TestCase):
    def test_label_opire_sans_lien_verifie_ajoute_des_points(self):
        data = {
            "full_name": "userA/test-repo",
            "issue_number": 1,
            "issue_title": "🎯 Fix: something",
            "issue_labels": ["opire", "$10"],
            "issue_body_sample": "",
            "reward_verified": None,
            "owner_login": "usera",
        }
        reward_check = next(
            c for c in score(data, load_rules())["checks"] if c["name"] == "reward_link"
        )
        self.assertEqual(reward_check["points"], 1)

    def test_lien_verifie_ne_penalise_pas(self):
        data = {
            "full_name": "userB/test-repo",
            "issue_number": 1,
            "issue_title": "🎯 Fix: something",
            "issue_labels": ["opire", "$10"],
            "issue_body_sample": "",
            "reward_verified": True,
            "owner_login": "userb",
        }
        reward_check = next(
            c for c in score(data, load_rules())["checks"] if c["name"] == "reward_link"
        )
        self.assertEqual(reward_check["points"], 0)


if __name__ == "__main__":
    unittest.main()