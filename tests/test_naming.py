import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "naming.py"
POLICY = ROOT / "registry" / "naming-policy.json"


def load_naming():
    spec = importlib.util.spec_from_file_location("divan_naming", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load naming controller")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NamingPolicyTests(unittest.TestCase):
    def test_repository_has_english_canonical_policy_and_bounded_legacy_aliases(self) -> None:
        naming = load_naming()
        errors = naming.validate(ROOT)
        self.assertEqual(errors, [])

        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(policy["canonical_language"], "en")
        self.assertEqual(policy["locales"], ["en", "tr"])
        replacements = {row["replacement"] for row in policy["legacy_aliases"]}
        for required in (
            "scripts/divan.py",
            "scripts/host_lifecycle.py",
            "scripts/catalog.py",
            "scripts/release.py",
            "scripts/standards.py",
            "scripts/hygiene.py",
            "scripts/handoff.py",
            "scripts/candidate_review.py",
        ):
            self.assertIn(required, replacements | set(policy["canonical_entrypoints"]))

    def test_unregistered_non_english_technical_name_is_rejected(self) -> None:
        naming = load_naming()
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            (root / "registry").mkdir()
            (root / "scripts").mkdir()
            (root / ".github" / "workflows").mkdir(parents=True)
            policy = json.loads(POLICY.read_text(encoding="utf-8"))
            policy["canonical_entrypoints"] = []
            policy["legacy_aliases"] = []
            (root / "registry" / "naming-policy.json").write_text(
                json.dumps(policy), encoding="utf-8"
            )
            (root / "scripts" / "yeni-arac.py").write_text("# tool\n", encoding="utf-8")

            errors = naming.validate(root)

        self.assertTrue(any("unregistered technical name" in error for error in errors))

    def test_legacy_python_aliases_are_narrow_deprecated_wrappers(self) -> None:
        naming = load_naming()
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        for row in policy["legacy_aliases"]:
            if not row["path"].endswith(".py"):
                continue
            path = ROOT / row["path"]
            errors = naming.legacy_wrapper_errors(path, row["replacement"])
            self.assertEqual(errors, [], row["path"])

