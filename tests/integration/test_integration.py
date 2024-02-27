import dataclasses
import pathlib
import shutil
import subprocess
import typing

import pytest

RESOURCE_DIR = pathlib.Path(__file__).parent / "resources"


@dataclasses.dataclass
class RunResult:
    script: str
    packages: typing.Tuple[pathlib.Path]


def run_export_packages(
    tmp_path, pyproject, extra_args: typing.Iterable[str] = ()
) -> RunResult:
    shutil.copyfile(pyproject, tmp_path / "pyproject.toml")
    out_dir = tmp_path / "out"
    script_fname = tmp_path / "script.sh"
    subprocess.check_call(
        [
            "poetry",
            "export-packages",
            *extra_args,
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


def test_my_single_file(tmp_path):
    """A simple project with a singular package"""
    rv = run_export_packages(
        tmp_path, RESOURCE_DIR / "my_single_file" / "pyproject.toml"
    )
    assert len(rv.packages) == 0
    assert rv.script.splitlines() == [
        "#! /bin/sh",
        "",
        "",
    ]


@pytest.mark.parametrize(
    "params, exp_packages, exp_missing_packages",
    [
        ([], ["antigravity"], ["black", "pytest"]),
        (["--only", "pytest"], ["pytest"], ["black", "antigravity"]),
        (["--with", "dev", "--with", "pytest"], ["pytest", "black", "antigravity"], []),
    ],
)
def test_grouped(tmp_path, params, exp_packages, exp_missing_packages):
    rv = run_export_packages(
        tmp_path,
        RESOURCE_DIR / "grouped" / "pyproject.toml",
        extra_args=params,
    )
    assert len(rv.packages) > 0
    for expected in exp_packages:
        assert any(expected in pkg.name for pkg in rv.packages), expected
    for must_be_missing in exp_missing_packages:
        assert all(
            must_be_missing not in pkg.name for pkg in rv.packages
        ), must_be_missing


@pytest.mark.parametrize(
    "platform, exp_pkg_name",
    [
        ("linux", "manylinux"),
        ("win32", "win32"),
    ],
)
def test_ruff(tmp_path, platform, exp_pkg_name):
    rv = run_export_packages(
        tmp_path,
        RESOURCE_DIR / "ruff" / "pyproject.toml",
        extra_args=["--platform", platform],
    )
    assert len(rv.packages) > 0
    ruff_pkg = [el.name for el in rv.packages if el.name.startswith("ruff-")]
    assert len(ruff_pkg) == 1, "There must be only one"
    ruff_pkg = ruff_pkg[0]
    assert exp_pkg_name in ruff_pkg
