import pytest
from unittest.mock import Mock, patch
from app import process_attachments, validate_file

def test_validate_file_valid():
    with patch("os.path.getsize", return_value=5*1024*1024):
        with patch("mimetypes.guess_type", return_value=("text/plain", None)):
            validate_file("test.txt")

def test_validate_file_invalid_size():
    with pytest.raises(ValueError):
        with patch("os.path.getsize", return_value=15*1024*1024):
            validate_file("large_file.bin")

def test_process_attachments_no_files():
    assert process_attachments([]) == []

@patch("app.validate_file")
def test_process_attachments(mock_validate):
    mock_file = Mock()
    mock_file.name = "test.txt"
    assert len(process_attachments([mock_file])) == 1
