import pathlib

import pytest

import poetry_plugin_export_packages


class TestExportOutput:
    @pytest.fixture
    def test_file(self, tmp_path):
        file_dir = tmp_path / "test_file_dir" / "mydir"
        file_dir.mkdir(parents=True)
        my_file = file_dir / "test.txt"
        with my_file.open("w") as fout:
            fout.write("hello")
        with (file_dir / "f2.txt").open("w") as fout:
            fout.write("hello2")
        return my_file

    @pytest.fixture
    def test_file_2(self, tmp_path):
        file_dir = tmp_path / "test_file_dir_2" / "mydir"
        file_dir.mkdir(parents=True)
        my_file = file_dir / "test.txt"
        with my_file.open("w") as fout:
            fout.write("HELLO-I AM DIFFERENT")
        with (file_dir / "f2.txt").open("w") as fout:
            fout.write("dif 2")
        return my_file

    @pytest.fixture
    def export_output(self, tmp_path):
        my_root = pathlib.Path(tmp_path / "export_out")
        my_root.mkdir()
        out_dir = my_root / "d1" / "d2" / "d3" / "out"
        out_dir.mkdir(parents=True)
        return poetry_plugin_export_packages.export_output.ExportOutput(
            out_dir=out_dir, rel_root=my_root
        )

    def test_save_same_file(self, tmp_path, test_file, export_output):
        out_fname1 = export_output.save_file(test_file)
        assert str(out_fname1) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test.txt"
        )
        assert out_fname1.is_file()
        out_fname2 = export_output.save_file(test_file)
        assert out_fname2 == out_fname1, "Same file -> same name"

    def test_save_diff_file(self, tmp_path, test_file, test_file_2, export_output):
        out_fname1 = export_output.save_file(test_file)
        assert str(out_fname1) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test.txt"
        )
        assert out_fname1.is_file()
        out_fname2 = export_output.save_file(test_file_2)
        assert str(out_fname2) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test_2.txt"
        )

    def test_save_same_dir(self, tmp_path, test_file, export_output):
        out_fname1 = export_output.save_file(test_file.parent)
        assert str(out_fname1) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "mydir"
        )
        assert out_fname1.is_dir()
        out_fname2 = export_output.save_file(test_file.parent)
        assert out_fname2 == out_fname1, "Same file -> same name"

    def test_save_dir(self, tmp_path, test_file, export_output):
        out_fname1 = export_output.save_file(test_file.parent)
        assert str(out_fname1) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "mydir"
        )
        assert out_fname1.is_dir()

    def test_rel_path(self, test_file, export_output):
        out_fname = export_output.save_file(test_file)
        rel_path = export_output.to_rel_path(out_fname)
        assert str(rel_path) == "d1/d2/d3/out/test.txt"

    def test_pip_cmd(self, export_output):
        export_output.add_pip_command(["c1", "a1"])
        export_output.add_pip_command(["c2", "a2"])

        assert export_output.get_pip_script("#! shebang").splitlines() == [
            "#! shebang",
            "",
            "pip c1 a1",
            "pip c2 a2",
            "",
        ]
