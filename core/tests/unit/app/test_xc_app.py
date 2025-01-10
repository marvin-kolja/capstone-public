import pathlib
import shutil

import pytest

from core.xc.app_bundle.bundle_interface import AppBundle


class TestXcApp:
    def test_parse_info_plist(self, tmp_path, example_info_plist_path):
        """
        GIVEN: A path to an .app package.
        AND: A valid Info.plist file in the .app package.

        WHEN: The `parse_info_plist` method is called.

        THEN: The Info.plist file is read and parsed correctly.
        """
        fake_app_path = pathlib.Path(tmp_path, "Placeholder.app")
        fake_app_path.mkdir()
        # Copy file example `Info.plist` to the fake app path.
        shutil.copyfile(example_info_plist_path, fake_app_path.joinpath("Info.plist"))

        app = AppBundle(fake_app_path.absolute().as_posix())

        info_plist = app.parse_info_plist()

        assert info_plist.CFBundlePackageType == "APPL"
        assert info_plist.CFBundleIdentifier == "com.example.Placeholder"
        assert info_plist.CFBundleName == "Placeholder"
        assert info_plist.CFBundleDisplayName is None
        assert info_plist.MinimumOSVersion == "17.3"
        assert info_plist.LSRequiresIPhoneOS is True

    def test_parse_info_plist_file_not_found(self, tmp_path):
        """
        GIVEN: A path to an .app package.
        AND: No Info.plist file in the .app package.

        WHEN: The `parse_info_plist` method is called.

        THEN: A `FileNotFoundError` is raised.
        """
        fake_app_path = pathlib.Path(tmp_path, "Placeholder.app")
        fake_app_path.mkdir()

        app = AppBundle(fake_app_path.absolute().as_posix())

        with pytest.raises(FileNotFoundError):
            app.parse_info_plist()

    def test_path_property(self, tmp_path):
        """
        GIVEN: A path to an .app package.

        WHEN: The `path` property is accessed.

        THEN: The correct path to the .app package is returned.
        """
        fake_app_path = pathlib.Path(tmp_path, "Placeholder.app")
        fake_app_path.mkdir()

        app = AppBundle(fake_app_path.absolute().as_posix())

        assert app.path == fake_app_path.absolute().as_posix()
