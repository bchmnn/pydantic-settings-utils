import shlex
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent

readme_template = root.joinpath("scripts/README.template.md")


readme = ""

with open(readme_template, "r") as file:
    for line in file:
        if line.startswith("$$$"):
            command = line.removeprefix("$$$")
            command = shlex.split(command)
            result = subprocess.run(
                command,
                capture_output=True,
                check=True,
                cwd=root,
            )
            readme += result.stdout.decode()
        else:
            readme += line

with open(root.joinpath("README.md"), "w") as file:
    file.write(readme)
