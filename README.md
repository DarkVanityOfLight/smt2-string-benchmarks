# SMT2 String lib benchmarks

This repository contains several helper scripts, to benchmark and
analyze several SMT solvers over the theory of strings.

## Solvers
Current supported solvers contain:
  - [z3](https://github.com/Z3Prover/z3)
  - [z3-noodler](https://github.com/VeriFIT/z3-noodler)
  - [z3-alpha](https://github.com/JohnLyu2/z3alpha)(with a modified startup scripts)
  - [cvc5](https://github.com/cvc5/cvc5)
  - [ostrich](https://github.com/uuverifiers/ostrich)

## The runner
This script is used to run several solvers in parallel and measure their runtime using `perf`.
The timeout given to each solver by default is 60 seconds, after 70 seconds they are hard killed by the script.
The runner will produce an output directory `out` containing the performance stats and other infos.
Before running you should adjust your paths to the solvers in the script.
For options check `python3 runner.py --help`.

> Note:
> When using the --solver argument make sure to put a -- as delimiter between it and the next argumnet.
> Eg. `python3 runner.py --solvers ostrich -- benchmarks/non-incremental/QF_SLIA`

## The dataparser
The dataparser takes the raw output from the runner and extracts it to an 
easy to use pandas dataframe that is saved as csv.
There could(?) arise some issues on windows machines.
For options check `python3 dataparser.py --help`

## The visualizer
The visualizer takes in a parsed dataset(in csv form), and can generate 
several informations about the dataset. 
Supported are:
  - A summary table, displaying the number of timeouts, solved problems, errors and total time used in userpace per solver
  - A heatmap plot
  - A scatter plot
  - A cactus plot

For checking how to use run:
`python3 dataparser.py --help`

## Requirments
Each script is written using python 3.12, other versions might still work.

### Runner
The runner requires only `perf` for measuring the runtime of each solver.
The rest should be standard python librarys, make sure you have installed each solver
and adjusted the path for each solver in the script.

### Dataparser
The dataparser requires pandas.

### Visualizer
The visualizer requires pandas and matplotlib and seaborn.
Additionally make sure you have a compatible backend for matplotlib installed.

### Benchmarking
The generall procces of benchmarking would look something like this:
- Adjust the values in the runner script to your liking
- Run the script, eg. `python3 runner.py benchmarks/non-incremental/QF_S`
- Run the dataparser, eg. `python3 dataparser.py out/benchmarks/non-incremental/QF_S QF_S.csv`
- Run the visualizer, eg. `python3 visualizer.py --cactus --table --heatmap QF_S.csv`
