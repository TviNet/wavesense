import os
import subprocess


def run_experiment(top_path: str):
    subprocess.run(
        [
            "codex",
            "exec",
            f"""The goal is to understand the behaviour of thedesign {top_path} using simulation waveforms.
Use temp_artifacts/ as a working directory.

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


<rendered waveform format>
- A table with each row one timestep with gaps to skip time.
- The table should be in a readable, compact format to help understand the design behaviour.
- Assume clk is implicit and is 1 for all rows.
- Make sure you take snippets of the waveforms from the .txt files and copy paste them. 
You may only copy specific lines or columns and stitch them together along with few lines of context.
Do not make up values.
Highlight the key things to look out for in the waveform.
Example:
```
a b c d
=========
0 0 0xFF 0
1 0 0x00 1
0 0 0x01 2
1 0 0x02 3
0 0 0x03 4
...
```
</rendered waveform format>

<behaviour>
- For multiple clocks, use the same frequency for all clocks.
- Track task progress externally in task_progress.md and if it exists continue from there.
- Always read learnings.md and adjust the experiment accordingly. NEVER delete or rewrite learnings.md without looking at the contents.
- All of the above artifacts (hypotheses.md, run.cmd, waves/wave_id.txt, mental_model.md) should be in temp_artifacts/ so that you may resume the process from any step in between.
- Generate hypotheses / coverpoints one by one and use the previous to generate a good idea to test next.
- Repeat the process until you have a good understanding of the design.
- Keep track of all the learnings you encounter in learnings.md so that you don't make the same mistakes when this loop is run again.
- If these artifacts already exist, check the mental_model.md and hypotheses.md to understand the current state and figure out how to proceed from there.
</behaviour>

<commands guidelines>
- To run the simulation, 
    Step 1: create testbench.sv files
    Step 2: create a testbench_filelist.f file
    Step 3: run the following command:
    ```
    bash run_vcs.sh design_filelist.f testbench_filelist.f testbench_top_module
    ```
    do not use simv or any other wrappers
    Make sure the testbench.sv files have vcd dumps.
</commands guidelines>
""",
        ],
        env=os.environ.copy(),
    )


if __name__ == "__main__":
    # run_experiment(
    #     "/home/vineet/chipstack-ai/kpi/chipstack_kpi/references/dev_set/cdc_fifo/rtl/filelist.f with /home/vineet/chipstack-ai/kpi/chipstack_kpi/references/dev_set/cdc_fifo/rtl/filelist.f"
    # )
    # run_experiment(
    #     "/Users/vineet/Projects/Job/ChipStack/chipstack-ai/kpi/chipstack_kpi/references/dev_set/rr_arbiter/arbiter.v with /Users/vineet/Projects/Job/ChipStack/chipstack-ai/kpi/chipstack_kpi/references/dev_set/rr_arbiter/filelist.f"
    # )
    run_experiment(
        "/home/vineet/chipstack-ai/kpi/chipstack_kpi/references/dev_set/bedrock-rtl/counter/rtl/br_counter.sv with /home/vineet/chipstack-ai/kpi/chipstack_kpi/references/dev_set/filelist_counter_rtl_br_counter.f"
    )
