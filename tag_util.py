import os
from typing import Dict, List, Set, Tuple
import json
import pandas as pd
import argparse


def find_having_tags(df, TAGS, tagset):
    """
    Filter the DataFrame `df` to include only those problems that have all the tags specified in `tagset`.

    Parameters:
    - df (DataFrame): The main DataFrame containing problem data. It is assumed that it has a column named 'problem'.
    - TAGS (DataFrame): A DataFrame that maps problems to their tags. It should contain at least two columns: 
                        'problem' (the identifier of the problem) and 'tags' (the associated tag).
    - tagset (set): A set of tags that each problem must include.

    Returns:
    - DataFrame: A subset of `df` containing only the problems that include all tags in `tagset`.
    """
    filtered_tags = TAGS[TAGS['tags'].isin(list(tagset))]

    # Group by 'problem' and find problems with both tags
    problems_with_both_tags = (
        filtered_tags.groupby("problem")["tags"]
        .apply(set)  # Get unique tags for each problem
        .apply(lambda t: tagset.issubset(t))  # Check if both tags are present
    )

    # Get problems that satisfy the condition
    matching_problems = problems_with_both_tags[problems_with_both_tags].index

    return df[df['problem'].isin(matching_problems)]


def find_exact_tagset(df, TAGS, tagset):
    """
    Filter the DataFrame `df` to include only those problems whose tags exactly match the given `tagset`.

    Parameters:
    - df (DataFrame): The main DataFrame containing problem data, expected to have a column named 'problem'.
    - TAGS (DataFrame): A DataFrame that associates problems with their tags. Must contain 'problem' and 'tags' columns.
    - tagset (set): The exact set of tags that a problem must have to be considered a match.

    Returns:
    - DataFrame: A subset of `df` containing only the problems whose set of tags exactly matches `tagset`.
    """
    # Group by 'problem' and collect unique tags for each problem
    problem_to_tags = (
        TAGS.groupby("problem")["tags"]
        .apply(set)  # Get unique tags as a set for each problem
    )

    # Find problems where the tags exactly match the given tagset
    matching_problems = problem_to_tags[problem_to_tags == tagset].index

    # Filter the original dataframe for these problems
    return df[df['problem'].isin(matching_problems)]


def get_unique_tagsets(TAGS):
    """
    Get a list of unique tag sets across all problems in the TAGS DataFrame.

    Parameters:
    - TAGS (DataFrame): A DataFrame that contains problem-tag mappings, with at least the columns 'problem' and 'tags'.

    Returns:
    - list: A list of unique tag sets (as Python sets), where each set represents the unique tags associated with a problem.
    """
    # Group by 'problem' and collect unique tags as sets
    problem_to_tags = (
        TAGS.groupby("problem")["tags"]
        .apply(set)  # Get unique tags as a set for each problem
    )

    # Extract unique tagsets
    unique_tagsets = problem_to_tags.drop_duplicates().tolist()

    return unique_tagsets


if __name__ == "__main__":
    pass
