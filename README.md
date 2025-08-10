# Wavesense

## What it does?

**GPT-5 powered RTL design understanding through hypothesis and experimentation**

WaveSense is an automated tool that uses GPT-5 to understand digital hardware designs by intelligently generating hypothesis, running simulations, and analyzing waveforms to build comprehensive mental models. This tool iteratively runs the experiments until a much better understanding of how chips actually behave is achieved. 

## How does it achieve this?

Given an RTL design,

1. Hypothesis: Come up with interesting coverpoints / stimuli
2. Experiment: Generate code and run simulation to capture waveforms for these
3. Analysis: Create a mental model of how the design behaves based on the generated artifacts
4. Repeat from step 1.

## Implementation details

- Codex CLI as orchestrator agent with the following tools:
  - Regular bash commands
  - Verilator/VCS as simulator
- Compiled design as the environment
- Waveforms as the observations

## Usage

- `OPENAI_API_KEY=<your-key> python src/wavesense.py path/to/design.sv path/to/filelist.f my_artifacts_folder`

Some example designs and filelists are in the `example_rtl` folder.

## Requirements

- Codex CLI

```
npm install -g @openai/codex
```

~/.codex/config.toml

```
model = "gpt-5"

# full-auto mode
approval_policy = "on-request"
sandbox_mode    = "workspace-write"
```

- vcdvcd, vcdcat

```
pip install vcdvcd
```

- EDA simulators
  Preferably VCS as it is industry grade, verilator may also work based on the design.
