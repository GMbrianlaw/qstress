import filecmp
import pathlib
import shutil
import typing

import rich.panel
import typer

from .config import cur_config
from .util import compile_file
from .util import console
from .util import data_path
from .util import get_path
from .util import run_bin

app = typer.Typer(add_completion=False)

@app.command()
def check(
    main_file: typing.Annotated[str, typer.Argument(help="File to stress test")],
    check_file: typing.Annotated[str, typer.Argument(help="File to check outputs")],
    gen_file: typing.Annotated[str, typer.Argument(help="File to generate tests")],
    tests: typing.Annotated[
        int, typer.Option(help="Maximum number of tests to generate")
    ] = cur_config["tests"],
    find: typing.Annotated[
        int, typer.Option(help="Maximum number of failing cases to find")
    ] = cur_config["find"],
    folder: typing.Annotated[
        str, typer.Option(help="Folder to save failing test cases")
    ] = cur_config["folder"]
) -> None:
    """
    Generates test cases and checks whether output is valid.
    """

    tests_folder = pathlib.Path.cwd() / folder

    if not tests_folder.exists():
        tests_folder.mkdir()
    else:
        for x in tests_folder.iterdir():
            x.unlink()

    console.print()

    with console.status("") as status:
        if not compile_file(main_file, "main", status):
            return
        if not compile_file(check_file, "check", status):
            return
        if not compile_file(gen_file, "gen", status):
            return
        console.print()
        found = 0
        for i in range(tests):
            status.update(f"Running on test {i + 1} ({found} / {tests})")
            with get_path("input.txt").open("w+") as file:
                run_bin("gen", stdout=file)
            with get_path("input.txt").open("r") as file:
                output = run_bin("main", capture_output=True, stdin=file, text=True).stdout
                valid = run_bin(
                    "check", capture_output=True, cwd=data_path, input=output, text=True
                ).stdout.strip()
                if valid != "1":
                    shutil.copy(get_path("input.txt"), tests_folder / f"input_{found + 1}.txt")
                    found += 1
                if found == find:
                    break
        console.print(
            "[green]Passed {tests} test cases[/]" if found == 0 else
            f"[red]Found {found} / {find} failing test cases[/]"
        )

@app.command()
def cmp(
    main_file: typing.Annotated[str, typer.Argument(help="File to stress test")],
    slow_file: typing.Annotated[str, typer.Argument(help="File to compare against")],
    gen_file: typing.Annotated[str, typer.Argument(help="File to generate tests")],
    tests: typing.Annotated[
        int, typer.Option(help="Maximum number of tests to generate")
    ] = cur_config["tests"],
    find: typing.Annotated[
        int, typer.Option(help="Maximum number of failing cases to find")
    ] = cur_config["find"],
    folder: typing.Annotated[
        str, typer.Option(help="Folder to save failing test cases")
    ] = cur_config["folder"]
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
        if not compile_file(main_file, "main", status):
            return
        if not compile_file(slow_file, "slow", status):
            return
        if not compile_file(gen_file, "gen", status):
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
            f"[green]Passed {tests} test cases[/]" if found == 0 else
            f"[red]Found {found} / {find} failing test cases[/]"
        )

@app.command()
def config() -> None:
    """
    Outputs the current config values.
    """

    console.print()
    console.print(cur_config)

@app.command()
def gen(gen_file: typing.Annotated[str, typer.Argument(help="File to generate tests")]) -> None:
    """
    Generates a test case and displays it.
    """

    console.print()

    with console.status("") as status:
        if not compile_file(gen_file, "gen", status):
            return

    console.print()
    console.print(rich.panel.Panel("\n" + run_bin("gen", capture_output=True, text=True).stdout))

@app.command()
def view(
    test: typing.Annotated[int, typer.Argument(help="Test case to view")] = 0,
    folder: typing.Annotated[
        str, typer.Option(help="Folder to find test cases")
    ] = cur_config["folder"],
    checker: typing.Annotated[bool, typer.Option(help="Use checker mode")] = False
) -> None:
    """
    Views output for failing test cases using compiled binaries.
    """

    console.print()

    test_folder = pathlib.Path.cwd() / folder

    def display(test_idx: int) -> None:
        data = (test_folder / f"input_{test_idx}.txt").read_text()
        name = "Output" if test == 0 else "Output (main)"
        text = ["\n", "[bold]Input:[/]", "\n", "\n", data, "\n", f"[bold]{name}:[/]", "\n", "\n"]
        text.append(run_bin("main", capture_output=True, input=data, text=True).stdout)
        if not checker:
            text.extend(["\n", "[bold]Output (slow):[/]", "\n", "\n"])
            text.append(run_bin("slow", capture_output=True, input=data, text=True).stdout)
        console.print(rich.panel.Panel("".join(text), title=f"[bold]Test {test_idx}[/]"))
        console.print()

    if test == 0:
        for i in range(1, len(list(test_folder.iterdir())) + 1):
            display(i)
    else:
        display(test)
