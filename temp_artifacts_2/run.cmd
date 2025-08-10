#!/usr/bin/env bash
set -euo pipefail

# Build (attempt; may fail in this sandbox)
verilator -cc rtl/counter.v --exe temp_artifacts_2/sim_main.cpp --trace -Mdir temp_artifacts_2/obj_dir || true
make -C temp_artifacts_2/obj_dir -f Vcounter.mk Vcounter || true

# Generate a fresh waveform using existing binary
(cd temp_artifacts_2 && ../temp_artifacts/bin/counter_cov_sim && mv -f waves.vcd waves/generated_default.vcd)

# Render waves for each experiment
vcdcat -x temp_artifacts_2/waves/basic_counting.vcd TOP.clk TOP.rst TOP.en 'TOP.count[7:0]' > temp_artifacts_2/waves/basic_counting.txt
vcdcat -x temp_artifacts_2/waves/hold_when_disabled.vcd TOP.clk TOP.rst TOP.en 'TOP.count[7:0]' > temp_artifacts_2/waves/hold_when_disabled.txt
vcdcat -x temp_artifacts_2/waves/reset_behavior.vcd TOP.clk TOP.rst TOP.en 'TOP.count[7:0]' > temp_artifacts_2/waves/reset_behavior.txt
vcdcat -x temp_artifacts_2/waves/rst_over_en_priority.vcd TOP.clk TOP.rst TOP.en 'TOP.count[7:0]' > temp_artifacts_2/waves/rst_over_en_priority.txt
vcdcat -x temp_artifacts_2/waves/wraparound.vcd TOP.clk TOP.rst TOP.en 'TOP.count[7:0]' > temp_artifacts_2/waves/wraparound.txt
vcdcat -x temp_artifacts_2/waves/mid_stream_reset.vcd TOP.clk TOP.rst TOP.en 'TOP.count[7:0]' > temp_artifacts_2/waves/mid_stream_reset.txt
vcdcat -x temp_artifacts_2/waves/generated_default.vcd TOP.clk TOP.rst TOP.en 'TOP.count[7:0]' > temp_artifacts_2/waves/generated_default.txt
