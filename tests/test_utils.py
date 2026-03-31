"""Tests for utility functions."""

import re

from core.db.db_chat import sanitize_table_name


class TestSanitizeTableName:
    """Tests for the sanitize_table_name function."""

    def test_basic_name(self):
        """A simple lowercase name should be returned unchanged."""
        assert sanitize_table_name("myproject") == "myproject"

    def test_uppercase_converted(self):
        """Uppercase letters should be lowercased."""
        assert sanitize_table_name("MyProject") == "myproject"

    def test_spaces_to_underscores(self):
        """Spaces should be converted to underscores (or removed)."""
        result = sanitize_table_name("my project name")
        assert " " not in result

    def test_hyphens_handled(self):
        """Hyphens should be replaced with underscores."""
        result = sanitize_table_name("my-project")
        assert re.match(r"^[a-z0-9_]+$", result), f"Invalid identifier: {result}"

    def test_length_limit(self):
        """Result should not exceed 63 characters."""
        result = sanitize_table_name("x" * 200)
        assert len(result) <= 63

    def test_special_chars_removed(self):
        """Special characters should be stripped or replaced."""
        result = sanitize_table_name("project@#$%name!")
        assert re.match(r"^[a-z0-9_]+$", result), f"Invalid identifier: {result}"


class TestFileAttachmentSchema:
    """Tests for FileAttachment Pydantic model."""

    def test_file_attachment_fields(self):
        """FileAttachment should expose filename, content_type, and data fields."""
        import base64

        from api.schema import FileAttachment

        # Use properly base64-encoded content
        raw = b"binary file content"
        b64 = base64.b64encode(raw).decode()
        f = FileAttachment(
            filename="test.pdf", content_type="application/pdf", data=b64
        )
        assert f.filename == "test.pdf"
        assert f.content_type == "application/pdf"
        assert f.data == b64
