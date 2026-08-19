# Tests des améliorations P2 : clone_check, payment_history, batch, retry.

import json
import unittest
from pathlib import Path
from unittest import mock
import urllib.error

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import load_rules, score  # noqa: E402


class TestCloneCheck(unittest.TestCase):
    def test_repo_cree_juste_apres_compte_est_suspect(self):
        data = {
            "full_name": "userA/copy-repo",
            "issue_number": 1,
            "issue_title": "🎯 Fix: x",
            "issue_labels": ["bounty", "opire", "$10"],
            "issue_body_sample": "",
            "repo_fork": False,
            "repo_stars": 0,
            "owner_login": "usera",
            "owner_created": "2026-08-18T10:00:00Z",
            "repo_created": "2026-08-18T11:00:00Z",
        }
        clone_check = next(
            c for c in score(data, load_rules())["checks"] if c["name"] == "clone_check"
        )
        self.assertEqual(clone_check["points"], 1)

    def test_repo_cree_des_annees_apres_compte_est_normal(self):
        data = {
            "full_name": "userB/old-repo",
            "issue_number": 10,
            "issue_title": "Add feature",
            "issue_labels": ["enhancement"],
            "issue_body_sample": "",
            "repo_fork": False,
            "repo_stars": 50,
            "owner_login": "userb",
            "owner_created": "2018-04-01T10:00:00Z",
            "repo_created": "2021-06-15T10:00:00Z",
        }
        clone_check = next(
            c for c in score(data, load_rules())["checks"] if c["name"] == "clone_check"
        )
        self.assertEqual(clone_check["points"], 0)


class TestPaymentHistory(unittest.TestCase):
    def test_historique_paye_ne_penalise_pas(self):
        data = {
            "full_name": "userC/repo",
            "issue_number": 5,
            "issue_title": "Fix bug",
            "issue_labels": ["💰 Reward"],
            "issue_body_sample": "",
            "paid_history": True,
            "owner_login": "userc",
        }
        payment_check = next(
            c for c in score(data, load_rules())["checks"] if c["name"] == "payment_history"
        )
        self.assertEqual(payment_check["points"], 0)

    def test_revendication_sans_historique_est_suspecte(self):
        data = {
            "full_name": "userD/repo",
            "issue_number": 1,
            "issue_title": "🎯 Fix: x",
            "issue_labels": ["opire", "$10"],
            "issue_body_sample": "",
            "paid_history": False,
            "owner_login": "userd",
        }
        payment_check = next(
            c for c in score(data, load_rules())["checks"] if c["name"] == "payment_history"
        )
        self.assertEqual(payment_check["points"], 1)

    def test_historique_inconnu_est_neutre(self):
        data = {
            "full_name": "userE/repo",
            "issue_number": 3,
            "issue_title": "Add docs",
            "issue_labels": ["💰 Reward"],
            "issue_body_sample": "",
            "paid_history": None,
            "owner_login": "usere",
        }
        payment_check = next(
            c for c in score(data, load_rules())["checks"] if c["name"] == "payment_history"
        )
        self.assertEqual(payment_check["points"], 0)


class TestRetry(unittest.TestCase):
    def test_fetch_json_retry_puis_succes(self):
        """Un 403 puis un succès : la 2e tentative doit aboutir."""
        import verify_bounty

        calls = {"n": 0}

        def fake_urlopen(req, timeout=30):
            calls["n"] += 1
            if calls["n"] == 1:
                raise urllib.error.HTTPError(
                    "https://api.github.com/test", 403, "rate limit", {}, None
                )
            # 2e appel : réponse JSON valide
            resp = mock.MagicMock()
            resp.read.return_value = b'{"ok": true}'
            resp.__enter__.return_value = resp
            resp.__exit__.return_value = False
            return resp

        with mock.patch.object(verify_bounty.urllib.request, "urlopen", side_effect=fake_urlopen), \
             mock.patch.object(verify_bounty.time, "sleep"):
            result = verify_bounty.fetch_json("https://api.github.com/test")
        self.assertEqual(result, {"ok": True})
        self.assertEqual(calls["n"], 2)


if __name__ == "__main__":
    unittest.main()