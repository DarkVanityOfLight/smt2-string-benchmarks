from concurrent.futures import ProcessPoolExecutor
import subprocess
import os
import pathlib
import queue
import threading
from typing import Tuple, List
from typing import Iterator

solvers = {
        "cvc5": ["/home/lichtner/cvc5"],
        "ostrich": ["/home/lichtner/ostrich/ostrich", "-logo", "-runtime", "+quiet"],
        "z3alpha": ["/software/python/3.12.0/bin/python3.12", "/home/lichtner/z3alpha/smtcomp24/z3alpha.py"],
        "z3noodler": ["/home/lichtner/z3-noodler"]
    }


OUTPUT_DIR = "out"
seperator = ","
TIMEOUT = 60 # Timeout in seconds

class LazyPathIterator:
    def __init__(self, path: str):
        self.path = path

    def __iter__(self) -> Iterator[str]:
        # Walk through each directory and subdirectory
        for root, _, files in os.walk(self.path):
            # Yield only files ending with .smt2
            for f in files:
                if f.endswith(".smt2"):
                    yield os.path.join(root, f)


def benchmark_solver(solver_name: str, solver_command: List[str], input_file: str) -> str:
    """
    Runs a benchmark on a single file with a single solver
    param: input_file The full path of the input file
    """

    with open(f"{solver_name}.log", "a") as f:
        f.write(f"{input_file}\n")

    output = os.path.join(OUTPUT_DIR, f"{os.path.splitext(input_file)[0]}_{solver_name}.out")

    os.makedirs(os.path.dirname(output), exist_ok=True)


    perf_command = ["perf", "stat", *solver_command, input_file]

    with open(output, "w+") as f:
        try:
            out = subprocess.run(perf_command, timeout=TIMEOUT, capture_output=True)
            f.write(f"{out.returncode}\n{out.stdout.decode('utf-8')}\n{out.stderr.decode('utf-8')}\n")
        except subprocess.TimeoutExpired:
            f.write(f"timeout")



def worker(solver_name: str, pool: LazyPathIterator):
    for f in pool:
        benchmark_solver(solver_name, solvers[solver_name], f)



def run(path):
    pool1 = LazyPathIterator(path)
    pool2 = LazyPathIterator(path)
    pool3 = LazyPathIterator(path)
    pool4 = LazyPathIterator(path)

    solver1 = "cvc5"
    solver2 = "ostrich"
    solver3 = "z3noodler"
    solver4 = "z3alpha"


    with open(f"{solver1}.log", "w+"):
        pass

    with open(f"{solver2}.log","w+"):
        pass

    with open(f"{solver3}.log","w+"):
        pass

    with open(f"{solver4}.log", "w+"):
        pass

    # Creating threads for each solver
    thread1 = threading.Thread(target=worker, args=(solver1, pool1))
    thread2 = threading.Thread(target=worker, args=(solver2, pool2))
    thread3 = threading.Thread(target=worker, args=(solver3, pool3))
    thread4 = threading.Thread(target=worker, args=(solver4, pool4))
    
    # Start threads
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()
    
    # Wait for threads to complete
    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()

if __name__ == "__main__":
    run("benchmarks/non-incremental")
