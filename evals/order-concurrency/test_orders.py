import json
from pathlib import Path
import tempfile
import unittest

from orders import submit_order


class OrderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "orders.json"

    def test_persists_new_order(self):
        order = submit_order(self.path, "order-1", "çay", 2)
        self.assertEqual([order], json.loads(self.path.read_text(encoding="utf-8")))

    def test_repeated_request_does_not_duplicate_persisted_order(self):
        first = submit_order(self.path, "order-1", "çay", 2)
        before = self.path.read_bytes()
        again = submit_order(self.path, "order-1", "çay", 2)
        self.assertEqual(first, again)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual([first], json.loads(self.path.read_text(encoding="utf-8")))

    def test_same_request_with_different_content_is_rejected(self):
        first = submit_order(self.path, "order-1", "çay", 2)
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            submit_order(self.path, "order-1", "kahve", 2)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual([first], json.loads(self.path.read_text(encoding="utf-8")))

    def test_same_request_with_different_quantity_is_rejected(self):
        first = submit_order(self.path, "order-1", "çay", 2)
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            submit_order(self.path, "order-1", "çay", 3)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual([first], json.loads(self.path.read_text(encoding="utf-8")))

    def test_invalid_quantity_does_not_create_a_file(self):
        for invalid in (0, -1, True, 1.2):
            with self.subTest(quantity=invalid):
                with self.assertRaises(ValueError):
                    submit_order(self.path, "bad", "çay", invalid)
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
