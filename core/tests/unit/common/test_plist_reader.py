import pathlib
import plistlib
from pyexpat import ExpatError

import pytest

from core.common.plist_reader import read_plist
from core.exceptions.common import InvalidFileContent


class TestParseXctestrunContent:
    def test_reading_valid_xctestrun(self, example_xctestrun_path):
        """
        GIVEN valid xctestrun file

        WHEN content is read

        THEN the result should be a dictionary
        """
        result = read_plist(example_xctestrun_path)
        assert isinstance(result, dict)

    def test_reading_non_existing_file(self):
        """
        GIVEN non-existing file

        WHEN content is read

        THEN FileNotFoundError should be raised
        """
        with pytest.raises(FileNotFoundError):
            read_plist("non-existing-file")

    def test_invalid_file(self, tmp_path):
        """
        GIVEN invalid file

        WHEN content is read

        THEN InvalidFileContent should be raised
        AND The cause should be plistlib.InvalidFileException
        """
        tmp_file = pathlib.Path(tmp_path, "invalid_file")
        tmp_file.write_bytes(b"Invalid content")

        with pytest.raises(InvalidFileContent, match="Failed to parse plist file") as e:
            read_plist(tmp_file.absolute().as_posix())

        assert isinstance(e.value.__cause__, plistlib.InvalidFileException)

    def test_plist_is_not_dict(self, tmp_path):
        """
        GIVEN plist file that is not a dictionary

        WHEN content is read

        THEN InvalidFileContent should be raised
        """
        tmp_file = pathlib.Path(tmp_path, "invalid_file")
        tmp_file.write_bytes(b"<plist><string>test</string></plist>")

        with pytest.raises(
            InvalidFileContent, match="content is not a dictionary"
        ) as e:
            read_plist(tmp_file.absolute().as_posix())

    def test_broken_plist_content(self, tmp_path):
        """
        GIVEN plist file that is broken

        WHEN content is read

        THEN InvalidFileContent should be raised
        AND the cause should be ExpatError
        """
        tmp_file = pathlib.Path(tmp_path, "invalid_file")
        tmp_file.write_bytes(b"<plist><string>test</string>")

        with pytest.raises(InvalidFileContent, match="Failed to parse plist file") as e:
            read_plist(tmp_file.absolute().as_posix())

        assert isinstance(e.value.__cause__, ExpatError)
