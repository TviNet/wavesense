// Simple 8-bit counter with synchronous reset
module counter (
    input  wire clk,
    input  wire rst,
    input  wire en,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (rst) begin
            count <= 8'd0;
        end else if (en) begin
            count <= count + 8'd1;
        end
    end
endmodule

