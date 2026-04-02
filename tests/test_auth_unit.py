"""Unit tests for JWT authentication."""

from datetime import timedelta

import pytest

from core.auth.jwt import create_access_token, verify_token

# The JWT module is importable when PYTHONPATH includes src/.
# All tests use the real implementation with mocked config where needed.


class TestJWTTokenCreation:
    """Tests for JWT token operations."""

    def test_create_access_token_returns_string(self):
        """create_access_token should return a non-empty string."""
        token = create_access_token(username="testuser", user_id=1)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_three_parts(self):
        """JWT tokens consist of three dot-separated parts."""
        token = create_access_token(username="testuser", user_id=1)
        parts = token.split(".")
        assert len(parts) == 3

    def test_verify_valid_token(self):
        """A freshly created token should pass verification."""
        token = create_access_token(username="testuser", user_id=1)
        payload = verify_token(token)
        assert payload is not None
        assert payload.sub == "testuser"
        assert payload.user_id == 1

    def test_expired_token_is_rejected(self):
        """An expired token should fail verification."""
        token = create_access_token(
            username="testuser",
            user_id=1,
            expires_delta=timedelta(seconds=-1),
        )
        payload = verify_token(token)
        assert payload is None

    def test_tampered_token_is_rejected(self):
        """A tampered token should fail verification."""
        token = create_access_token(username="testuser", user_id=1)
        tampered = token[:-5] + "XXXXX"
        payload = verify_token(tampered)
        assert payload is None

    def test_token_includes_display_name(self):
        """Token payload should include display_name when provided."""
        token = create_access_token(username="alice", user_id=2, display_name="Alice Smith")
        payload = verify_token(token)
        assert payload is not None
        assert payload.display_name == "Alice Smith"

    def test_token_includes_ad_groups(self):
        """Token payload should include ad_groups when provided."""
        groups = ["cn=devs,ou=groups,dc=example,dc=com"]
        token = create_access_token(username="bob", user_id=3, ad_groups=groups)
        payload = verify_token(token)
        assert payload is not None
        assert payload.ad_groups == groups


class TestPasswordHashing:
    """Tests for password hashing.

    The codebase uses LDAP-based authentication and does not expose standalone
    hash_password / verify_password helpers. These tests verify bcrypt
    behaviour using whichever library is available (passlib or bcrypt directly).
    """

    @staticmethod
    def _get_hash_functions():
        """Return (hash_fn, verify_fn) from the first available library."""
        try:
            from passlib.context import CryptContext

            ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return ctx.hash, ctx.verify
        except ImportError:
            pass
        try:
            import bcrypt

            def _hash(pw):
                return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

            def _verify(pw, hashed):
                return bcrypt.checkpw(pw.encode(), hashed.encode())

            return _hash, _verify
        except ImportError:
            return None, None

    def test_hash_is_not_plaintext(self):
        """A hashed password should differ from the original."""
        hash_fn, _ = self._get_hash_functions()
        if hash_fn is None:
            pytest.skip("No bcrypt library available (passlib or bcrypt)")
        hashed = hash_fn("secret123")
        assert hashed != "secret123"

    def test_verify_correct_password(self):
        """Correct plaintext should verify against its hash."""
        hash_fn, verify_fn = self._get_hash_functions()
        if hash_fn is None:
            pytest.skip("No bcrypt library available (passlib or bcrypt)")
        hashed = hash_fn("secret123")
        assert verify_fn("secret123", hashed) is True

    def test_verify_wrong_password(self):
        """Wrong plaintext should NOT verify against the hash."""
        hash_fn, verify_fn = self._get_hash_functions()
        if hash_fn is None:
            pytest.skip("No bcrypt library available (passlib or bcrypt)")
        hashed = hash_fn("secret123")
        assert verify_fn("wrongpassword", hashed) is False
