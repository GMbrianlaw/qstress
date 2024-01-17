import pathlib
import shutil
import subprocess
import typing

from .config import global_config
from .globals import console
from .globals import internal_path

def get_path(*args: str) -> pathlib.Path:

    path = internal_path

    for x in args:
        path /= x

    return path

def compile_file(source_file: str, bin_file: str, status: typing.Any) -> bool:

    status.update(f"Compiling [bold]{source_file}[/]")

    process = subprocess.run(
        [shutil.which(global_config["compilerBin"])] + global_config["compileFlags"] +
        [str(pathlib.Path.cwd() / source_file), "-o", str(get_path("bin", bin_file))]
    )

    if process.returncode:
        console.print()
        console.print(f"[red]Failed to compile [bold]{source_file}[/][/]")
        return False

    console.print(f"Compiled [bold]{source_file}[/]")

    return True

def run_bin(bin_file: str, **kwargs) -> subprocess.CompletedProcess:

    return subprocess.run([str(get_path("bin", bin_file))], **kwargs)
