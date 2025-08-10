#!/usr/bin/env python3

import os
import subprocess
import argparse
import sys


def run_experiment(top_design_file: str, filelist: str, output_dir: str):
    # Open log file for both stdout and stderr
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/log.txt", "w") as log_file:
        subprocess.run(
            [
                "codex",
                "exec",
                f"""The goal is to understand the behaviour of the design {top_design_file} with filelist {filelist} using simulation waveforms.
Use {output_dir} as a working directory.

<iteration loop>
1. Hypothesis generation: Update hypotheses.md with the new experiments to understand the design starting from typical use cases of the design.
(Note that these may or may not be correct, they should just provide interesting insights into the design)
Output artifacts: hypotheses.md

2. Experimentation: For each hypothesis we need to generate a separate waveform file in waves/wave_id.vcd.
Also convert the waveforms to a readable format in waves/wave_id.txt.
Output artifacts: testbenches/testbench_id.sv, testbenches/testbench_filelist.f, run_experiments.sh, waves/wave_id.vcd, waves/wave_id.txt

3. Analysis: In mental_model.md, maintain a list of features of the design + rendered waveforms.
Each function should highlight how the design is functions when used in various conditions, focus primarily on long term behaviour.
If multiple experiments correspond to the same function just update it to have the most comprehensive information.
Output artifacts: mental_model.md
</iteration loop>

<artifacts structure>
- <design_name>_artifacts/
    - hypotheses.md
    - testbenches/
    - waves/
    - mental_model.md
    - run_experiments.sh
</artifacts structure>

<hypothesis format>
- Use a yaml format to list the hypotheses.
- Hypothesis 1:
    - Description: string
    - Motivation: string
    - Prediction: string
- Hypothesis 2:
    - Description: string
    - Motivation: string
    - Prediction: string
- ...
</hypothesis format>

<mental model format>
- Use a markdown format to enumerate the mental model.
- Format:
## Summary
- Summary of the design behaviour.

## Observation 1
- Key points with notes on hypothesis prediction correctness: string
- Rendered waveform:
```

```


## Observation 2
- Key points with notes on hypothesis prediction correctness: string
- Rendered waveform:
```

```
...
</mental model format>


<rendered waveform format>
- A table with each row one timestep with gaps to skip time.
- The table should be in a readable, compact format to help understand the design behaviour.
- Assume clk is implicit and is 1 for all rows.
- Make sure you take snippets of the waveforms from the .txt files and copy paste them to avoid hallucinations.
- You may only copy specific lines or columns and stitch them together along with few lines of context.
- Do not make up values.
- Highlight the key things as notes to look out for in the waveform.
- Provide a few extra lines of context to help understand the waveform.
Example:
```
a b c d
=========
0 0 0xFF 0 <-- initial value
1 0 0x00 1 <-- increases
0 0 0x01 2 <-- increases
1 0 0x02 3 <-- increases
0 1 0x03 2 <-- decreases
...
```
</rendered waveform format>

<domain knowledge>
- For multiple clocks, use the same frequency for all clocks.
</domain knowledge>

<simulation commands guidelines>
- To run the simulation, 
    Step 1: create testbench.sv files
    Step 2: create a testbench_filelist.f file
    Step 3: run the following command:
    ```
    bash run_vcs.sh design_filelist.f testbench_filelist.f testbench_top_module
    ```
    do not use simv or any other wrappers
    Make sure the testbench.sv files have vcd dumps.
</simulation commands guidelines>
""",
            ],
            env=os.environ.copy(),
            stdout=log_file,
            stderr=log_file,
        )


def main():
    parser = argparse.ArgumentParser(
        description="WaveSense: AI-powered RTL design analysis using simulation waveforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s design.v filelist.f output_dir
  %(prog)s path/to/design.sv path/to/filelist.f my_artifacts
  %(prog)s --help
        """,
    )

    parser.add_argument(
        "top_design_file",
        help="Path to the top-level design file (e.g., design.v, design.sv)",
    )

    parser.add_argument(
        "filelist",
        help="Path to the filelist containing all design files",
    )

    parser.add_argument("output_dir", help="Output directory for artifacts and logs")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    if args.verbose:
        print(f"Starting WaveSense analysis...")
        print(f"Top design file: {args.top_design_file}")
        print(f"Filelist: {args.filelist}")
        print(f"Output directory: {args.output_dir}")

    try:
        run_experiment(args.top_design_file, args.filelist, args.output_dir)
        if args.verbose:
            print(
                f"Analysis completed successfully. Check {args.output_dir}/log.txt for details."
            )
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
