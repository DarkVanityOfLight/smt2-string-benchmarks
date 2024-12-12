import subprocess
import os
import threading
from typing import List
from typing import Iterator

solvers = {
    "cvc5": ["/home/lichtner/cvc5", "--tlimit", "60000"],
    "ostrich": ["/home/lichtner/ostrich/ostrich", "-logo", "-runtime", "+quiet", "-timeout=60000"],
    "z3alpha": ["/software/python/3.12.0/bin/python3.12", "/home/lichtner/z3alpha/smtcomp24/z3alpha.py", "-T:60"],
    "z3noodler": ["/home/lichtner/z3-noodler", "-T:60"],
    "z3": ["/home/lichtner/.local/bin/z3", "-T:60"]
}

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


def worker(solver_name: str, pool: LazyPathIterator):
    for f in pool:
        try:
            benchmark_solver(solver_name, solvers[solver_name], f)
        except Exception as e:
            print(f"Some Exception occured: {e}")


def run(path):
    solvers = ["cvc5", "ostrich", "z3noodler", "z3alpha", "z3"]
    pools = [LazyPathIterator(path) for _ in solvers]

    threads = []
    for solver, pool in zip(solvers, pools):
        threads.append(threading.Thread(target=worker, args=(solver, pool)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    run("benchmarks/non-incremental/QF_SLIA")
