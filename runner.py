import subprocess
import os
import threading
from typing import List, Iterator, cast, Tuple, Dict
import argparse
import json

OUTPUT_DIR = "out"
seperator = ","
TIMEOUT = 70  # Timeout in seconds, Give the solvers 10 seconds to clean up


class LazyPathIterator:
    def __init__(self, path: str, skip: int = 0):
        self.path = path
        self.skip = skip

    def __iter__(self) -> Iterator[str]:

        count = 0

        # Walk through each directory and subdirectory
        for root, _, files in os.walk(self.path):

            # Yield only files ending with .smt2
            for f in files:
                if f.endswith(".smt2"):
                    if count <= self.skip:
                        count += 1
                        continue

                    yield os.path.join(root, f)


def read_config() -> dict:

    with open("config.json", "r") as config_file:
        config = json.load(config_file)

        return config


def benchmark_solver(solver_name: str, solver_command: List[str], input_file: str):
    """
    Runs a benchmark on a single file with a single solver
    param: input_file The full path of the input file
    """

    output = os.path.join(OUTPUT_DIR, f"{os.path.splitext(input_file)[0]}_{solver_name}.out")

    os.makedirs(os.path.dirname(output), exist_ok=True)

    perf_command = ["perf", "stat", *solver_command, input_file]

    try:
        with open(output, "w+") as f:
            try:
                out = subprocess.run(perf_command, timeout=TIMEOUT, capture_output=True)
                f.write(f"{out.returncode}\n{out.stdout.decode('utf-8')}\n{out.stderr.decode('utf-8')}\n")
            except subprocess.TimeoutExpired:
                f.write("hardtimeout")

            except Exception as e:
                f.write(f"3\n{e}\n")  # Error code 3
                print(f"{solver_name} ran into a problem: {e}")

    except Exception as e:
        print(f"Error writing to output file {output}: {e}")


def worker(solver: Tuple[str, List[str]], pool: LazyPathIterator):
    for f in pool:
        try:
            benchmark_solver(solver[0], solver[1], f)
        except Exception as e:
            print(f"Some Exception occured: {e}")


def run(args) -> None:
    solvers_to_run: list[str] = args.solvers
    solver_dict = read_config()
    cast(Dict[str, List[str]], solver_dict)

    # Make sure we have a config for all specified solvers
    if not args.solvers[0] == "all":  # All just runs all from the config
        for solver in solvers_to_run:
            if solver not in solver_dict.keys():
                print(f"Solver {solver} was specified as argument but does not exist in the config")
                return

    selected_solvers = None
    if solvers_to_run[0] == "all":
        selected_solvers = solver_dict.items()
    else:
        selected_solvers = [(name, solver) for name, solver in solver_dict.items() if name in solvers_to_run]  # type: ignore

    if not selected_solvers:
        print("No solver was selected")
        return

    pools = [LazyPathIterator(args.path, args.skip) for _ in selected_solvers]

    threads = []
    for (name, command), pool in zip(selected_solvers, pools):
        print(f"[+] Starting solver {name}")
        threads.append(threading.Thread(target=worker, args=((name, command), pool)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run smt solvers on a given benchmark set")
    parser.add_argument("--skip", type=int, default=0, help="Number of benchmark files to skip")
    parser.add_argument("--solvers",
                        type=str,
                        nargs="+",
                        default=["all"],
                        help="Define which solvers to run from your config.json")
    parser.add_argument("path", type=str, help="Path to the directory containing the benchmarks")
    args = parser.parse_args()

    run(args)
