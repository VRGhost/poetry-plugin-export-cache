import poetry.console.application
import poetry.plugins
import typing
import pathlib
from poetry.core.packages.dependency_group import MAIN_GROUP
from cleo.helpers import option
from poetry.console.commands.command import Command
from poetry.console.commands.group_command import GroupCommand
import poetry.installation.installer
import poetry.installation.executor
import poetry.utils.env
import tempfile
import sys
import shutil
import shlex

class ExportOutput:

    rel_root: pathlib.Path
    out_dir: pathlib.Path
    pip_commands : typing.List[typing.Tuple[str]]
    
    def __init__(self, out_dir: pathlib.Path, rel_root: pathlib.Path):
        self.rel_root = rel_root.absolute()
        self.out_dir = out_dir.absolute()
        self.pip_commands = []

    def save_file(self, orig: pathlib.Path) -> pathlib.Path:
        """Save a file in the `out_dir`, return path to the copy"""
        idx = 1
        out_fname = self.out_dir / orig.name
        while out_fname.exists():
            # Ensure output name uniqueness
            idx += 1
            out_fname = self.out_dir / f"{orig.stem}_{idx}{''.join(orig.suffixes)}"
        if orig.is_file():
            shutil.copyfile(orig, out_fname)
        elif orig.is_dir():
            shutil.copytree(orig, out_fname)
        else:
            raise NotImplementedError(orig)
        return out_fname
    
    def to_rel_path(self, path: pathlib.Path) -> pathlib.Path:
        return path.relative_to(self.rel_root)

    def add_pip_command(self, cmd: typing.Iterable[str]):
        self.pip_commands.append(tuple(cmd))

    def get_pip_script(self, shebang:str) -> str:
        out_lines = [shebang, '']
        for cmd in self.pip_commands:
            out_lines.append(shlex.join(('pip',)+ cmd))
        return '\n'.join(out_lines)

class ExportEnv(poetry.utils.env.NullEnv):

    export_out: ExportOutput

    def __init__(self, export_plugin_output:ExportOutput, **kwargs):
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
        if '--prefix' in logged_args:
            # remove --prefix <arg>
            pref_idx = logged_args.index('--prefix')
            logged_args[pref_idx:pref_idx+2] = []
        
        self.export_out.add_pip_command(logged_args)
        return ""

    def execute(self, *args, **kwargs) -> int:
        raise NotImplementedError

class ExportExecutor(poetry.installation.executor.Executor):
    """An exporting executor"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._use_modern_installation = False # Force using pip

class ExportPackagesCommand(GroupCommand):
    name = "export-packages"
    description = "export python packages"

    options = [
        option(
            "output_dir",
            short_name="o",
            description="Directory to save packages to.",
            flag=False,
            value_required=True,
            default=str(pathlib.Path('.', 'export-packages'))
        ),
        option(
            "shebang",
            description="Shebang to start the generated pip install script with",
            flag=False,
            value_required=True,
            default="#! /bin/sh"
        ),
        option(
            "output_script",
            short_name="f",
            description="Place to save output script to.",
            flag=False,
            value_required=False,
            default=None
        ),
        *GroupCommand._group_dependency_options(),
    ]

    @property
    def default_groups(self) -> typing.Set[str]:
        return {MAIN_GROUP}

    def handle(self) -> int:
        my_poetry = self.poetry
        out_script : typing.Optional[pathlib.Path] = None
        log_out_script: bool = self.io.is_verbose()
        if (out_script_input := self.option('output_script')) is not None:
            out_script = pathlib.Path(out_script_input)
        else:
            log_out_script = True
        out_dir = pathlib.Path(self.option("output_dir")).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        my_out = ExportOutput(out_dir, rel_root=pathlib.Path('.'))
        
        with tempfile.TemporaryDirectory(prefix='poetry-export-packages') as tmpd:
            env = ExportEnv(export_plugin_output=my_out, path=pathlib.Path(tmpd), execute=False)
            installer = poetry.installation.installer.Installer(
                io=self.io,
                env=env,
                package=my_poetry.package,
                locker=my_poetry.locker,
                pool=my_poetry.pool,
                config=my_poetry.config,
                executor=ExportExecutor(
                    env=env,
                    pool=my_poetry.pool,
                    config=my_poetry.config,
                    io=self.io
                )
            )

            if (rc := installer.run()) != 0:
                self.line_error("Poetry installer returned an error")
                return rc

        out_script_text = my_out.get_pip_script(str(self.option('shebang')))
        if log_out_script:
            for line in out_script_text.splitlines():
                self.info(f"Install script: {line}")
        if out_script is not None:
            with out_script.open('w') as fout:
                fout.write(out_script_text)
        return 0



class ExportPackagesPlugin(poetry.plugins.application_plugin.ApplicationPlugin):
    
    @property
    def commands(self) -> typing.List[Command]:
        return [ExportPackagesCommand]
