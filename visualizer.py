import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib.colors import LogNorm, Normalize

import matplotlib
matplotlib.use('qtagg')

# pd.set_option("display.max_rows", None)


def visualize_runtime(df):

    # Pivot the data for easier plotting
    print("[+]Pivoting data")
    pivot_df = df.pivot(index='problem', columns='solver', values='task-clock:u')

    print("[+]Filling NaN")
    pivot_df = pivot_df.fillna(0)
    print("[+]Converting to float")
    pivot_df = pivot_df.astype({col: float for col in pivot_df.columns})

    # pivot_df = pivot_df.head(1000)
    # Plotting
    print("[+]Plot")
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        pivot_df,
        cmap="YlGnBu",
        annot=False,
        fmt=".2f",
        cbar_kws={'label': 'Task Clock Time (msecs)'},
        norm=LogNorm()
    )

    # Title and labels
    plt.title('Task Clock Time by Problem and Solver')
    plt.xlabel('Solver')
    plt.ylabel('Problem')

    plt.yticks([])

    # Adjust layout to fit the plot
    plt.tight_layout()

    # Save the plot
    print("[+] Saving")
    plt.savefig('heatmap_plot.png', bbox_inches='tight')


def count_timeouts(df):
    print("Timeouts:\n")
    timeout_counts = df[df['status'] == 'Timeout'].groupby('solver').size()
    print(timeout_counts)


def count_errors(df):
    print("Errors:\n")
    timeout_counts = df[df['status'] == 'Error'].groupby('solver').size()
    print(timeout_counts)


def total_time(df):
    # Convert 'task-clock:u' to float
    print("Total time used")
    df['task-clock:u'] = df['task-clock:u'].astype(float)

    # Group by 'solver' and sum 'task-clock:u'
    task_clock_sum = df.groupby('solver')['task-clock:u'].sum()

    print(task_clock_sum)


if __name__ == "__main__":
    import dataparser

    df = dataparser.main()
    visualize_runtime(df)
    count_timeouts(df)
    count_errors(df)
    total_time(df)
