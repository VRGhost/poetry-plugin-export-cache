import os
import pathlib
import platform
import sys
import tempfile
import typing

import packaging.tags
import poetry.console.application
import poetry.installation.executor
import poetry.installation.installer
import poetry.plugins
import poetry.utils.env
from cleo.helpers import option
from pip import __version__ as DEFAULT_PIP_VERSION  # noqa: N812
from poetry.console.commands.command import Command
from poetry.console.commands.group_command import GroupCommand
from poetry.core.packages.dependency_group import MAIN_GROUP

from .export_output import ExportOutput

DEFAULT_VERSION_INFO = ".".join(str(el) for el in sys.version_info[:3])


class ExportEnv(poetry.utils.env.MockEnv):
    export_out: ExportOutput

    def __init__(self, export_plugin_output: ExportOutput, **kwargs):
        super().__init__(is_venv=False, execute=False, **kwargs)
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

        # Misc arg meddling
        if "--prefix" in logged_args:
            # remove --prefix <arg>
            pref_idx = logged_args.index("--prefix")
            logged_args[pref_idx : pref_idx + 2] = []

        self.export_out.add_pip_command(logged_args)
        return ""

    def execute(self, *args, **kwargs) -> int:
        raise NotImplementedError  # pragma: nocover
    
    def _run(self, *args, **kwargs) -> int:
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
        option(
            "python-implementation",
            description="""
                The Python platform to fetch packages for.

                Default:
                ```
                    >>> import platform
                    >>> print(platform.python_implementation())
                ```
            """,
            flag=False,
            default=platform.python_implementation(),
        ),
        option(
            "platform",
            description="""
                Target platform (e.g 'darwin' or 'linux').

                Default:
                ```
                    >>> import sys
                    >>> print(sys.platform)
                ```
            """,
            flag=False,
            default=sys.platform,
        ),
        option(
            "platform-machine",
            description="""
                Target cpu arch. (e.g. "x86_64").

                Default:
                ```
                    >>> import platform
                    >>> print(platform.machine())
                ```
            """,
            flag=False,
            default=platform.machine(),
        ),
        option(
            "version-info",
            description="""
                The target python version.

                Default:
                ```
                    >>> import sys
                    >>> print(sys.version_info)
                ```
            """,
            flag=False,
            default=DEFAULT_VERSION_INFO,
        ),
        option(
            "pip-version",
            description="""
                Pip version.

                Default:
                ```
                    >>> from pip import __version__
                    >>> print(__version__)
                ```
            """,
            flag=False,
            default=DEFAULT_PIP_VERSION,
        ),
        option(
            "os-name",
            description="""
            Target OS name.

            Default:
            ```
                >>> import os
                >>> print(os.name)
            ```
        """,
            flag=False,
            default=os.name,
        ),
        option(
            "supported-tags",
            description="""
                Supported tags (comma-separated).

                Default:
                ```
                    >>> from packaging.tags import sys_tags
                    >>> print(list(sys_tags()))
                ```
            """,
            flag=False,
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

        # Compute supported_tags for the export env
        python_version = [
            int(el)
            for el in self.option("version-info", DEFAULT_VERSION_INFO).split(".")
        ]
        platform = self.option("platform")
        if supported_tags_str := self.option("supported-tags"):
            supported_tags = set()
            for str_tag in supported_tags_str.split(","):
                supported_tags.update(packaging.tags.parse_tag(str_tag))
            supported_tags = list(supported_tags)
        else:
            supported_tags = list(
                packaging.tags.compatible_tags(
                    python_version=python_version,
                    platforms=[self.option("platform-machine")],
                )
            )

        with tempfile.TemporaryDirectory(prefix="poetry-export-packages") as tmpd:
            env = ExportEnv(
                export_plugin_output=my_out,
                path=pathlib.Path(tmpd),
                version_info=python_version,
                python_implementation=self.option("python-implementation"),
                platform=platform,
                platform_machine=self.option("platform-machine"),
                os_name=self.option("os-name"),
                pip_version=self.option("pip-version", DEFAULT_PIP_VERSION),
                supported_tags=supported_tags,
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
