import os
import subprocess


def run_experiment(top_path: str):
    subprocess.run(
        [
            "codex",
            "exec",
            f"""The goal is to understand the design {top_path} using simulation waveforms.
Use temp_artifacts_comparator/ as a working directory.

<iteration loop>
1. Maintain a list of coverpoints and the reasons for testing these (note that these may or may not be correct) in hypotheses.md. 
2. For each coverpoint we need to generate a separate waveform file in waves/wave_id.vcd
Use vcs to run the simulation and generate the waveforms.
Maintain the run commands in run.sh
Note that you may run this step multiple times to get better waveforms so maintain modular code.
3. Use vcdcat (already available as a bash command) to render the waveforms for each experiment and waves/wave_id.txt
4. In mental_model.md, maintain a list of features of the design + rendered waveforms.
Each function should highlight how the design is functions when used in various conditions, focus primarily on long term behaviour.
If multiple experiments correspond to the same function just update it to have the most comprehensive information.
</iteration loop>

Repeat the iteration loop 5 times until you have a good understanding of the design.

<rendered waveform format>
- A table with each row one timestep with gaps to skip time.
- The table should be in a readable, compact format to help understand the design behaviour.
- Assume clk is implicit and is 1 for all rows.
- Make sure you take snippets of the waveforms from the .txt files and copy paste them. 
You may only copy specific lines or columns and stitch them together. 
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
- All of the above artifacts (hypotheses.md, run.cmd, waves/wave_id.txt, mental_model.md) should be in temp_artifacts_comparator/ so that you may resume the process from any step in between.
- Generate hypotheses / coverpoints one by one and use the previous to generate a good idea to test next.
- Repeat the process until you have a good understanding of the design.
- Keep track of all the learnings you encounter in learnings.md so that you don't make the same mistakes when this loop is run again.
- If these artifacts already exist, check the mental_model.md and hypotheses.md to understand the current state and figure out how to proceed from there.
</behaviour>

<commands details>
- To run the simulation, 
Step 1: create testbench.sv files
Step 2: create a testbench_filelist.f file
Step 3: run the following command:
```
bash run_vcs.sh design_filelist.f testbench_filelist.f testbench_top_module
```
do not use simv or any other wrappers
Make sure the testbench.sv files have vcd dumps.
</commands details>
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
        "/home/vivek_cstack/chipstack-ai/kpi/chipstack_kpi/references/dev_set/comparator/comparator.sv with /home/vivek_cstack/chipstack-ai/kpi/chipstack_kpi/references/dev_set/comparator/filelist.f"
    )
