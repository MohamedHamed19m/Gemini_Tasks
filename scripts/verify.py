import subprocess
import os
import sys


def run_tests():
    print("Running Python tests from scripts/verify.py...")
    # Add server to PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "server")

    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "server/tests/"],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        print(result.stdout)
        print("✓ Tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("✗ Tests failed!")
        print(e.stdout)
        print(e.stderr)
        return False


if __name__ == "__main__":
    if run_tests():
        sys.exit(0)
    else:
        sys.exit(1)
