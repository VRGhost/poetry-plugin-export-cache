import pathlib
import shlex
import shutil
import threading
import typing


class ExportOutput:
    rel_root: pathlib.Path
    out_dir: pathlib.Path
    pip_commands: typing.List[typing.Tuple[str]]
    lock: threading.Lock

    def __init__(self, out_dir: pathlib.Path, rel_root: pathlib.Path):
        self.rel_root = rel_root.absolute()
        self.out_dir = out_dir.absolute()
        self.pip_commands = []
        self.lock = threading.Lock()

    def save_file(self, orig: pathlib.Path) -> pathlib.Path:
        """Save a file in the `out_dir`, return path to the copy"""
        idx = 1
        with self.lock:
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
                raise NotImplementedError(orig)  # pragma: nocover
        return out_fname

    def to_rel_path(self, path: pathlib.Path) -> pathlib.Path:
        return path.relative_to(self.rel_root)

    def add_pip_command(self, cmd: typing.Iterable[str]):
        with self.lock:
            self.pip_commands.append(tuple(cmd))

    def get_pip_script(self, shebang: str) -> str:
        out_lines = [shebang, ""]
        with self.lock:
            for cmd in self.pip_commands:
                out_lines.append(shlex.join(("pip",) + cmd))
        return "\n".join(out_lines + ["", ""])
