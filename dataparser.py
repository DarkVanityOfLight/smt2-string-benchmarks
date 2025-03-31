import pandas as pd
import re
import os
from pathlib import Path
from typing import List, Set, Tuple, Dict
import sys
import argparse
import json

TIMEOUT_STRING = "timeout"
OSTRICH_TIMEOUT_STRING = "unknown"
CVC5_TIMEOUT_STRING = "cvc5 interrupted by timeout."
PERF_START_STRING = "Performance counter stats for "

Timeout = "Timeout"


def clean_lines(text):
    return [re.sub(r"\s+", ' ', line).strip() for line in text if line.strip()]


def parse_file(path: str):

    # This is a bit messy but what can you do
    try:
        with open(path, "r") as f:
            content = f.readlines()
            stripped_content = clean_lines(content)

            if len(stripped_content) == 0:
                return (2, "Error")

            # First is a hard timeout by the script, the others indicate a clean timeout by the parser
            if TIMEOUT_STRING in stripped_content[0] or ( len(stripped_content) > 1 and (TIMEOUT_STRING in stripped_content[1] or CVC5_TIMEOUT_STRING in stripped_content[1] or OSTRICH_TIMEOUT_STRING in stripped_content[1])):
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
    except Exception as e:
        print(f"Error {e} while parsing file {path}")
        return (3, "Error")


def parse_perf_stats(stats: List[str]):
    result = {}

    for line in stats[1:]:
        parts = line.split("#")[0].strip()  # Split at '#' and take the part before it
        if not parts:
            continue

        value, key = parts.rsplit(maxsplit=1)
        # Can't remember this edgecase
        if value.count('.') > 1:
            parts = value.split('.')  # type: ignore # (Reassigning variable)
            value = "".join(parts[0:-1]) + "." + parts[-1]

        result[key] = value.split(maxsplit=1)[0].replace(",", "")

    return result


def parse_files(files):
    data = []

    print("[+]Parsing files: ", end=None)
    for i, file in enumerate(files):
        filled_blocks = int((i + 1) / len(files) * 10)  # 10 blocks in the bar
        progress_bar = f"[{'■' * filled_blocks}{'□' * (10 - filled_blocks)}] {((i + 1) / len(files)) * 100:.1f}%"
        #sys.stdout.write(f"\r{progress_bar}")
        #sys.stdout.flush()

        parsed = parse_file(file)
        if not parsed:
            continue

        result = {}

        # Extract the base name of the file
        base_name = os.path.basename(file).replace('.out', '')

        # Split the base name by underscores to separate problem name and solver name
        # FIXME: Name cannot contain _
        name_parts = base_name.split('_')

        # Problem name is everything except the last part
        problem_name = '_'.join(name_parts[:-1])

        # Prepend the directory to the problem name
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


############ TAG PARSING ############

def parse_tagfile(file_path: str, directory: str, base_tags: Set[str]) -> Tuple[Dict[str, List[str]], Set[str]]:
    """
    Tag all files in a directory with the given tagfile
    :param file_path The path of the tagfile
    :param directory The directory to tag
    :base_tags The tags to apply on every file
    :returns A tuple containing, all files in a directory with their tags, a set of tags that apply at the given path
    """
    tags = None
    with open(file_path, "r") as f:
        tags = json.load(f)

    files_with_tags = {}
    all_tags = set(base_tags)

    add_tags = set(tags.get("add", []))
    all_tags.update(add_tags)

    files = [
        os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f != "tags.json"
    ]

    for file_path in files:
        files_with_tags[file_path] = all_tags

    for custom in tags.get("customize", []):
        for filepath, custom_tags in custom.items():
            full_path = os.path.join(directory, filepath)
            files_with_tags[full_path] = set(custom_tags)

    return {file: list(tags) for file, tags in files_with_tags.items()}, all_tags


def tag_directory(directory, tags=set()) -> Dict[str, List[str]]:
    """
    Recursively tag all files in the directory and all subdirs
    """

    dirs = []
    tags = tags.copy()
    found_tagfile = False
    taged_files: Dict[str, List[str]] = {}
    files = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)

        if os.path.isfile(full_path):
            if os.path.basename(full_path) == "tags.json":
                taged_files, tags = parse_tagfile(full_path, directory, tags)
                found_tagfile = True
            else:
                files.append(full_path)

        if os.path.isdir(full_path):
            dirs.append(full_path)

    if not found_tagfile:
        taged_files = {file: list(tags) for file in files}

    for dir in dirs:
        taged_files.update(tag_directory(dir, tags))

    return taged_files


def enrich_with_folders(df, cut=4):
    new_df = df.assign(folder=df['problem'].apply(lambda x: os.path.dirname(x)))  # Create a new df with additional folder column
    new_df.loc[:, 'folder'] = new_df['problem'].apply(
        lambda x: '/'.join(x.split(os.sep))[cut:][:-1]  # Cut the first n directorys and the file itself
    )

    new_df.loc[:, "problem"] = new_df["problem"].apply(
        lambda x: x.split(os.sep)[-1]  # Set the problem name to only the last part
    )

    return new_df


def tags_to_df(taged):
    return pd.DataFrame([(key, tag) for key, tags in taged.items() for tag in tags], columns=["problem", "tags"])


def clean_df(df, cut=2, remove_filetype=True, column="problem"):
    """
    Cleans the paths in the specified column of the DataFrame by:
    1. Removing the first 'cut' directories.
    2. Removing the file extension if `remove_filetype` is True.

    Parameters:
    - df: pandas.DataFrame
        The DataFrame to clean.
    - cut: int
        Number of directories to remove from the start of the path.
    - remove_filetype: bool
        Whether to remove the file extension.
    - column: str
        The name of the column containing the paths to clean.

    Returns:
    - pandas.DataFrame
        A new DataFrame with the cleaned paths.
    """
    def clean_path(path):
        # Split the path into components and remove the first 'cut' directories
        parts = path.split(os.sep)
        cleaned = os.sep.join(parts[cut:])
        # Remove the file extension if specified
        if remove_filetype:
            cleaned = os.path.splitext(cleaned)[0]
        return cleaned

    # Apply the cleaning function to the specified column
    df[column] = df[column].apply(clean_path)
    return df


def parse_data(args):
    files = [str(file) for file in Path(args.path).rglob("*.out")]
    df = parse_files(files)
    cleaned = clean_df(df, cut=args.cut, remove_filetype=args.remove_filetype)

    return cleaned


def parse_tags(args):
    taged = tag_directory(args.path)
    df = tags_to_df(taged)
    cleaned = clean_df(df, cut=args.cut, remove_filetype=args.remove_filetype)
    return cleaned


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse a directory generated by using the runner.py script, and store the resulting dataframe as csv")
    parser.add_argument("path", type=str, help="Path to the directory containing the results")
    parser.add_argument("output", type=str, help="The name to store the dataframe as")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["data", "tags"],
        default="data",
        help="Choose whether to parse data or tags (default: data)",
    )
    parser.add_argument("--cut", type=int, default=2, help="Number of directories to remove from the start of the paths (default: 2), only applicable if mode is set to tags")
    parser.add_argument("--remove-filetype", action="store_true", help="Remove the file extension from paths (default: False), only applicable if mode is set to tags")
    args = parser.parse_args()

    df = None
    if args.mode == "data":
        df = parse_data(args)
    else:
        df = parse_tags(args)

    df.to_csv(f"{args.output}.csv")
