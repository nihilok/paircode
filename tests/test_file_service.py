import pytest
from paircode.file_service import FileService


directories_to_clean = []


@pytest.fixture(autouse=True)
def cleanup(tmp_path):
    """Cleanup the temporary files created during tests."""
    yield
    for directory in directories_to_clean:
        if directory.exists() and directory.is_dir():
            for item in directory.iterdir():
                if item.is_file():
                    item.unlink()
                else:
                    for subitem in item.iterdir():
                        subitem.unlink()
                    item.rmdir()
            directory.rmdir()

def test_write_and_read_file(tmp_path):
    file_service = FileService(tmp_path)
    test_file = tmp_path / "test.txt"
    directories_to_clean.append(tmp_path)

    content = "Hello, Paircode!"
    file_service.write_to_file("test.txt", content)
    
    read_content = file_service.read_file("test.txt")
    assert read_content == content


def test_list_files(tmp_path):
    file_service = FileService(tmp_path)
    directories_to_clean.append(tmp_path)

    files = ["file1.txt", "file2.txt", "file3.txt"]
    for file in files:
        (tmp_path / file).touch()

    listed_files = file_service.list_files("")
    for file in files:
        assert file in listed_files


def test_write_outside_directory(tmp_path):
    file_service = FileService(tmp_path)
    directories_to_clean.append(tmp_path)

    with pytest.raises(ValueError, match="Access to the specified path is not allowed."):
        file_service.write_to_file("../unauthorized.txt", "Should not work")

def test_read_non_existent_file(tmp_path):
    file_service = FileService(tmp_path)
    directories_to_clean.append(tmp_path)

    with pytest.raises(FileNotFoundError, match="The file does not exist."):
        file_service.read_file("nonexistent.txt")

def test_special_characters_in_file_names(tmp_path):
    file_service = FileService(tmp_path)
    directories_to_clean.append(tmp_path)

    special_file_name = "spécial_chäräctêrs.txt"
    content = "Content with special characters in file name"
    file_service.write_to_file(special_file_name, content)

    read_content = file_service.read_file(special_file_name)
    assert read_content == content

def test_large_file_content(tmp_path):
    file_service = FileService(tmp_path)
    directories_to_clean.append(tmp_path)

    large_content = "A" * 10**6  # 1 million characters
    file_service.write_to_file("largefile.txt", large_content)

    read_content = file_service.read_file("largefile.txt")
    assert read_content == large_content

def test_long_file_path(tmp_path):
    file_service = FileService(tmp_path)
    directories_to_clean.append(tmp_path)

    long_file_name = "a" * 255 + ".txt"
    content = "Testing long file path"
    file_service.write_to_file(long_file_name, content)

    read_content = file_service.read_file(long_file_name)
    assert read_content == content
