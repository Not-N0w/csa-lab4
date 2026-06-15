from pathlib import Path
import subprocess


def test_golden():
    tests_dir = Path("tests")

    for test_case in tests_dir.iterdir():
        if not test_case.is_dir():
            continue

        with open(test_case / "stdin.txt", "r") as stdin_file:
            result = subprocess.run(
                [
                    "python3",
                    "main.py",
                    str(test_case / "simulation.conf"),
                    str(test_case / "code.lisp"),
                ],
                stdin=stdin_file,
                capture_output=True,
                text=True,
            )

        expected = (test_case / "expect.out").read_text()

        assert result.returncode == 0, (
            f"\nSTDOUT:\n{result.stdout}"
            f"\nSTDERR:\n{result.stderr}"
        )
        print(expected.strip())
        print(result.stdout.strip())
        assert expected.strip() in result.stdout.strip(), (
            f"Failed test {test_case.name}"
        )


test_golden()