import pathlib

import poetry.console.application
import pytest

import poetry_plugin_export_packages


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
