import json
import pathlib
import typing

default_config = {
    "compilerBin": "g++", "compileFlags": ["-O2", "-std=c++17"], "tests": 200, "find": 1,
    "folder": "test_cases"
}
qstress_path = pathlib.Path.home() / ".qstress"

def get_config() -> dict[str, typing.Any]:

    if not qstress_path.exists():
        qstress_path.mkdir()

    config_path = qstress_path / "config.json"

    if not config_path.exists():
        with config_path.open("w+") as file:
            json.dump(default_config, file, indent=4)

    with config_path.open("r") as file:
        return json.load(file)

cur_config = default_config | get_config()
