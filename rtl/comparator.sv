module Comparator #(
    parameter int num_triggers = 4,
    parameter int num_slots = 4
) (
    input  logic [63:0] tdata2 [num_slots-1:0],
    input  logic [63:0] csr_values [num_triggers-1:0][num_slots-1:0],
    input  logic [3:0]  match_mode,
    output logic        MatchEq [num_triggers-1:0][num_slots-1:0],
    output logic        Match [num_triggers-1:0][num_slots-1:0],
    input logic clk,
    input logic rst
);

    logic [63:0] mask_high;
    logic [31:0] mask_low;

    // Determine the mask value for napot
    function automatic logic [5:0] get_mask(input logic [63:0] data);
        logic [5:0] mask;
        mask = 0;
        for (int i = 0; i < 64; i++) begin
            if (data[i] == 1'b0) begin
                mask = 63 - i;
                break;
            end
        end
        return mask;
    endfunction

    // MatchEq output always behaves like `match == 0`
    always_comb begin
        for (int i = 0; i < num_triggers; i++) begin
            for (int j = 0; j < num_slots; j++) begin
                MatchEq[i][j] = (csr_values[i][j] == tdata2[j]);
            end
        end
    end

    // Match output behaves according to `match == k`
    always_comb begin
        static int j;
        for (int i = 0; i < num_triggers; i++) begin
            for (j = 0; j < num_slots; j++) begin
                case (match_mode)
                    4'd0: begin
                        Match[i][j] = tdata2[j] == csr_values[i][j];
                    end
                    4'd1: begin
                        static logic [63:0] mask = ~(64'hFFFFFFFFFFFFFFFF >> get_mask(tdata2[j]));
                        Match[i][j] = (csr_values[i][j] & mask) == (tdata2[j] & mask);
                    end
                    4'd2: begin
                        Match[i][j] = csr_values[i][j] >= tdata2[j];
                    end
                    4'd3: begin
                        Match[i][j] = csr_values[i][j] < tdata2[j];
                    end
                    4'd4: begin
                        mask_low = tdata2[j][63:32];
                        Match[i][j] = (csr_values[i][j][31:0] & mask_low) == tdata2[j][31:0];
                    end
                    4'd5: begin
                        mask_high = tdata2[j][63:32];
                        Match[i][j] = (csr_values[i][j][63:32] & mask_high) == tdata2[j][31:0];
                    end
                    4'd8: begin
                        Match[i][j] = !(csr_values[i][j] == tdata2[j]);
                    end
                    4'd9: begin
                        static logic [63:0] mask = ~(64'hFFFFFFFFFFFFFFFF >> get_mask(tdata2[j]));
                        Match[i][j] = !((csr_values[i][j] & mask) == (tdata2[j] & mask));
                    end
                    4'd12: begin
                        mask_low = tdata2[j][63:32];
                        Match[i][j] = !((csr_values[i][j][31:0] & mask_low) == tdata2[j][31:0]);
                    end
                    4'd13: begin
                        mask_high = tdata2[j][63:32];
                        Match[i][j] = !((csr_values[i][j][63:32] & mask_high) == tdata2[j][31:0]);
                    end
                    default: begin
                        Match[i][j] = '0;
                    end
                endcase
            end
        end
    end

endmodule
