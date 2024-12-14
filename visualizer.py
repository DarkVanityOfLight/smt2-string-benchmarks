import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import LogNorm
import argparse

import matplotlib


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

    # Group by 'solver' and sum 'task-clock:u'
    task_clock_sum = df.groupby('solver')['task-clock:u'].sum()

    print(task_clock_sum.to_string(index=True))


def full_heatmap(data_frame):
    pivot_df = data_frame.pivot(index='problem', columns='solver', values='task-clock:u')

    bad_color = 'purple'
    cmap = sns.color_palette("crest", as_cmap=True)
    cmap.set_bad(bad_color)

    # Create the figure and the heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(
        pivot_df,
        annot=False,
        fmt=".2f",
        cbar_kws={'label': 'task-clock:u'},
        norm=LogNorm(),
        cmap=cmap,
        ax=ax
    )

    # Title and labels
    ax.set_title('Task Clock Time by Problem and Solver')
    ax.set_xlabel('Solver')
    ax.set_ylabel('Problem')

    ax.set_yticks([])  # Hide y ticks

    plt.tight_layout()

    return fig


def scatter(df):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot each solver's data
    for solver in df['solver'].unique():
        subset = df[df['solver'] == solver]
        ax.scatter(subset['problem'], subset['task-clock:u'], label=solver)

    ax.set_xlabel('Problem')
    ax.set_ylabel('Elapsed Time')
    ax.set_title('Elapsed Time per Problem by Solver')
    ax.legend()
    ax.set_xticks([])

    # Return the figure object
    return fig


def summary_table(df):
    result = df.groupby('solver').agg(
        success_count=('status', lambda x: (x == 'Success').sum()),
        timeout_count=('status', lambda x: (x == 'Timeout').sum()),
        error_count=('status', lambda x: (x == "Error").sum()),
        total_task_clock=('task-clock:u', 'sum')
    ).reset_index()
    return result


def cactus_plot(df):
    cleaned = df[df["status"] == "Success"]

    # Pivot the dataframe to have 'solver' as columns and 'problem' as rows
    pivot_df = cleaned.pivot(index='problem', columns='solver', values='task-clock:u')

    # Create the plot
    fig, ax = plt.subplots(figsize=(10, 6))

    for solver in pivot_df.columns:
        sorted_data = pivot_df[solver].dropna().sort_values()
        cumulative = range(1, len(sorted_data) + 1)

        # Step plot
        ax.step(cumulative, sorted_data, where='post', label=solver)

        # Plot points at each step
        # step_indices = range(0, len(sorted_data), 10)  # Every 10th problem
        # ax.scatter(sorted_data.iloc[step_indices], [cumulative[i] for i in step_indices],
        #            s=10, color='black', zorder=3)

    # ax.set_xscale('log')
    ax.set_yscale('log')

    # Labels and title
    ax.set_ylabel('Task Clock (u)')
    ax.set_xlabel('Problem Count')
    ax.set_title('Cactus Plot: Task Completion Times by Solver')
    ax.legend(title='Solvers')
    ax.grid(True)

    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print and/or visualize stats gathered by the dataparser")
    parser.add_argument("path", type=str, help="Path to the csv containing the results")
    parser.add_argument("--heatmap", action="store_true", help="Enable heatmap visualization")
    parser.add_argument("--cactus", action="store_true", help="Enable cactus chart visualization")
    parser.add_argument("--scatter", action="store_true", help="Enable scatter chart visualization")
    parser.add_argument("--table", action="store_true", help="Enable a summary table visualization")
    parser.add_argument("--mpl", type=str, default="qtagg", help="The matplotlib backend to use, default is qtagg")
    parser.add_argument("--save_graphs", action="store_true", help="If the generated plots are to be saved")
    args = parser.parse_args()

    df = pd.read_csv(args.path)
    matplotlib.use(args.mpl)

    if args.table:
        print(summary_table(df))

    figures = []
    if args.heatmap:
        figures.append(full_heatmap(df))

    if args.cactus:
        figures.append(cactus_plot(df))

    if args.scatter:
        figures.append(scatter(df))

    print("[+] Showing graphs")
    plt.show()

    if args.save_graphs:
        for i, fig in enumerate(figures):
            fig.savefig(f"plot_{i}.png")
