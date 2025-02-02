# SMT2 String lib benchmarks

This repository contains several helper scripts, to benchmark and
analyze several SMT solvers over the theory of strings.

## Solvers
Current benchmarked solvers are:
  - [z3](https://github.com/Z3Prover/z3)
  - [z3-noodler](https://github.com/VeriFIT/z3-noodler)
  - [z3-alpha](https://github.com/JohnLyu2/z3alpha)(with a modified startup scripts)
  - [cvc5](https://github.com/cvc5/cvc5)
  - [ostrich](https://github.com/uuverifiers/ostrich)
  - [ostrich with modular proof rules](https://github.com/uuverifiers/ostrich/tree/modular_proof_rules)

## The runner
This script is used to run several solvers in parallel and measure their runtime using `perf`.
The timeout given to each solver by default is 60 seconds, after 70 seconds they are hard killed by the script.
The runner will produce an output directory `out` containing the performance stats and other infos.
For options check `python3 runner.py --help`.

## The dataparser
The dataparser takes the raw output from the runner and extracts it to an 
easy to use pandas dataframe that is saved as csv.
There could(?) arise some issues on windows machines.
For options check `python3 dataparser.py --help`.

Tags can be generated using the dataparser in tag mode and the originial smt2 dataset.
Assume the originial problem set is in `benchmarks`
- Add `tags.json` files to indicate tags on files/folders

> Note: Check `tags.json` for an example tag file

## The visualizer
The visualizer takes in a parsed dataset(in csv form), and can generate 
several informations about the dataset. 
Supported are:
  - A summary table, displaying the number of timeouts, solved problems, errors and total time used in userpace per solver
  - A heatmap plot
  - A scatter plot
  - A cactus plot
  - Barcharts for runtime
  - Barcharts for solved problems(divided into sat/unsat)

For checking how to use run:
`python3 dataparser.py --help`

## Requirments
Each script is written using python >= python3.12. Since there were recent changes for `subprocess.run` 
older versions fail for the runner, but work for the other parts.

### Runner
The runner requires `perf` for measuring the runtime of each solver.
The rest should be standard python >= python3.12 librarys, make sure you have installed each solver
and adjusted the path for each solver in config file.

### Dataparser
The dataparser requires pandas.

### Visualizer
The visualizer requires pandas and matplotlib and seaborn.
Additionally make sure you have a compatible backend for matplotlib installed.

#### tag_util
The only non-system dependency is pandas.


## Benchmarking
> Note:
> When using any list argument make sure to put a -- as delimiter between it and an unflaged argumnet.
> Eg. `python3 runner.py --solvers ostrich -- benchmarks/non-incremental/QF_SLIA`
> `python3 runner.py --solvers ostrich --skip 10 benchmarks/` still works

The generall procces of benchmarking would look something like this:
- Install requirements, eg. `perf`
- Install all wanted solvers
- Configure all solvers using a config.json beside the runner.py file
- Start the benchmarking using the runner eg. `python3 runner.py benchmarks/`
- Run the dataparser, eg. `python3 dataparser.py out/benchmarks/`
- Add `tags.json` files in the originial problem set
- Run the dataparser again in tag mode `python3 dataparser.py --mode tags --cut 1 --remove-filetype benchmarks/ TAGS`
- Run the visualizer, eg. `python3 visualizer.py --having lia --tags TAGS.csv --table --clean 3 ALL_PARSED.csv` 


> Note: 
> The config file follows a simple format of solver_name: ["solver", "arguments"]
> Solver names should not contain _ since, they are used later in the dataparser as special character
> For example:
```json
{
    "cvc5": ["/home/lichtner/cvc5", "--tlimit", "60000"],
    "ostrich": ["/home/lichtner/ostrich/ostrich", "-logo", "-runtime", "+quiet", "-timeout=60000"],
    "z3alpha": ["/software/python/3.12.0/bin/python3.12", "/home/lichtner/z3alpha/smtcomp24/z3alpha.py", "-T:60"],
    "z3noodler": ["/home/lichtner/z3-noodler", "-T:60"],
    "z3": ["/home/lichtner/.local/bin/z3", "-T:60"]
}
```
