import pytest

import poetry_plugin_export_packages


@pytest.fixture
def path_eq():
    return poetry_plugin_export_packages.export_output.PathEq()


def test_same_file_different_modes_not_eq(tmp_path, path_eq):
    """A difference in file permissions caused for it to be detected as non-equal."""
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    for f_path in (f1, f2):
        with f_path.open("w") as fout:
            fout.write("potato")
    f2.chmod(0o777)

    assert path_eq.is_equal(f1, f2)
