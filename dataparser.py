import pandas as pd
import re
import os
from pathlib import Path
from typing import List
import sys

# animation = ["10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"]
animation = ["[■□□□□□□□□□]", "[■■□□□□□□□□]", "[■■■□□□□□□□]", "[■■■■□□□□□□]", "[■■■■■□□□□□]", "[■■■■■■□□□□]", "[■■■■■■■□□□]", "[■■■■■■■■□□]", "[■■■■■■■■■□]", "[■■■■■■■■■■]"]

TIMEOUT_STRING = "timeout"
OSTRICH_TIMEOUT_STRING = "unknown"
CVC5_TIMEOUT_STRING = "cvc5 interrupted by timeout."
PERF_START_STRING = "Performance counter stats for "

type Timeout = "Timeout"


def clean_lines(text):
    return [re.sub(r"\s+", ' ', line).strip() for line in text if line.strip()]


def parse_file(path: str):

    with open(path, "r") as f:
        content = f.readlines()
        stripped_content = clean_lines(content)

        # First is a hard timeout by the script, the others indicate a clean timeout by the parser
        if TIMEOUT_STRING in stripped_content[0] or TIMEOUT_STRING in stripped_content[1] or CVC5_TIMEOUT_STRING in stripped_content[1] or OSTRICH_TIMEOUT_STRING in stripped_content[1]:
            return (1, Timeout)

        exit_code = int(stripped_content[0])

        if exit_code == 0:
            sat = stripped_content[1]  # Sat or unsat
        else:
            return (exit_code, "Error")

        perf_index = next((i for i, s in enumerate(stripped_content) if PERF_START_STRING in s), None)

        if perf_index:
            perf_stats_string = stripped_content[perf_index:]
            additional_info = stripped_content[1:perf_index - 1]

            return (exit_code, sat, perf_stats_string, additional_info)
        else:
            print(f"Error parsing file: {path}")


def parse_perf_stats(stats: List[str]):
    result = {}

    for line in stats[1:]:
        parts = line.split("#")[0].strip()  # Split at '#' and take the part before it
        if not parts:
            continue

        value, key = parts.rsplit(maxsplit=1)  # Split value from the key
        if value.count('.') > 1:
            parts = value.split('.')
            value = "".join(parts[0:-1]) + "." + parts[-1]

        result[key] = value.split(maxsplit=1)[0].replace(",", "")

    return result


def parse_files(files):
    data = []

    print("[+]Parsing files: ", end=None)
    for i, file in enumerate(files):
        filled_blocks = int((i + 1) / len(files) * 10)  # 10 blocks in the bar
        progress_bar = f"[{'■' * filled_blocks}{'□' * (10 - filled_blocks)}] {((i + 1) / len(files)) * 100:.1f}%"
        sys.stdout.write(f"\r{progress_bar}")
        sys.stdout.flush()

        parsed = parse_file(file)
        if not parsed:
            continue

        result = {}

        # Extract the base name of the file
        base_name = os.path.basename(file).replace('.out', '')

        # Split the base name by underscores to separate problem name and solver name
        name_parts = base_name.split('_')

        # Problem name is everything except the last part
        problem_name = '_'.join(name_parts[:-1])

        # Prepend the last directory to the problem name
        problem_name = f"{os.path.dirname(file)}/{problem_name}"

        # Solver name is the last part
        solver_name = name_parts[-1]

        if parsed[0] != 0:
            if parsed[1] == Timeout:
                result = {"problem": problem_name, "solver": solver_name, "status": "Timeout", "sanity_sat": None}
            else:
                result = {"problem": problem_name, "solver": solver_name, "status": "Error", "sanity_sat": None}

        else:
            perf_stats = parse_perf_stats(parsed[2])
            sanity_sat = parsed[1]

            result = {"problem": problem_name, "solver": solver_name, "status": "Success", "sanity_sat": sanity_sat, **perf_stats}

        data.append(result)

    print("\n[+]Parsing dataframe")

    return pd.DataFrame(data)


def main():
    files = [str(file) for file in Path("out").rglob("*.out")]
    df = parse_files(files)

    return df


if __name__ == "__main__":
    df = main()
    df.to_csv("QF_S_PARSED.csv")
