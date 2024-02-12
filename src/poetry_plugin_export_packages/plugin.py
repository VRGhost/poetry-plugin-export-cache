import pathlib
import tempfile
import typing

import poetry.console.application
import poetry.installation.executor
import poetry.installation.installer
import poetry.plugins
import poetry.utils.env
from cleo.helpers import option
from poetry.console.commands.command import Command
from poetry.console.commands.group_command import GroupCommand
from poetry.core.packages.dependency_group import MAIN_GROUP

from .export_output import ExportOutput


class ExportEnv(poetry.utils.env.NullEnv):
    export_out: ExportOutput

    def __init__(self, export_plugin_output: ExportOutput, **kwargs):
        super().__init__(**kwargs)
        self.export_out = export_plugin_output

    def run_pip(self, *args: str, **kwargs: typing.Any) -> str:
        assert not kwargs, f"Unexpected kwargs: {kwargs}"

        logged_args = list(args)
        # Process the installed package
        installed_path = pathlib.Path(args[-1])
        if installed_path.exists():
            new_path = self.export_out.save_file(installed_path)
            rel_path = self.export_out.to_rel_path(new_path)
            logged_args[-1] = str(rel_path)
        else:
            pass  # Assume a remote URI

        # Mist arg meddling
        if "--prefix" in logged_args:
            # remove --prefix <arg>
            pref_idx = logged_args.index("--prefix")
            logged_args[pref_idx : pref_idx + 2] = []

        self.export_out.add_pip_command(logged_args)
        return ""

    def execute(self, *args, **kwargs) -> int:
        raise NotImplementedError  # pragma: nocover

    @property
    def sys_path(self) -> typing.List[str]:
        # Do not return env parents' path to force
        #   all deps to pass through installation"""
        return [
            str(self._path.resolve()),
        ]


class ExportExecutor(poetry.installation.executor.Executor):
    """An exporting executor"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._use_modern_installation = False  # Force using pip


class ExportPackagesCommand(GroupCommand):
    name = "export-packages"
    description = "export python packages"

    options = [
        option(
            "output-dir",
            short_name="o",
            description="Directory to save packages to.",
            flag=False,
            value_required=True,
            default=str(pathlib.Path(".", "export-packages")),
        ),
        option(
            "shebang",
            description="Shebang to start the generated pip install script with",
            flag=False,
            value_required=True,
            default="#! /bin/sh",
        ),
        option(
            "output-script",
            short_name="f",
            description="Place to save output script to.",
            flag=False,
            value_required=False,
            default=None,
        ),
        *GroupCommand._group_dependency_options(),
    ]

    @property
    def default_groups(self) -> typing.Set[str]:
        return {MAIN_GROUP}

    def handle(self) -> int:
        my_poetry = self.poetry
        out_script: typing.Optional[pathlib.Path] = None
        log_out_script: bool = self.io.is_verbose()
        if (out_script_input := self.option("output-script")) is not None:
            out_script = pathlib.Path(out_script_input)
        else:
            log_out_script = True
        out_dir = pathlib.Path(self.option("output-dir")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        if out_script:
            rel_root = out_script.parent
        else:
            rel_root = pathlib.Path("/")
        my_out = ExportOutput(out_dir, rel_root=rel_root)

        with tempfile.TemporaryDirectory(prefix="poetry-export-packages") as tmpd:
            env = ExportEnv(
                export_plugin_output=my_out, path=pathlib.Path(tmpd), execute=False
            )
            installer = poetry.installation.installer.Installer(
                io=self.io,
                env=env,
                package=my_poetry.package,
                locker=my_poetry.locker,
                pool=my_poetry.pool,
                config=my_poetry.config,
                executor=ExportExecutor(
                    env=env, pool=my_poetry.pool, config=my_poetry.config, io=self.io
                ),
            )
            installer.only_groups(self.activated_groups)

            if (rc := installer.run()) != 0:
                self.line_error("Poetry installer returned an error")
                return rc

        out_script_text = my_out.get_pip_script(str(self.option("shebang")))
        if log_out_script:
            for line in out_script_text.splitlines():
                self.info(f"Install script: {line}")
        if out_script is not None:
            with out_script.open("w") as fout:
                fout.write(out_script_text)
        return 0


class ExportPackagesPlugin(poetry.plugins.application_plugin.ApplicationPlugin):
    @property
    def commands(self) -> typing.List[Command]:
        return [ExportPackagesCommand]
