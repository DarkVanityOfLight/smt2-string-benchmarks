import os
from typing import Dict, List, Set, Tuple
import json
import pandas as pd
import argparse

def find_having_tags(df, TAGS, tagset):
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
