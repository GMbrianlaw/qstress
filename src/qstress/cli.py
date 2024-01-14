import filecmp
import pathlib
import shutil
import subprocess
import typing

import rich
import typer

from .config import default_config
from .config import get_config
from .config import qstress_path

app = typer.Typer(add_completion=False)
console = rich.console.Console()

config = default_config | get_config()
data_path = qstress_path / "_data"

def get_path(file: str) -> pathlib.Path:

    return data_path / file

def compile(source_file: str, bin_file: str, status: typing.Any) -> bool:

    if not data_path.exists():
        data_path.mkdir()

    status.update(f"Compiling [bold]{source_file}[/]")

    process = subprocess.run(
        [shutil.which(config["compilerBin"])] + config["compileFlags"] +
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

@app.command()
def check() -> None:

    pass

@app.command()
def cmp(
    main_file: typing.Annotated[str, typer.Argument(help="File to stress test")],
    slow_file: typing.Annotated[str, typer.Argument(help="File to compare against")],
    gen_file: typing.Annotated[str, typer.Argument(help="File to generate tests")],
    tests: typing.Annotated[
        int, typer.Option(help="Maximum number of tests to generate")
    ] = config["tests"],
    find: typing.Annotated[
        int, typer.Option(help="Maximum number of failing cases to find")
    ] = config["find"],
    folder: typing.Annotated[
        str, typer.Option(help="Folder to save failing cases")
    ] = config["folder"]
) -> None:
    """
    Generates test cases and compares outputs from two programs.
    """

    tests_folder = pathlib.Path.cwd() / folder

    if not tests_folder.exists():
        tests_folder.mkdir()
    else:
        for x in tests_folder.iterdir():
            x.unlink()

    console.print()

    with console.status("") as status:
        if not compile(main_file, "main", status):
            return
        if not compile(slow_file, "slow", status):
            return
        if not compile(gen_file, "gen", status):
            return
        console.print()
        found = 0
        for i in range(tests):
            status.update(f"Running on test {i + 1} ({found} / {tests})")
            data = run_bin("gen", capture_output=True, text=True).stdout
            with get_path("out_1.txt").open("w+") as output_file:
                run_bin("main", input=data, stdout=output_file, text=True)
            with get_path("out_2.txt").open("w+") as output_file:
                run_bin("slow", input=data, stdout=output_file, text=True)
            if (not filecmp.cmp(str(get_path("out_1.txt")), str(get_path("out_2.txt")), False)):
                with (tests_folder / f"input_{found + 1}.txt").open("w+") as file:
                    file.write(data)
                found += 1
            if found == find:
                break
        console.print(
            "[green]All tests passed[/]" if found == 0 else
            f"[red]Found {found} / {find} failing test cases[/]"
        )
