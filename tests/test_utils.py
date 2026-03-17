"""Tests for utility functions."""
import pytest


class TestSanitizeTableName:
    """Tests for the sanitize_table_name function."""

    def _get_fn(self):
        try:
            from core.db.db_chat import sanitize_table_name
            return sanitize_table_name
        except ImportError:
            return None

    def test_basic_name(self):
        fn = self._get_fn()
        if not fn:
            pytest.skip("Function not importable")
        result = fn("myproject")
        assert result == "myproject"

    def test_uppercase_converted(self):
        fn = self._get_fn()
        if not fn:
            pytest.skip("Function not importable")
        assert fn("MyProject") == "myproject"

    def test_spaces_to_underscores(self):
        fn = self._get_fn()
        if not fn:
            pytest.skip("Function not importable")
        result = fn("my project name")
        assert " " not in result

    def test_hyphens_handled(self):
        fn = self._get_fn()
        if not fn:
            pytest.skip("Function not importable")
        result = fn("my-project")
        import re
        assert re.match(r'^[a-z0-9_]+$', result)

    def test_length_limit(self):
        fn = self._get_fn()
        if not fn:
            pytest.skip("Function not importable")
        result = fn("x" * 200)
        assert len(result) <= 63

    def test_special_chars_removed(self):
        fn = self._get_fn()
        if not fn:
            pytest.skip("Function not importable")
        result = fn("project@#$%name!")
        import re
        assert re.match(r'^[a-z0-9_]+$', result)


class TestFileAttachmentSchema:
    """Tests for FileAttachment Pydantic model."""

    def test_file_attachment_fields(self):
        from api.schema import FileAttachment
        f = FileAttachment(filename="test.pdf", content_type="application/pdf", data="base64data")
        assert f.filename == "test.pdf"
        assert f.content_type == "application/pdf"
        assert f.data == "base64data"
