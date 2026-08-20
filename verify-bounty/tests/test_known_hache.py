# Tests du mode HACHÉ de known_list (non-divulgation des comptes).
# Vérifie : détection par hash, non-lisibilité en clair.

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from checks.known_list import _sha256, _load_known, run  # noqa: E402


class TestKnownListHache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.orig_path = Path(__file__).resolve().parent.parent / "known.json"
        self._saved = self.orig_path.read_text(encoding="utf-8")
        # on pointe _load_known vers un fichier temporaire via monkeypatch
        self._known_path = self.dir / "known.json"

    def tearDown(self):
        self.orig_path.write_text(self._saved, encoding="utf-8")
        self.tmp.cleanup()

    def _patch_load(self):
        import checks.known_list as kl
        self._orig_load = kl._load_known
        kl._load_known = lambda: json.loads(self._known_path.read_text(encoding="utf-8"))
        return kl

    def test_detecte_compte_via_hash(self):
        kl = self._patch_load()
        try:
            self._known_path.write_text(json.dumps(
                {"known_traps_hashes": [_sha256("trapuser01")], "known_payers_hashes": []},
                ensure_ascii=False), encoding="utf-8")
            res = kl.run({"owner_login": "trapuser01", "full_name": "trapuser01/caddy"}, {})
            self.assertEqual(res.get("force"), "PIEGE")
        finally:
            kl._load_known = self._orig_load

    def test_pas_de_nom_en_clair_dans_le_fichier(self):
        """Le fichier haché ne contient JAMAIS le login en clair."""
        self._known_path.write_text(json.dumps(
            {"known_traps_hashes": [_sha256("trapuser01")], "known_payers_hashes": []},
            ensure_ascii=False), encoding="utf-8")
        content = self._known_path.read_text(encoding="utf-8")
        self.assertNotIn("trapuser01", content.lower())

    def test_sha256_deterministe(self):
        self.assertEqual(_sha256("abc"), hashlib.sha256(b"abc").hexdigest())


if __name__ == "__main__":
    unittest.main()
