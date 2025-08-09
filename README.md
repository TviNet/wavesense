# Wavesense

## What it does?

Understanding of design via waveforms

## How it does it?

1. Given RTL design
2. generate coverpoints
3. run sim with design and coverpoints
4. generate waveforms of these covers
5. log the experiment coverpoints and use waveforms to generate better mental model
6. repeat 2.

## Implementation details

- Codex CLI as orchestrator
- Verilator as simulator
- VCD as waveform format using vcdvcd, vcdcat to render waveforms for the llm
- Waveform viewer / rendered (todo)

## Usage

- Requirements: `verilator`, `make`, C++17 toolchain in PATH.
- Orchestrator CLI: `tools/wavesense.py`

Examples:

- Build and run simulation, produce `wave.vcd`:
  - `python3 tools/wavesense.py run --top counter`
- Generate heuristic coverpoints from RTL:
  - `python3 tools/wavesense.py coverpoints --rtl rtl --out coverpoints.yaml`
- Analyze VCD and print a concise waveform summary:
  - `python3 tools/wavesense.py analyze --vcd wave.vcd --out wave_summary.txt`
- End-to-end (run sim → coverpoints → analyze):
  - `python3 tools/wavesense.py all --top counter --vcd wave.vcd --coverpoints coverpoints.yaml --analysis wave_summary.txt`

Notes:

- Coverpoints are heuristic (regex-based) from the top RTL file and include toggles, min/max for buses, and rollover hints for counters.
- VCD analysis uses a lightweight built-in parser; no Python deps required.
