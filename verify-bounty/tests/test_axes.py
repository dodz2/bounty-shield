# Tests des axes AUTHENTICITÉ / EXPLOITABILITÉ + check repo_liveness (items 1, 3, 4).
# Vérifie :
#  - liveness : un repo mort avec bounties orphelins est pénalisé (cas cocohub)
#  - deux axes indépendants en sortie
#  - exploitabilité : PRIS / CONTESTÉ / LIBRE / INCONNU selon la concurrence

import json
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scorer import load_rules, score  # noqa: E402


def _base(**kw):
    """Profil synthétique d'un dépôt propre (signaux faibles)."""
    data = {
        "full_name": "unknown/clean-repo",
        "issue_number": 42,
        "issue_title": "Add a config option",
        "issue_state": "open",
        "issue_labels": ["bounty", "$50"],
        "issue_body_sample": "reward link https://opire.dev/x",
        "reward_verified": True,
        "repo_fork": False,
        "repo_stars": 120,
        "repo_archived": False,
        "repo_license": "MIT",
        "repo_created": "2023-01-01T10:00:00Z",
        "repo_pushed_at": "2026-08-10T10:00:00Z",
        "open_reward_issues": 3,
        "paid_history": True,
        "claims": 0,
        "open_pr_count": 0,
        "merged_pr_for_issue": False,
        "owner_login": "unknown",
        "owner_created": "2020-01-01T10:00:00Z",
    }
    data.update(kw)
    return data


class TestRepoLiveness(unittest.TestCase):
    """Item 1 : le check repo_liveness flagge les dépôts morts."""

    def test_repo_actif_ne_penalise_pas(self):
        data = _base()
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "repo_liveness")
        self.assertEqual(check["points"], 0)

    def test_repo_inactif_avec_bounties_orphelins_est_penalise(self):
        """Cas cocohub : inactif + bounties ouverts = travail jamais payé."""
        data = _base(repo_pushed_at="2026-01-01T10:00:00Z", open_reward_issues=18)
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "repo_liveness")
        self.assertEqual(check["points"], 2)

    def test_repo_inactif_sans_bounties_penalise_legere(self):
        data = _base(repo_pushed_at="2026-01-01T10:00:00Z", open_reward_issues=0)
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "repo_liveness")
        self.assertEqual(check["points"], 1)

    def test_donnees_manquantes_neutres(self):
        data = _base()
        del data["repo_pushed_at"]
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "repo_liveness")
        self.assertEqual(check["points"], 0)


class TestAuthenticity(unittest.TestCase):
    """Item 3 : l'axe authenticité distingue PIÈGE / SANS_PREUVE / PAIEUR_PROUVE."""

    KNOWN = Path(__file__).resolve().parent.parent / "known.json"

    def setUp(self):
        self._orig = self.KNOWN.read_text(encoding="utf-8")

    def tearDown(self):
        self.KNOWN.write_text(self._orig, encoding="utf-8")

    def _seed_trap(self, account):
        import json as _json
        self.KNOWN.write_text(_json.dumps(
            {"known_traps": [account], "known_payers": [], "comment": "test"},
            ensure_ascii=False, indent=2), encoding="utf-8")

    def test_payeur_historique_prouve(self):
        result = score(_base(paid_history=True), load_rules())
        self.assertEqual(result["authenticity"]["status"], "PAIEUR_PROUVE")

    def test_sans_historique_ni_connu_est_sans_preuve(self):
        """Le cœur de la correction : un repo propre mais sans preuve de paiement = SANS_PREUVE, pas PAIEUR_PROUVE."""
        result = score(_base(paid_history=False), load_rules())
        self.assertEqual(result["authenticity"]["status"], "SANS_PREUVE")

    def test_piege_reste_piege(self):
        data = _base(
            owner_created="2026-08-18T10:00:00Z", repo_stars=0,
            issue_number=1, issue_title="🎯 Fix: x",
            issue_labels=["opire", "$10"], paid_history=False,
        )
        result = score(data, load_rules())
        self.assertEqual(result["authenticity"]["status"], "PIEGE")

    def test_piege_connu_force_piege(self):
        self._seed_trap("trapuser01")
        data = _base(full_name="trapuser01/caddy", owner_login="trapuser01")
        result = score(data, load_rules())
        self.assertEqual(result["authenticity"]["status"], "PIEGE")

    def test_piege_a_historique_forge_reste_piege(self):
        """Usine qui simule un paid_history : la note de risque prime."""
        data = _base(
            owner_created="2026-08-05T10:00:00Z", repo_stars=0,
            issue_number=1, issue_title="🎯 Fix: x",
            issue_labels=["opire", "$10"], paid_history=True,
        )
        result = score(data, load_rules())
        self.assertEqual(result["authenticity"]["status"], "PIEGE")


class TestExploitability(unittest.TestCase):
    """Items 3+4 : l'axe exploitabilité mesure la concurrence."""

    def test_libre_aucun_claim_aucune_pr(self):
        result = score(_base(claims=0, open_pr_count=0), load_rules())
        self.assertEqual(result["exploitability"]["status"], "LIBRE")

    def test_conteste_un_claim(self):
        result = score(_base(claims=1, open_pr_count=0), load_rules())
        self.assertEqual(result["exploitability"]["status"], "CONTESTE")

    def test_conteste_pr_ouverte(self):
        result = score(_base(claims=0, open_pr_count=1), load_rules())
        self.assertEqual(result["exploitability"]["status"], "CONTESTE")

    def test_pris_pr_fusionnee(self):
        result = score(_base(merged_pr_for_issue=True), load_rules())
        self.assertEqual(result["exploitability"]["status"], "PRIS")

    def test_pris_issue_fermee(self):
        result = score(_base(issue_state="closed", claims=0, open_pr_count=0), load_rules())
        self.assertEqual(result["exploitability"]["status"], "PRIS")

    def test_inconnu_donnees_absentes(self):
        """Ne pas inventer un verdict : sans données de concurrence -> INCONNU."""
        result = score(_base(), load_rules())
        result["exploitability"]  # sanity
        data = _base()
        del data["claims"]
        del data["open_pr_count"]
        result2 = score(data, load_rules())
        self.assertEqual(result2["exploitability"]["status"], "INCONNU")


class TestMultiDevises(unittest.TestCase):
    """Item 5 : le montant est détecté en plusieurs devises, pas seulement $."""

    def test_dollar(self):
        from checks.amount_check import _find_amount
        a, c = _find_amount({"issue_title": "", "issue_labels": [], "issue_body_sample": "reward $150"})
        self.assertEqual((a, c), (150.0, "USD"))

    def test_xlm(self):
        from checks.amount_check import _find_amount
        a, c = _find_amount({"issue_title": "", "issue_labels": [], "issue_body_sample": "Bounty: 10 XLM"})
        self.assertEqual(c, "XLM")
        self.assertLessEqual(a, 20)  # faible -> suspect

    def test_ethereum_decimal(self):
        from checks.amount_check import _find_amount
        a, c = _find_amount({"issue_title": "", "issue_labels": [], "issue_body_sample": "0.5 ETH reward"})
        self.assertEqual(c, "ETH")
        self.assertEqual(a, 0.5)

    def test_devise_elevee_non_suspecte(self):
        data = _base(issue_body_sample="Bounty $150", issue_labels=["bounty"])
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "amount_check")
        self.assertEqual(check["points"], 0)


class TestMultiPlateformes(unittest.TestCase):

    def test_opire_reconnu(self):
        from checks.platforms import extract_reward_link
        url, plat = extract_reward_link("See https://opire.dev/a/b/c for reward")
        self.assertEqual(plat, "opire")

    def test_algora_reconnu(self):
        from checks.platforms import extract_reward_link
        url, plat = extract_reward_link("Funded via https://algora.io/xyz")
        self.assertEqual(plat, "algora")

    def test_grantfox_reconnu(self):
        from checks.platforms import extract_reward_link
        url, plat = extract_reward_link("Reward via https://grantfox.xyz/x (released in 48h)")
        self.assertEqual(plat, "grantfox")

    def test_lien_tiers_non_reconnu_penalise(self):
        """Un lien de récompense vers un domaine inconnu est une revendication non prouvée."""
        data = _base(issue_labels=["bounty"], issue_body_sample="Reward: https://example.com/pay")
        data["reward_url"] = "https://example.com/pay"
        data["reward_verified"] = None
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "reward_link")
        self.assertEqual(check["points"], 1)


class TestCompteAgeGradu(unittest.TestCase):
    """Item 6 : account_age est gradué en 3 bandes au lieu d'être binaire."""

    def test_compte_etabli_pas_penalise(self):
        data = _base(owner_created="2015-01-01T10:00:00Z")
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "account_age")
        self.assertEqual(check["points"], 0.0)

    def test_compte_jeune_nuance(self):
        """33 j (cas copperhead) : nuance, ni blanc ni piège."""
        data = _base(owner_created="2026-07-17T10:00:00Z")
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "account_age")
        self.assertEqual(check["points"], 0.2)

    def test_compte_recent_moyen(self):
        data = _base(owner_created="2026-08-01T10:00:00Z")
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "account_age")
        self.assertEqual(check["points"], 0.5)

    def test_compte_tres_recent_fort(self):
        data = _base(owner_created="2026-08-18T10:00:00Z")
        check = next(c for c in score(data, load_rules())["checks"] if c["name"] == "account_age")
        self.assertEqual(check["points"], 1.0)


class TestConfianceAffichage(unittest.TestCase):

    def test_confiance_haut_niveau_propre(self):
        result = score(_base(), load_rules())
        # note faible = confiance haute
        self.assertGreaterEqual(10 - result["note"], 7.0)

    def test_rapport_contient_les_deux_axes(self):
        import io
        import contextlib
        import verify_bounty
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            verify_bounty.print_report(_base(claims=2, open_pr_count=1), score(_base(claims=2, open_pr_count=1), load_rules()))
        out = buf.getvalue()
        self.assertIn("AUTHENTICITÉ", out)
        self.assertIn("EXPLOITABILITÉ", out)
        self.assertIn("CONTESTÉ", out)


if __name__ == "__main__":
    unittest.main()
