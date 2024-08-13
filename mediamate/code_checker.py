"""
This module is designed to check whether the project code complies with the PEP 8 specification.
If the output result is not empty, please adjust or modify the code format.
"""
import subprocess


def run_pylint():
    """
    Runs Pylint on the current directory and prints the output.
    """
    try:
        result = subprocess.run(['pylint', '.', '--disable=C0301'], capture_output=True, text=True, check=False, encoding='utf-8')
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print(f"Standard error output:\n{e.stderr}")


if __name__ == "__main__":
    run_pylint()
