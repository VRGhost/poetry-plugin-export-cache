import dataclasses
import pathlib
import shutil
import subprocess
import typing

RESOURCE_DIR = pathlib.Path(__file__).parent / "resources"


@dataclasses.dataclass
class RunResult:
    script: str
    packages: typing.Tuple[pathlib.Path]


def run_export_packages(tmp_path, pyproject) -> RunResult:
    shutil.copyfile(pyproject, tmp_path / "pyproject.toml")
    out_dir = tmp_path / "out"
    script_fname = tmp_path / "script.sh"
    subprocess.check_call(
        [
            "poetry",
            "export-packages",
            "--output-dir",
            out_dir,
            "--output-script",
            script_fname,
        ],
        cwd=tmp_path,
    )
    return RunResult(
        script=script_fname.open("r").read(), packages=tuple(out_dir.iterdir())
    )


def test_antigravity(tmp_path):
    """A simple project with a singular package"""
    rv = run_export_packages(tmp_path, RESOURCE_DIR / "antigravity" / "pyproject.toml")
    assert len(rv.packages) == 1
    assert "antigravity" in rv.packages[0].name
    assert rv.script.splitlines() == [
        "#! /bin/sh",
        "",
        (
            "pip install --disable-pip-version-check --isolated --no-input"
            " --no-deps out/antigravity-0.1-py3-none-any.whl"
        ),
        "",
    ]
