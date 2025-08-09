# Wavesense

## What it does?

Understanding of design via waveforms

## How it does it?

1. Given RTL design ->
2. generate coverpoints ->
3. run sim ->
4. generate waveforms ->
5. use waveforms to generate better mental model ->
6. repeat 2.

## Implementation details

- Codex CLI as orchestrator
- Verilator as simulator
- VCD as waveform format
- Waveform viewer / rendered (todo)
