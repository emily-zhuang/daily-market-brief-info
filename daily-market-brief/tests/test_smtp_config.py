import os
import sys
from pathlib import Path

import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))
from mail_config import smtp_config_from_env


class SmtpConfigTests(unittest.TestCase):
  def test_requires_address_and_app_password(self):
    os.environ["GMAIL_ADDRESS"] = "sender@gmail.com"
    os.environ["GMAIL_APP_PASSWORD"] = "abcd efgh ijkl mnop"

    self.assertEqual(smtp_config_from_env(), ("sender@gmail.com", "abcdefghijklmnop"))

  def test_removes_non_breaking_spaces_from_app_password(self):
    os.environ["GMAIL_ADDRESS"] = "sender@gmail.com"
    os.environ["GMAIL_APP_PASSWORD"] = "abcd\u00a0efgh ijkl mnop"

    self.assertEqual(smtp_config_from_env(), ("sender@gmail.com", "abcdefghijklmnop"))

  def test_reports_missing_secret(self):
    os.environ.pop("GMAIL_ADDRESS", None)
    os.environ.pop("GMAIL_APP_PASSWORD", None)

    with self.assertRaisesRegex(RuntimeError, "GMAIL_ADDRESS and GMAIL_APP_PASSWORD"):
        smtp_config_from_env()


if __name__ == "__main__":
  unittest.main()
