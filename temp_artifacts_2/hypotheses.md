Counter coverpoints and hypotheses (iterative)

Iteration 1
- CP1: Basic counting when enabled: After synchronous reset deasserts, with `en=1`, `count` should increment by 1 each enabled cycle. Reason: core functionality of an up-counter. Wave: `waves/basic_counting.vcd`.

Iteration 2
- CP2: Hold when disabled: With `en=0`, `count` must hold its value across cycles. Reason: ensure gating logic works. Wave: `waves/hold_when_disabled.vcd`.

Iteration 3
- CP3: Synchronous reset semantics: While `rst=1`, `count` should be driven to 0 at the next posedge and remain 0 while asserted. Reason: verify reset timing and polarity. Wave: `waves/reset_behavior.vcd`.

Iteration 4
- CP4: Reset has priority over enable: If both `rst=1` and `en=1`, reset dominates and output is 0. Reason: confirm `if (rst) ... else if (en) ...` priority. Wave: `waves/rst_over_en_priority.vcd`.

Iteration 5
- CP5: 8-bit wraparound at 255→0: With continuous `en=1`, `count` should roll over from `0xFF` to `0x00`. Reason: 8-bit arithmetic overflow behavior. Wave: `waves/wraparound.vcd`.
- CP6: Mid-stream single-cycle reset: During counting, a one-cycle `rst` pulse should clear `count` on that posedge, then counting resumes. Reason: robustness to in-flight resets. Wave: `waves/mid_stream_reset.vcd`.

Notes
- Namespacing: vcdcat requires `TOP.count[7:0]` for the bus; using `TOP.count` omits the column.
- All tests assume a deterministic reset is applied at or near time 0 to avoid uninitialized state under Verilator.

