"""SSRF protection tests for _is_private_ip() in server/routes/v2_settings.py.

Covers:
- localhost blocked
- *.nip.io / *.localtest.me blocked
- public domains pass
- DNS resolution failure → fail-closed (blocked)
- private IP ranges (127.x, 10.x, 172.16.x, 192.168.x) blocked
- IPv6 loopback / link-local blocked
"""

from __future__ import annotations

import socket
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")

from server.routes.v2_settings import _is_private_ip


class TestBlockedDomains:
    """Domain blacklist tests."""

    def test_localhost_blocked(self):
        assert _is_private_ip("localhost") is True

    def test_localhost_uppercase_blocked(self):
        assert _is_private_ip("LOCALHOST") is True

    def test_metadata_google_internal_blocked(self):
        assert _is_private_ip("metadata.google.internal") is True


class TestBlockedDomainSuffixes:
    """Wildcard DNS suffix blacklist tests."""

    def test_nip_io_blocked(self):
        assert _is_private_ip("127.0.0.1.nip.io") is True

    def test_nip_io_subdomain_blocked(self):
        assert _is_private_ip("anything.nip.io") is True

    def test_localtest_me_blocked(self):
        assert _is_private_ip("foo.localtest.me") is True

    def test_deep_subdomain_nip_io_blocked(self):
        assert _is_private_ip("a.b.c.nip.io") is True


class TestPrivateIPRanges:
    """Direct private IP address tests."""

    def test_loopback_127_0_0_1(self):
        assert _is_private_ip("127.0.0.1") is True

    def test_loopback_127_x(self):
        assert _is_private_ip("127.0.0.2") is True

    def test_class_a_private_10_x(self):
        assert _is_private_ip("10.0.0.1") is True

    def test_class_b_private_172_16(self):
        assert _is_private_ip("172.16.0.1") is True

    def test_class_c_private_192_168(self):
        assert _is_private_ip("192.168.1.1") is True

    def test_link_local_169_254(self):
        assert _is_private_ip("169.254.1.1") is True

    def test_ipv6_loopback(self):
        assert _is_private_ip("::1") is True

    def test_ipv6_link_local(self):
        assert _is_private_ip("fe80::1") is True


class TestPublicIPAddresses:
    """Public IP addresses should pass."""

    def test_public_ip_8_8_8_8(self):
        assert _is_private_ip("8.8.8.8") is False

    def test_public_ip_1_1_1_1(self):
        assert _is_private_ip("1.1.1.1") is False

    def test_public_ipv6(self):
        assert _is_private_ip("2001:4860:4860::8888") is False


class TestPublicDomains:
    """Public domains should pass (mocked DNS)."""

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_google_com_passes(self, mock_dns):
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("142.250.80.46", 0)),
        ]
        assert _is_private_ip("google.com") is False

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_openai_com_passes(self, mock_dns):
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("104.18.6.192", 0)),
        ]
        assert _is_private_ip("api.openai.com") is False

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_domain_resolving_to_public_ip_passes(self, mock_dns):
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
        ]
        assert _is_private_ip("example.com") is False


class TestDNSResolutionToPrivate:
    """Domain that resolves to private IP should be blocked."""

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_domain_resolving_to_loopback_blocked(self, mock_dns):
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
        ]
        assert _is_private_ip("internal.example.com") is True

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_domain_resolving_to_10_x_blocked(self, mock_dns):
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 0)),
        ]
        assert _is_private_ip("vpn.example.com") is True

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_domain_resolving_to_192_168_blocked(self, mock_dns):
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.100", 0)),
        ]
        assert _is_private_ip("router.local") is True

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_mixed_results_with_private_blocked(self, mock_dns):
        """If any resolved IP is private, the domain is blocked."""
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0)),
        ]
        assert _is_private_ip("mixed.example.com") is True


class TestDNSFailureFailClosed:
    """DNS resolution failure should fail-closed (block the request)."""

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_dns_gaierror_blocked(self, mock_dns):
        mock_dns.side_effect = socket.gaierror("Name resolution failed")
        assert _is_private_ip("nonexistent.invalid") is True

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_dns_oserror_blocked(self, mock_dns):
        mock_dns.side_effect = OSError("Network unreachable")
        assert _is_private_ip("unreachable.example.com") is True


class TestTrailingDotNormalization:
    """Trailing dots in hostnames should be normalized."""

    def test_localhost_with_trailing_dot(self):
        assert _is_private_ip("localhost.") is True

    @patch("server.routes.v2_settings.socket.getaddrinfo")
    def test_public_domain_with_trailing_dot(self, mock_dns):
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
        ]
        assert _is_private_ip("example.com.") is False
