"""Keep the task evaluator honest about its deliberately broken starting code."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "evals" / "order-concurrency"


class OrderConcurrencyEvalTests(unittest.TestCase):
    def test_starting_fixture_passes_sequential_tests(self):
        suite = unittest.defaultTestLoader.discover(str(TASK), pattern="test_orders.py")
        result = unittest.TestResult()
        suite.run(result)
        self.assertEqual(5, result.testsRun)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

    def test_grader_rejects_starting_race(self):
        grader = self.load_grader()
        self.assertEqual(
            {"distinct_requests": False, "conflicting_request": False},
            grader.evaluate(TASK),
        )

    def test_grader_rejects_same_race_with_read_bytes(self):
        grader = self.load_grader()
        source = (TASK / "orders.py").read_text(encoding="utf-8")
        alternate = source.replace(
            'path.read_text(encoding="utf-8")',
            'path.read_bytes().decode("utf-8")',
        )
        self.assertNotEqual(source, alternate)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "orders.py").write_text(alternate, encoding="utf-8")
            self.assertEqual(
                {"distinct_requests": False, "conflicting_request": False},
                grader.evaluate(folder),
            )

    def test_grader_rejects_same_race_with_builtin_open(self):
        grader = self.load_grader()
        source = (TASK / "orders.py").read_text(encoding="utf-8")
        alternate = source.replace(
            '    orders = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []',
            '    if path.exists():\n'
            '        with open(path, encoding="utf-8") as handle:\n'
            '            orders = json.load(handle)\n'
            '    else:\n'
            '        orders = []',
        )
        self.assertNotEqual(source, alternate)
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "orders.py").write_text(alternate, encoding="utf-8")
            self.assertEqual(
                {"distinct_requests": False, "conflicting_request": False},
                grader.evaluate(folder),
            )

    def test_grader_accepts_serialized_control(self):
        grader = self.load_grader()
        lock = Lock()

        def submit_order(path, request_id, product, quantity):
            with lock:
                orders = json.loads(path.read_text(encoding="utf-8"))
                for order in orders:
                    if order["request_id"] == request_id:
                        if (order["product"], order["quantity"]) != (product, quantity):
                            raise ValueError("conflicting request")
                        return order
                order = {"request_id": request_id, "product": product, "quantity": quantity}
                orders.append(order)
                path.write_text(json.dumps(orders), encoding="utf-8")
                return order

        candidate = SimpleNamespace(submit_order=submit_order)
        with patch.object(grader, "load_candidate", return_value=candidate):
            self.assertEqual(
                {"distinct_requests": True, "conflicting_request": True},
                grader.evaluate(TASK),
            )

    @staticmethod
    def load_grader():
        spec = importlib.util.spec_from_file_location("order_concurrency_grader", TASK / "grade.py")
        grader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grader)
        return grader


if __name__ == "__main__":
    unittest.main()
