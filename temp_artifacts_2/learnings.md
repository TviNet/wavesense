Learnings and pitfalls

- vcdcat exact names: Use `TOP.count[7:0]` for the bus; `TOP.count` yields no data column.
- Wave rendering signals: `vcdcat -l <vcd>` helps discover exact signal paths when unsure.
- Verilator build on this machine: Linking a fresh sim under `temp_artifacts_2/` failed due to toolchain/sandbox quirks. Reused existing prebuilt sim (`temp_artifacts/bin/counter_cov_sim`) to generate a new VCD in the working directory.
- Modular runs: Keep a parameterized testbench to generate one waveform per coverpoint; record commands in `run.cmd` for reproducibility.
- Wraparound capture: Ensure at least 256 enabled increments after reset to observe 0xFE→0xFF→0x00 sequence.

