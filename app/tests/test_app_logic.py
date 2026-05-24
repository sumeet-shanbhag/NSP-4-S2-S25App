from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.actions.handlers import ActionHandler
from app.core.logger import ActionLogger
from app.data.sample_data import generate_employee_data


class AppLogicTests(unittest.TestCase):
    def test_sample_data_generation_shape(self) -> None:
        rows = generate_employee_data(rows=120, seed=7)
        self.assertEqual(len(rows), 120)
        self.assertTrue({"EmployeeID", "Attrition", "Age", "Department"}.issubset(rows[0].keys()))

    def test_action_handler_success_no_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "events.log"
            logger = ActionLogger(log_file=log_file)
            handler = ActionHandler(logger=logger, failure_rate=0.0)

            result = handler.run("sample_action", {"x": 1}, lambda: "ok")

            self.assertEqual(result, "ok")
            # Success actions should NOT be logged (only errors are logged)
            self.assertFalse(log_file.exists())

    def test_action_handler_failure_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "events.log"
            logger = ActionLogger(log_file=log_file)
            handler = ActionHandler(logger=logger, failure_rate=1.0)

            with self.assertRaises(Exception):
                handler.run("always_fail", {}, lambda: "never")

            text = log_file.read_text(encoding="utf-8")
            self.assertIn('"status": "error"', text)
            self.assertIn("always_fail", text)


if __name__ == "__main__":
    unittest.main()

