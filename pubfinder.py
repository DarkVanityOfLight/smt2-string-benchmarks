import os
import re
import sys


def extract_publications_line(file_path):
    pattern = re.compile(r"^\s*publications\s*:\s*(.*)$", re.IGNORECASE)

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            match = pattern.match(line)
            if match:
                return f"{match.group(1).strip()}"
    return None


def process_directory(directory):
    results = {}
    unique_lines = set()  # To store unique publication lines

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            try:
                line = extract_publications_line(file_path)
                if line and line not in unique_lines:
                    unique_lines.add(line)
                    results[file_path] = line
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    return results


if __name__ == "__main__":
    directory = sys.argv[1]
    publication_lines = process_directory(directory)

    for path, line in publication_lines.items():
        print(f"  {line}")
