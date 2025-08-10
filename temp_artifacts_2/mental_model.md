Counter mental model and evidence

Feature: Synchronous reset to zero
- Behavior: When `rst=1`, `count` is 0 at posedge and remains 0 while `rst` is held.
- Evidence (from `waves/reset_behavior.txt`):
  0 1 2 3  4 
  ==========
  650 1 1 0  0
  651 0 1 0  0
  652 1 0 0  0
  ...
  660 1 1 0  0
  662 1 1 0  0

Feature: Reset priority over enable
- Behavior: If `rst=1` and `en=1`, reset dominates; `count=0`.
- Evidence (from `waves/rst_over_en_priority.txt`):
  0 1 2 3  4 
  ==========
  630 1 0 1  4
  632 1 1 1  0
  634 1 0 1  1

Feature: Enable-gated increment (+1 per enabled cycle)
- Behavior: With `en=1` and `rst=0`, `count` increments by one each posedge.
- Evidence (from `waves/basic_counting.txt`):
  0 1 2 3  4 
  ==========
  20 1 0 1  9
  22 1 0 1  a
  24 1 0 1  b
  26 1 0 1  c
  34 1 0 1 10

Feature: Hold when disabled
- Behavior: With `en=0` and `rst=0`, `count` holds its value across cycles.
- Evidence (from `waves/hold_when_disabled.txt`):
  0 1 2 3  4 
  ==========
  78 1 0 1  8
  80 1 0 0  8
  82 1 0 0  8
  84 1 0 0  8

Feature: Mid-stream reset pulse
- Behavior: A one-cycle `rst` pulse clears `count` on that posedge and counting resumes next cycles if `en=1`.
- Evidence (from `waves/mid_stream_reset.txt`):
  0 1 2 3  4 
  ==========
  664 1 0 1  6
  666 1 1 1  0
  668 1 0 1  1
  670 1 0 1  2

Feature: 8-bit width and wraparound
- Behavior: After 255 (0xFF), the next increment wraps to 0.
- Evidence: Current run shows steady increments (`waves/wraparound.txt`) but does not reach 0xFF→0 due to limited cycles. Extend enabled cycles to ≥256 to capture rollover.

Summary
- Design is an 8-bit synchronous up-counter with active-high synchronous reset and enable gating. Verified behaviors cover reset semantics and priority, gated counting, holding when disabled, and mid-stream reset handling. Wraparound is implied by 8-bit width and to be captured with longer runs.

