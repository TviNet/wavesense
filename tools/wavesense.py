import os
import subprocess


def run_experiment(top_path: str):
    subprocess.run(
        [
            "codex",
            "exec",
            f"""The goal is to understand the design {top_path} using simulation waveforms.
Use temp_artifacts/ as a working directory.
Follow the following steps:
1. maintain a list of coverpoints and the reasons for testing these (note that these may or may not be correct) in hypotheses.md
2. For each coverpoint we need to generate a separate waveform file in waves/wave_id.vcd
Use verilator to run the simulation and generate the waveforms.
Maintain the run cmd in run.cmd
Note that you may run this step multiple times to get better waveforms so maintain modular code.
3. Use vcdcat (already available as a bash command) to render the waveforms for each experiment and waves/wave_id.txt
4. In mental_model.md, maintain a list of features of the design and corresponding  waveforms rendered to help understand the design behaviour.
All of the above artifacts (hypotheses.md, run.cmd, waves/wave_id.txt, mental_model.md) should be in temp_artifacts/ so that you may resume the process from any step in between.

Repeat the process until you have a good understanding of the design.
Keep track of all the learnings you encounter in learnings.md so that you don't make the same mistakes when this loop is run again.
If these artifacts already exist, check the mental_model.md and hypotheses.md to understand the current state and figure out how to proceed from there.
""",
        ],
        env=os.environ.copy(),
    )


if __name__ == "__main__":
    run_experiment("rtl/counter.sv")
