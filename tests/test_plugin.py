import pathlib

import pytest

import poetry_plugin_export_packages


class TestExportOutput:
    @pytest.fixture
    def export_output(self, tmp_path):
        my_root = pathlib.Path(tmp_path / "export_out")
        my_root.mkdir()
        out_dir = my_root / "d1" / "d2" / "d3" / "out"
        out_dir.mkdir(parents=True)
        return poetry_plugin_export_packages.plugin.ExportOutput(
            out_dir=out_dir, rel_root=my_root
        )

    def test_save_file(self, tmp_path, export_output):
        my_file = tmp_path / "test.txt"
        with my_file.open("w") as fout:
            fout.write("hello")
        out_fname1 = export_output.save_file(my_file)
        assert str(out_fname1) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test.txt"
        )
        out_fname2 = export_output.save_file(my_file)
        assert str(out_fname2) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test_2.txt"
        )
