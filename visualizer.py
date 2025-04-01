import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import LogNorm
import matplotlib

import argparse
import sys


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
    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()

    # Create an error indicator:
    # It's True if either:
    #   - status is "Error", OR
    #   - sanity_sat is not "sat" or "unsat"
    # But we exclude any rows where status is "Timeout"
    df['error_indicator'] = (((df['status'] == 'Error') | (~df['sanity_sat'].isin(['sat', 'unsat'])))
                             & (df['status'] != 'Timeout'))

    # Now aggregate by solver
    result = df.groupby('solver').agg(
        total_problems=('solver', 'count'),
        timeout_count=('status', lambda x: (x == 'Timeout').sum()),
        error_count=('error_indicator', 'sum'),
        solved_count=('sanity_sat', lambda x: x.isin(['sat', 'unsat']).sum()),
        sat_count=('sanity_sat', lambda x: (x == 'sat').sum()),
        unsat_count=('sanity_sat', lambda x: (x == 'unsat').sum()),
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
        cumulative = range(0, len(sorted_data) + 1)

        # Step plot
        ax.step(cumulative, [0] + sorted_data.tolist(), where='post', label=solver)

        # Plot points at each step
        # step_indices = range(0, len(sorted_data), 10)  # Every 10th problem
        # ax.scatter(sorted_data.iloc[step_indices], [cumulative[i] for i in step_indices],
        #            s=10, color='black', zorder=3)

    # ax.set_xscale('log')
    ax.set_yscale('log')

    # Labels and title
    ax.set_ylabel('Task Clock: msec')
    ax.set_xlabel('Problem Count')
    ax.set_title('Cactus Plot: Task Completion Times by Solver')
    ax.legend(title='Solvers')
    ax.grid(True)

    return fig


def sum_time_barchart(data_frame, figsize=(10, 6), ax=None):
    total_problems = data_frame["problem"].nunique()

    # Group the data by 'solver' and calculate the sum of 'task-clock:u'
    summed_data = data_frame.groupby('solver')['task-clock:u'].sum().sort_values(ascending=False)
    max_value = summed_data.max()
    threshold = max_value * 0.1  # 10% of the maximum value as the threshold

    # Calculate the number of problems solved per solver
    problems_solved = data_frame[data_frame["status"] == "Success"].groupby('solver').size()

    # Calculate the average time per problem for each solver
    avg_time_per_problem = summed_data / problems_solved

    # Create the bar chart on the provided axis
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = None

    bars = summed_data.plot(kind='bar', color='skyblue', ax=ax)
    ax.set_yscale("log")

    # Adding text to the bars
    for bar, value, solver in zip(bars.patches, summed_data, summed_data.index):
        # Determine the position and alignment based on the value relative to the threshold
        if value > threshold:
            # For larger values, place text slightly above the bar with 'bottom' alignment
            text_y = value * 1.1
            text_va = 'bottom'
        else:
            # For smaller values, place text higher with 'bottom' alignment to ensure visibility
            text_y = value * 3
            text_va = 'bottom'

        # Main value text
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            text_y,
            f"{value:.2f}",
            ha="center",
            va=text_va,
            fontsize=9,
            color="black",
        )

        # Solved problems text
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            text_y * 0.7,  # Position below the main value text
            f"Solved: {problems_solved[solver]}",
            ha="center",
            va='top',
            fontsize=8,
            color="black",
        )

        # Average time text
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            text_y * 0.5,  # Position below the solved text
            f"Avg: {avg_time_per_problem[solver]:.2f}",
            ha="center",
            va='top',
            fontsize=8,
            color="black",
        )

    # Add title and labels
    ax.set_title('Total Task Clock Time by Solver', fontsize=10)
    ax.set_xlabel('Solver', fontsize=9)
    ax.set_ylabel('Total Task Clock Time in msec', fontsize=9)
    ax.set_xticklabels(ax.get_xticklabels(), ha='right', rotation=45, fontsize=8)

    # Add global problem count label
    ax.text(
        0.5, 0.9,
        f"Total Problems: {total_problems}",
        ha="center",
        va="bottom",
        fontsize=8,
        color="gray",
        transform=ax.transAxes,
    )

    if fig:
        plt.tight_layout()

    return fig


def solved_barchart(data_frame, figsize=(10, 6), ax=None):
    # Filter rows where status is "Success"
    solved_df = data_frame[data_frame['status'] == 'Success']
    solved_df = solved_df[solved_df["sanity_sat"].isin(["sat", "unsat"])]  # Only accept sat or unsat

    # Group by 'solver' and 'sanity_sat' and count the number of successes
    sanity_counts = solved_df.groupby(['solver', 'sanity_sat']).size().unstack(fill_value=0)

    # Sort by total solved count (sum of 'sat' and 'unsat')
    sanity_counts = sanity_counts.loc[sanity_counts.sum(axis=1).sort_values(ascending=False).index]

    # Calculate the total number of problems
    total_problems = data_frame["problem"].nunique()

    # Create a figure and axis if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = None  # No standalone figure when using subplots

    color_map = {'sat': 'green', 'unsat': 'orange'}
    colors = [color_map.get(col, 'blue') for col in sanity_counts.columns]

    # Plot the stacked bar chart with the sorted order
    sanity_counts.plot(kind='bar', stacked=True, ax=ax, color=colors)

    # Add a horizontal line for the total number of problems
    ax.axhline(y=total_problems, color='red', linestyle='--', linewidth=1.5, label='Total Problems')

    # Customize the plot
    ax.set_xlabel('Solver')
    ax.set_ylabel('Number of Problems Solved')

    ax.text(
        0.5, 0.96,  # Position at the top center (relative coordinates)
        f"Total Problems: {total_problems}",
        ha="center",
        va="bottom",
        fontsize=8,
        color="gray",
        transform=ax.transAxes,
    )

    # Adjust layout if it's a standalone figure
    if fig:
        plt.tight_layout()

    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print and/or visualize stats gathered by the dataparser")
    parser.add_argument("path", type=str, help="Path to the csv containing the results")
    parser.add_argument("--heatmap", action="store_true", help="Enable heatmap visualization")
    parser.add_argument("--cactus", action="store_true", help="Enable cactus chart visualization")
    parser.add_argument("--scatter", action="store_true", help="Enable scatter chart visualization")
    parser.add_argument("--table", action="store_true", help="Enable a summary table visualization")
    parser.add_argument("--solved", action="store_true", help="Enable a barchart showing solved sat/unsat instances per solver")
    parser.add_argument("--mpl", type=str, default="qtagg", help="The matplotlib backend to use, default is qtagg")
    parser.add_argument("--save-graphs", action="store_true", help="If the generated plots are to be saved")
    parser.add_argument("--tags", type=str, help="Path to the parsed tags")
    parser.add_argument("--having", nargs='+', type=str, help="Filter results having either tag")
    parser.add_argument("--exact", nargs='+', type=str, help="Filter results having exact tags")
    args = parser.parse_args()

    matplotlib.use(args.mpl)

    df = pd.read_csv(args.path)

    if args.tags:
        import tag_util

    # Ensure we have tags when working with tags
    if (args.having or args.exact) and not args.tags:
        print("If you want to filter by tags please provide parsed tags via the --tags flag")
        sys.exit(1)

    if (args.having and args.exact):
        print("You cannot use --having and --exact at the same time")
        sys.exit(1)

    tags = None
    # Read tags
    if args.tags:
        tags = pd.read_csv(args.tags)

    # Filter df by tags
    if (args.having):
        print("[+] Filtering by tags")
        df = tag_util.find_having_tags(df, tags, set(args.having))
    elif (args.exact):
        print("[+] Filtering by tags")
        df = tag_util.find_exact_tagset(df, tags, set(args.exact))

    if df.empty:
        print("[+] The selected dataframe is empty!")
        sys.exit(-1)

    if args.table:
        print(summary_table(df))

    figures = []
    if args.heatmap:
        figures.append(full_heatmap(df))

    if args.cactus:
        figures.append(cactus_plot(df))

    if args.scatter:
        figures.append(scatter(df))

    if args.solved:
        figures.append(solved_barchart(df))

    if len(figures) > 0:
        print("[+] Showing graphs")
        plt.show()

        if args.save_graphs:
            for i, fig in enumerate(figures):
                fig.savefig(f"plot_{i}.png")
