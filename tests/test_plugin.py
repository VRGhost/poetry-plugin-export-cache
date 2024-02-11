import pathlib

import poetry.console.application
import pytest

import poetry_plugin_export_packages


class TestExportOutput:
    @pytest.fixture
    def test_file(self, tmp_path):
        file_dir = tmp_path / "test_file_dir"
        file_dir.mkdir()
        my_file = file_dir / "test.txt"
        with my_file.open("w") as fout:
            fout.write("hello")
        return my_file

    @pytest.fixture
    def export_output(self, tmp_path):
        my_root = pathlib.Path(tmp_path / "export_out")
        my_root.mkdir()
        out_dir = my_root / "d1" / "d2" / "d3" / "out"
        out_dir.mkdir(parents=True)
        return poetry_plugin_export_packages.plugin.ExportOutput(
            out_dir=out_dir, rel_root=my_root
        )

    def test_save_file(self, tmp_path, test_file, export_output):
        out_fname1 = export_output.save_file(test_file)
        assert str(out_fname1) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test.txt"
        )
        assert out_fname1.is_file()
        out_fname2 = export_output.save_file(test_file)
        assert str(out_fname2) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test_2.txt"
        )
        assert out_fname2.is_file()

    def test_save_dir(self, tmp_path, test_file, export_output):
        out_fname1 = export_output.save_file(test_file.parent)
        assert str(out_fname1) == str(
            tmp_path / "export_out" / "d1" / "d2" / "d3" / "out" / "test_file_dir"
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


class TestExportCommand:
    @pytest.fixture(autouse=True)
    def mock_installer_cls(self, mocker):
        installer_cls = mocker.patch("poetry.installation.installer.Installer")
        installer_cls.return_value.run.return_value = 0
        return installer_cls

    @pytest.fixture
    def mock_installer(self, mock_installer_cls):
        return mock_installer_cls.return_value

    @pytest.fixture
    def command(self, mocker):
        out = poetry_plugin_export_packages.plugin.ExportPackagesCommand()
        option_mock = mocker.patch.object(out, "option")
        option_mock.values = {
            "output-dir": "./testout",
        }
        option_mock.side_effect = lambda key, default=None: option_mock.values.get(
            key, default
        )
        mocker.patch.object(out, "_io")
        app_mock = mocker.patch.object(
            out, "_application", spec=poetry.console.application.Application
        )
        app_mock.poetry.config.installer_max_workers = 1
        return out

    def test_def_groups(self, command):
        assert command.default_groups == {"main"}

    def test_no_out_script(self, mocker, command):
        command.option.values.update({"output-script": None, "shebang": "#! potato"})
        rc = command.handle()
        assert rc == 0

        command.io.write_line.assert_any_call(
            "<info>Install script: #! potato</>", verbosity=mocker.ANY
        )

    def test_run_rc(self, mock_installer, command):
        mock_installer.run.return_value = 4242
        rc = command.handle()
        assert rc == 4242
