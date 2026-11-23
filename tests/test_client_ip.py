import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rate_limiter import client_ip_from_headers


class ClientIpTest(unittest.TestCase):
    def setUp(self):
        os.environ.pop("TRUSTED_PROXY_HOPS", None)

    def test_spoofed_left_values_are_ignored(self):
        h = {"X-Forwarded-For": "1.2.3.4, 9.9.9.9, 203.0.113.7"}
        self.assertEqual(client_ip_from_headers(h), "203.0.113.7")

    def test_single_value(self):
        self.assertEqual(client_ip_from_headers({"x-forwarded-for": "203.0.113.7"}), "203.0.113.7")

    def test_two_trusted_hops(self):
        os.environ["TRUSTED_PROXY_HOPS"] = "2"
        h = {"X-Forwarded-For": "1.2.3.4, 198.51.100.2, 203.0.113.7"}
        self.assertEqual(client_ip_from_headers(h), "198.51.100.2")

    def test_missing_header_and_client_set_alternates_not_trusted(self):
        self.assertEqual(client_ip_from_headers({"X-Real-IP": "1.2.3.4", "CF-Connecting-IP": "5.6.7.8"}), "unknown")


if __name__ == "__main__":
    unittest.main()
