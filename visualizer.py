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
    timeout_counts = df[df['status'] == 'Timeout'].groupby('solver').size()
    if timeout_counts.empty:
        print("Timeouts: 0")
    else:
        print("Timeouts:")
        print(timeout_counts.to_string(index=True))


def count_errors(df):
    error_counts = df[df['status'] == 'Error'].groupby('solver').size()
    if error_counts.empty:
        print("Errors: 0")
    else:
        print("Errors:")
        print(error_counts.to_string(index=True))


def total_time(df):
    # Convert 'task-clock:u' to float
    print("Total time used(in ms user time):")
    df['task-clock:u'] = df['task-clock:u'].astype(float)

    # Group by 'solver' and sum 'task-clock:u'
    task_clock_sum = df.groupby('solver')['task-clock:u'].sum()

    print(task_clock_sum.to_string(index=True))


def full_heatmap(data_frame):
    pivot_df = data_frame.pivot(index='problem', columns='solver', values='task-clock:u')

    bad_color = 'purple'
    cmap = sns.color_palette("crest", as_cmap=True)
    cmap.set_bad(bad_color)

    plt.figure(figsize=(12, 8))
    sns.heatmap(
        pivot_df,
        annot=False,
        fmt=".2f",
        cbar_kws={'label': 'task-clock:u'},
        norm=LogNorm(),
        cmap=cmap
    )

    # Title and labels
    plt.title('Task Clock Time by Problem and Solver')
    plt.xlabel('Solver')
    plt.ylabel('Problem')

    plt.yticks([])
    plt.xticks()

    plt.tight_layout()


def scatter(df):
    plt.figure(figsize=(10, 6))
    for solver in df['solver'].unique():
        subset = df[df['solver'] == solver]
        plt.scatter(subset['problem'], subset['task-clock:u'], label=solver)

    plt.xlabel('Problem')
    plt.ylabel('Elapsed Time')
    plt.title('Elapsed Time per Problem by Solver')
    plt.legend()
    plt.xticks([])  # Rotate x-axis labels if they overlap
    plt.show()


if __name__ == "__main__":
    df = pd.read_csv("QF_S_PARSED.csv")
    # visualize_runtime(df)
    count_timeouts(df)
    print("")
    count_errors(df)
    print("")
    total_time(df)
