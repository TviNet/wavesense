# WaveSense

**AI-powered RTL design improvements through hypothesis and experimentation**

WaveSense is an automated tool that uses GPT-5 to understand digital hardware designs by intelligently generating hypothesis, running simulations, and analyzing waveforms to build comprehensive mental models. This tool iteratively runs the experiments until a much better understanding of how chips actually behave is achieved. 

## What Does WaveSense Do?

WaveSense acts like an AI scientist that:

- **Analyzes RTL designs** by reading Verilog/SystemVerilog code
- **Generates intelligent test hypotheses** about different features of the design
- **Runs targeted simulations** using industry-standard tools (VCS/Verilator)
- **Interprets waveforms** to validate or refute hypotheses
- **Builds and updates its mental model** documenting the actual behavior of the design
- **Iteratively improves** understanding through multiple experimentation cycles

##  Key Features

### **AI-Driven Analysis**
- Uses GPT/Codex to intelligently analyze RTL code
- Generates meaningful test scenarios automatically
- Interprets complex waveform behaviors like a human expert

### 🔬 **Comprehensive Testing**
- Creates systematic test coverage for design behaviors
- Tests edge cases, boundary conditions, and corner scenarios
- Validates reset behavior, clocking, state transitions, and data flows

### **Rich Output Artifacts**
- **Hypotheses**: Structured predictions about design behavior
- **Waveforms**: Both VCD and human-readable text formats
- **Mental Models**: Clear documentation of actual vs. expected behavior
- **Test Coverage**: Systematic validation of design features

### **Industry-Standard Tools**
- Supports VCS (industry-standard) and Verilator simulators
- Generates professional VCD waveforms
- Compatible with existing RTL design flows

## Quick Example

Given a simple counter design like this:

```verilog
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
```

WaveSense will automatically:

1. **Generate hypotheses** like:
   - "Reset should clear counter to zero synchronously"
   - "Enable should gate counting behavior"
   - "Counter should wrap around at 8-bit boundary (255→0)"

2. **Create targeted tests** for each hypothesis

3. **Analyze waveforms** and produce insights like:
   ```
   ## Reset Behavior
   - Key points: Reset clears to zero synchronously
   - Rendered waveform shows count=0 at posedges with rst=1
   
   ## Enable Gating  
   - Key points: Enable gates counting
   - Waveform shows count holds when en=0, increments when en=1
   ```

## Installation & Setup

### Prerequisites

1. **Codex CLI** (OpenAI's code execution environment)
   ```bash
   npm install -g @openai/codex
   ```

2. **Configure Codex** (`~/.codex/config.toml`):
   ```toml
   model = "gpt-4"
   approval_policy = "on-request"
   sandbox_mode = "workspace-write"
   ```

3. **VCD Tools**:
   ```bash
   pip install vcdvcd
   ```

4. **EDA Simulator** (choose one):
   - **VCS** (recommended for professional use)
   - **Verilator** (open-source alternative)

### Environment Setup

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Analysis

```bash
python src/wavesense.py design.v filelist.f output_directory
```

### Example with Provided Designs

```bash
# Analyze a simple counter
python src/wavesense.py example_rtl/counter.v example_rtl/counter.f counter_analysis

# Analyze a buggy pipeline (demonstrates race conditions)
python src/wavesense.py example_rtl/buggy_pipeline.v example_rtl/buggy_pipeline.f pipeline_analysis

# Analyze a comparator
python src/wavesense.py example_rtl/comparator.sv example_rtl/comparator.f comparator_analysis
```

### Verbose Output

```bash
python src/wavesense.py --verbose design.v filelist.f output_dir
```

## 📁 Output Structure

WaveSense creates a comprehensive analysis directory:

```
output_directory/
├── hypotheses.md          # AI-generated test hypotheses  
├── mental_model.md        # Final behavioral understanding
├── log.txt               # Complete execution log
├── testbenches/          # Generated SystemVerilog testbenches
│   ├── testbench_h1.sv
│   ├── testbench_h2.sv
│   └── ...
├── waves/                # Simulation results
│   ├── h1.vcd           # Raw waveform data
│   ├── h1.txt           # Human-readable waveforms
│   └── ...
└── run_experiments.sh    # Simulation execution script
```

## How It Works

### 1. **Intelligent Analysis**
The AI reads your RTL code and forms hypotheses about expected behavior:
- Clock and reset behavior
- State machine transitions  
- Data path operations
- Edge cases and boundary conditions

### 2. **Targeted Test Generation**
For each hypothesis, WaveSense creates focused testbenches that:
- Exercise specific design features
- Test corner cases and edge conditions
- Validate timing relationships
- Check for race conditions or bugs

### 3. **Simulation & Waveform Analysis**
- Runs simulations using professional EDA tools
- Generates both VCD (standard) and text waveforms
- AI analyzes waveforms to validate or refute hypotheses

### 4. **Mental Model Building**
- Documents actual vs. expected behavior
- Identifies bugs, race conditions, or unexpected behaviors
- Creates comprehensive design documentation
- Iteratively refines understanding

## Example Designs

The repository includes several example designs to demonstrate WaveSense capabilities:

### **Counter** (`example_rtl/counter.v`)
- Simple 8-bit synchronous counter
- Demonstrates basic clocking, reset, and enable logic
- Good for understanding fundamental digital design patterns

### **Buggy Pipeline** (`example_rtl/buggy_pipeline.v`)
- Intentionally flawed two-stage pipeline
- Uses blocking assignments incorrectly
- Demonstrates how WaveSense can detect subtle timing bugs

### **Comparator** (`example_rtl/comparator.sv`)
- Combinatorial logic example
- Shows how WaveSense handles pure combinational designs

## 🔍 Real-World Applications

### **Design Verification**
- Automatically discover design bugs
- Validate complex state machine behaviors
- Test edge cases that manual testing might miss

### **Design Documentation**
- Generate comprehensive behavioral documentation
- Create test cases for regression testing
- Build institutional knowledge about design behavior

### **Education & Learning**
- Understand how digital designs actually work
- Learn about timing, clocking, and synchronization
- Discover the difference between intended and actual behavior

## Advanced Features

### **Iterative Refinement**
WaveSense doesn't just run once—it learns and improves:
- Uses results from early tests to generate better tests
- Refines hypotheses based on waveform analysis
- Builds increasingly sophisticated understanding

### **Bug Detection**
WaveSense is particularly good at finding:
- Race conditions and timing bugs
- Reset/clock domain issues
- Unintended latches or combinational loops
- State machine deadlocks or unreachable states

### **Professional Integration**
- Works with existing RTL design flows
- Uses industry-standard file formats (VCD, Verilog)
- Integrates with professional EDA tools
- Generates reusable testbenches


**WaveSense: Making RTL Design understanding as intelligent as your designs deserve.**