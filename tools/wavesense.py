import os
import subprocess


def run_experiment(top_path: str):
    subprocess.run(
        [
            "codex",
            "exec",
            f"""The goal is to understand the design {top_path} using simulation waveforms.
Use temp_artifacts/ as a working directory.

<iteration loop>
1. Maintain a list of coverpoints and the reasons for testing these (note that these may or may not be correct) in hypotheses.md. 
2. For each coverpoint we need to generate a separate waveform file in waves/wave_id.vcd
Use verilator to run the simulation and generate the waveforms.
Maintain the run cmd in run.cmd
Note that you may run this step multiple times to get better waveforms so maintain modular code.
3. Use vcdcat (already available as a bash command) to render the waveforms for each experiment and waves/wave_id.txt
4. In mental_model.md, maintain a list of features of the design + rendered waveforms.
Each feature should highlight key behaviours in various conditions.
If multiple experiments correspond to the same feature just update it to have the most comprehensive information.
</iteration loop>

Repeat the iteration loop 5 times until you have a good understanding of the design.

<rendered waveform format>
- A table with each row one timestep with gaps to skip time.
- The table should be in a readable, compact format to help understand the design behaviour.
- Assume clk is implicit and is 1 for all rows.
- Make sure you take snippets of the waveforms from the .txt files and copy paste them. You may only copy specific lines and stitch them together. Do not make up values.
Example:
```
a | b | c | d |
- | - | - | - |
...
0 | 0 | 0xFF | 0 |
1 | 0 | 0x00 | 1 |
0 | 0 | 0x01 | 2 |
1 | 0 | 0x02 | 3 |
0 | 0 | 0x03 | 4 |
...
```
</rendered waveform format>

<behaviour>
- All of the above artifacts (hypotheses.md, run.cmd, waves/wave_id.txt, mental_model.md) should be in temp_artifacts/ so that you may resume the process from any step in between.
- Generate hypotheses / coverpoints one by one and use the previous to generate a good idea to test next.
- Repeat the process until you have a good understanding of the design.
- Keep track of all the learnings you encounter in learnings.md so that you don't make the same mistakes when this loop is run again.
- If these artifacts already exist, check the mental_model.md and hypotheses.md to understand the current state and figure out how to proceed from there.
</behaviour>
""",
        ],
        env=os.environ.copy(),
    )


if __name__ == "__main__":
    run_experiment("rtl/counter.sv")
