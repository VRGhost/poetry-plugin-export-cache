import errno
import os
import pathlib
import shlex
import shutil
import stat
import threading
import typing
import zlib


class PathEq:
    """A helper class that checks if files (or dirs) are identical
    or not.
    """

    def stat(self, path: pathlib.Path) -> typing.Optional[os.stat_result]:
        try:
            return path.stat()
        except OSError as err:
            if err.errno == errno.ENOENT:
                # File not found
                return None
            else:
                raise  # pragma: nocover

    def _is_eq_files(self, p1: pathlib.Path, p2: pathlib.Path) -> bool:
        with p1.open("rb") as fin1, p2.open("rb") as fin2:
            crc1 = zlib.crc32(fin1.read())
            crc2 = zlib.crc32(fin2.read())
            return crc1 == crc2

    def _is_eq_dirs(self, p1: pathlib.Path, p2: pathlib.Path) -> bool:
        p1_children = sorted(ch.name for ch in p1.iterdir())
        p2_children = sorted(ch.name for ch in p2.iterdir())
        if p1_children != p2_children:
            # Different contents
            return False
        for ch_name in p1_children:
            if not self.is_equal(p1 / ch_name, p2 / ch_name):
                return False
        return True

    def is_equal(self, p1: pathlib.Path, p2: pathlib.Path) -> bool:
        p1_stat = self.stat(p1)
        p2_stat = self.stat(p2)
        if (p1_stat is None) and (p2_stat is None):
            # Neither exists -> return that they are equal
            return True
        elif None in (p1_stat, p2_stat):
            # One exists, the other does not => not equal
            return False
        # else
        assert None not in (p1_stat, p2_stat), "Both paths exist"
        st_dir_or_file = stat.S_IFDIR | stat.S_IFREG
        if (p1_stat.st_mode & st_dir_or_file) != (p2_stat.st_mode & st_dir_or_file):
            # They are of different types (e.g. file vs dir) => Not identical
            return False
        # Both paths exist and of identical type
        if stat.S_ISDIR(p1_stat.st_mode):
            return self._is_eq_dirs(p1, p2)
        assert stat.S_ISREG(p1_stat.st_mode), "Must be file then"
        return self._is_eq_files(p1, p2)


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
                if PathEq().is_equal(orig, out_fname):
                    # If the existing export-ed file is already a copy
                    #  - return that
                    return out_fname
                else:
                    # Ensure output name uniqueness
                    idx += 1
                    out_fname = (
                        self.out_dir / f"{orig.stem}_{idx}{''.join(orig.suffixes)}"
                    )
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
