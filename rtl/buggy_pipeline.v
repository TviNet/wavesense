// Buggy two-stage pipeline illustrating a scheduling/race bug.
// Intent (what a naive mental model/spec might infer by reading code):
//   - Two flip-flop stages imply one-cycle latency from input to output.
// Actual (simulation waveform):
//   - Uses blocking assignments in posedge blocks across two always blocks.
//   - Output latency becomes simulator-order dependent (0 or 1 cycle),
//     which only shows up when you inspect waveforms over time.

module buggy_pipeline #(
    parameter WIDTH = 8
) (
    input  wire              clk,
    input  wire              rst,     // synchronous reset
    input  wire              in_valid,
    input  wire [WIDTH-1:0]  in_data,
    output reg               out_valid,
    output reg  [WIDTH-1:0]  out_data
);

    // Stage 1 regs
    reg              s1_valid;
    reg [WIDTH-1:0]  s1_data;

    // BUG: blocking assignments inside edge-triggered processes.
    // Many readers form a mental model that posedge blocks are "flops" and
    // thus behave with 1-cycle latency through a two-stage pipeline.
    // However, using '=' (blocking) across distinct always blocks creates a
    // scheduling race: one block may see updates from the other in the same
    // time step, collapsing the pipeline by a cycle.

    // Stage 1 capture
    always @(posedge clk) begin
        if (rst) begin
            s1_valid = 1'b0;     // BUG: blocking assignment
            s1_data  = '0;       // BUG: blocking assignment
        end else begin
            s1_valid = in_valid; // BUG: blocking assignment
            s1_data  = in_data;  // BUG: blocking assignment
        end
    end

    // Stage 2 capture (drives outputs)
    always @(posedge clk) begin
        if (rst) begin
            out_valid = 1'b0;         // BUG: blocking assignment
            out_data  = '0;           // BUG: blocking assignment
        end else begin
            out_valid = s1_valid;     // BUG: blocking assignment
            out_data  = s1_data;      // BUG: blocking assignment
        end
    end

endmodule

