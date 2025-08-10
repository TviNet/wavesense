#include <verilated.h>
#include <verilated_vcd_c.h>
#include "Vcounter.h"
#include <string>
#include <iostream>
#include <cstdlib>

static vluint64_t main_time = 0;
double sc_time_stamp() { return main_time; }

static void tick(Vcounter* top, VerilatedVcdC* tfp) {
    // clk low
    top->clk = 0; top->eval(); if (tfp) tfp->dump(main_time++);
    // clk high
    top->clk = 1; top->eval(); if (tfp) tfp->dump(main_time++);
}

static void reset(Vcounter* top, VerilatedVcdC* tfp, int cycles) {
    top->rst = 1; top->eval(); if (tfp) tfp->dump(main_time++);
    for (int i = 0; i < cycles; ++i) tick(top, tfp);
    top->rst = 0; top->eval(); if (tfp) tfp->dump(main_time++);
}

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Verilated::traceEverOn(true);

    std::string test = argc > 1 ? std::string(argv[1]) : std::string("basic_counting");
    std::string vcd_path = argc > 2 ? std::string(argv[2]) : std::string("waves.vcd");

    Vcounter* top = new Vcounter;

    VerilatedVcdC* tfp = new VerilatedVcdC;
    top->trace(tfp, 99);
    tfp->open(vcd_path.c_str());

    // Init
    top->clk = 0; top->rst = 0; top->en = 0; top->eval(); tfp->dump(main_time++);

    if (test == "basic_counting") {
        reset(top, tfp, 1);
        top->en = 1;
        for (int i = 0; i < 20; ++i) tick(top, tfp);
        top->en = 0; for (int i = 0; i < 5; ++i) tick(top, tfp);
    } else if (test == "hold_when_disabled") {
        reset(top, tfp, 1);
        // Count a bit
        top->en = 1; for (int i = 0; i < 5; ++i) tick(top, tfp);
        // Hold
        top->en = 0; for (int i = 0; i < 10; ++i) tick(top, tfp);
        // Re-enable
        top->en = 1; for (int i = 0; i < 5; ++i) tick(top, tfp);
    } else if (test == "reset_behavior") {
        // Assert reset for multiple cycles with en toggling
        top->en = 1; reset(top, tfp, 2);
        for (int i = 0; i < 5; ++i) tick(top, tfp);
        top->en = 0; reset(top, tfp, 1);
        for (int i = 0; i < 5; ++i) tick(top, tfp);
    } else if (test == "rst_over_en_priority") {
        reset(top, tfp, 1);
        top->en = 1; for (int i = 0; i < 5; ++i) tick(top, tfp);
        // While en=1, assert reset for several cycles
        top->rst = 1; for (int i = 0; i < 4; ++i) tick(top, tfp);
        top->rst = 0; for (int i = 0; i < 6; ++i) tick(top, tfp);
    } else if (test == "wraparound") {
        // Drive count near 0xFE then wrap
        reset(top, tfp, 1);
        top->en = 1;
        // 0 -> 0xFE needs 254 increments
        for (int i = 0; i < 254; ++i) tick(top, tfp);
        for (int i = 0; i < 4; ++i) tick(top, tfp); // show FE, FF, 00, 01
        top->en = 0; for (int i = 0; i < 4; ++i) tick(top, tfp);
    } else if (test == "mid_stream_reset") {
        reset(top, tfp, 1);
        top->en = 1; for (int i = 0; i < 8; ++i) tick(top, tfp);
        // single cycle reset pulse mid-stream
        top->rst = 1; tick(top, tfp);
        top->rst = 0; for (int i = 0; i < 8; ++i) tick(top, tfp);
    } else {
        std::cerr << "Unknown test: " << test << "\n";
    }

    tfp->close();
    delete tfp;
    top->final();
    delete top;
    return 0;
}
