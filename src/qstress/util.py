import pathlib
import shutil
import subprocess
import typing

import rich.console

from .config import cur_config
from .config import qstress_path

console = rich.console.Console()

data_path = qstress_path / "_data"

def get_path(file: str) -> pathlib.Path:

    return data_path / file

def compile_file(source_file: str, bin_file: str, status: typing.Any) -> bool:

    if not data_path.exists():
        data_path.mkdir()

    status.update(f"Compiling [bold]{source_file}[/]")

    process = subprocess.run(
        [shutil.which(cur_config["compilerBin"])] + cur_config["compileFlags"] +
        [str(pathlib.Path.cwd() / source_file), "-o", str(get_path(bin_file))]
    )

    if process.returncode:
        console.print()
        console.print(f"[red]Failed to compile [bold]{source_file}[/][/]")
        return False

    console.print(f"Compiled [bold]{source_file}[/]")

    return True

def run_bin(bin_file: str, **kwargs) -> subprocess.CompletedProcess:

    return subprocess.run([str(get_path(bin_file))], **kwargs)
