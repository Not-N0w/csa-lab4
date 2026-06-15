from pathlib import Path
import subprocess


def test_golden():
    tests_dir = Path("tests")

    for test_case in tests_dir.iterdir():
        if not test_case.is_dir():
            continue

        result = subprocess.run(
            [
                "python3",
                "main.py",
                str(test_case / "simulation.conf"),
                str(test_case / "io.in"),
                str(test_case / "code.lisp"),
            ],
            capture_output=True,
            text=True,
        )

        expected = (test_case / "expect.out").read_text()

        assert result.returncode == 0
        assert expected.strip() in result.stdout.strip(), (
            f"Failed test {test_case.name}"
        )

test_golden()