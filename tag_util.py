import os
from typing import Dict, List, Set, Tuple
import json
import pandas as pd
import argparse


def parse_tagfile(file_path: str, directory: str, base_tags: Set[str]) -> Tuple[Dict[str, [List[str]]], Set[str]]:
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

if __name__ == "__main__":


    parser = argparse.ArgumentParser(description="Generate a tag dataframe, containing problems and their tags")
    parser.add_argument("path", type=str, help="Path to the directory containing the benchmarks and tagfiles")
    parser.add_argument("output", type=str, help="The name to store the dataframe as")
    parser.add_argument("--cut", type=int, default=2, help="Number of directories to remove from the start of the paths (default: 2)")
    parser.add_argument("--remove-filetype", action="store_true", help="Remove the file extension from paths (default: False)")
    #parser.add_argument("--column", type=str, default="problem", help="Name of the column to clean (default: 'problem')")
    args = parser.parse_args()



    taged = tag_directory(args.path)
    df = tags_to_df(taged)
    cleaned = clean_df(df, cut=args.cut, remove_filetype=args.remove_filetype)
    cleaned.to_csv(f"{args.output}.csv")
