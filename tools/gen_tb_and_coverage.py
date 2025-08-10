#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ART = ROOT / "temp_artifacts"
OBJ = ART / "obj_dir"
BIN_DIR = ART / "bin"
WAVES_DIR = ART / "waves"


def log(msg: str):
    print(f"[gen] {msg}")


def require_tool(cmd: str):
    if shutil.which(cmd) is None:
        raise RuntimeError(f"Required tool not found on PATH: {cmd}")


def extract_cpp_code(raw_output: str) -> str:
    """
    Extract only the C++ code from Codex output, filtering out metadata and explanations.
    """
    lines = raw_output.split('\n')
    cpp_lines = []
    in_code_block = False
    found_includes = False
    
    for line in lines:
        # Skip metadata lines with timestamps, dashes, etc.
        if (line.startswith('[') and ']' in line) or line.startswith('---') or 'workdir:' in line or 'model:' in line:
            continue
        
        # Look for start of C++ code
        if line.strip().startswith('#include') and not found_includes:
            found_includes = True
            in_code_block = True
        
        # If we found includes, start collecting C++ code
        if found_includes and in_code_block:
            # Skip lines that look like explanations or markdown
            if (line.strip().startswith('```') or 
                line.strip().startswith('*') or 
                line.strip().startswith('-') and not line.strip().startswith('- ') or
                'User instructions:' in line or
                'Mental Model:' in line):
                continue
                
            cpp_lines.append(line)
    
    # If no includes found, try to find any C++ looking content
    if not found_includes:
        for line in lines:
            if ('int main(' in line or 'void ' in line or 'class ' in line or 
                '#include' in line or 'using namespace' in line):
                found_includes = True
                break
        
        if found_includes:
            # Collect lines that look like C++ code
            for line in lines:
                if (line.strip() and not line.startswith('[') and not line.startswith('---') and
                    'workdir:' not in line and 'model:' not in line and
                    'User instructions:' not in line):
                    cpp_lines.append(line)
    
    return '\n'.join(cpp_lines).strip()


def fix_common_cpp_issues(code: str) -> str:
    """
    Fix common issues in LLM-generated C++ code.
    """
    # Fix incorrect include for verilated coverage
    code = code.replace('#include "verilatedcov.h"', '#include <verilated_cov.h>')
    code = code.replace('#include <verilatedcov.h>', '#include <verilated_cov.h>')
    code = code.replace('#include "verilated_cov.h"', '#include <verilated_cov.h>')
    
    # Fix other common header issues
    code = code.replace('#include "verilated.h"', '#include <verilated.h>')
    code = code.replace('#include "verilated_vcd_c.h"', '#include <verilated_vcd_c.h>')
    
    # Remove any remaining explanatory text that looks like comments but isn't
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines that look like natural language explanations
        stripped = line.strip()
        if (stripped and not stripped.startswith('//') and not stripped.startswith('/*') and
            any(phrase in stripped.lower() for phrase in [
                "i need to", "i'll", "i can", "i'm setting", "next, i", 
                "user instructions:", "mental model:", "addressing edge",
                "requirements:", "critical:"
            ])):
            continue
        
        cleaned_lines.append(line)
    
    code = '\n'.join(cleaned_lines)
    
    # Add sc_time_stamp function if missing
    if 'sc_time_stamp()' not in code:
        # Find where to insert it (after main_time declaration)
        lines = code.split('\n')
        insert_point = -1
        
        for i, line in enumerate(lines):
            if 'main_time' in line and ('static' in line or 'vluint64_t' in line):
                insert_point = i + 1
                break
        
        if insert_point > 0:
            lines.insert(insert_point, '')
            lines.insert(insert_point + 1, 'double sc_time_stamp() { return main_time; }')
            code = '\n'.join(lines)
    
    return code


def call_codex_to_generate_testbench(mental_model_path: Path, module_name: str = "counter") -> str:
    """
    Use Codex LLM to generate a complete C++ testbench based ONLY on the mental model.
    The RTL is not provided to the LLM - it should infer the interface from the mental model.
    """
    if not mental_model_path.exists():
        raise RuntimeError(f"Mental model not found: {mental_model_path}")
    
    mental_model_content = mental_model_path.read_text()
    
    prompt = f"""Generate a C++ testbench for Verilator based on this mental model:

{mental_model_content}

Requirements:
- Use V{module_name} class to instantiate the design
- Include VCD tracing with VerilatedVcdC
- Include coverage support with VerilatedCov
- MUST include 'double sc_time_stamp() {{ return 0; }}' function (required by Verilator)
- Test all behaviors mentioned in the mental model
- Write coverage data at the end
- Infer interface from mental model descriptions

CRITICAL: Output ONLY valid C++ code that starts with #include statements. No explanations, timestamps, markdown, or other text. Just pure C++ code that can be compiled directly."""

    try:
        # Call codex to generate the testbench (pass prompt directly)
        result = subprocess.run([
            "codex", "exec", prompt
        ], capture_output=True, text=True, check=True)
        
        raw_output = result.stdout.strip()
        print("raw_output is ", raw_output)
        
        # Extract only the C++ code part (filter out metadata/explanations)
        generated_code = extract_cpp_code(raw_output)
        
        # Post-process to fix common issues
        generated_code = fix_common_cpp_issues(generated_code)
        
        # Basic validation that we got C++ code
        if not generated_code or '#include' not in generated_code:
            raise RuntimeError(f"Codex did not generate valid C++ code. Got: {raw_output[:200]}...")
        
        log(f"Successfully generated testbench using Codex LLM")
        return generated_code
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Codex failed to generate testbench: {e.stderr}")


def generate_testbench_with_llm(mental_model_path: Path, module_name: str, out_cpp: Path):
    """
    Generate a C++ testbench using Codex LLM based ONLY on the mental model.
    """
    log("Generating testbench using Codex LLM from mental model...")
    
    # Call Codex to generate the testbench (no RTL provided)
    generated_cpp = call_codex_to_generate_testbench(mental_model_path, module_name)
    
    # Write the generated code to file
    out_cpp.write_text(generated_cpp)
    log(f"Wrote LLM-generated testbench: {out_cpp}")
    
    return generated_cpp


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None):
    log("$ " + " ".join(cmd))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=True)


def build_and_run(top: Path, cpp_tb: Path, module_name: str = "counter") -> None:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    WAVES_DIR.mkdir(parents=True, exist_ok=True)
    OBJ.mkdir(parents=True, exist_ok=True)

    # 1) Verilate with coverage enabled
    run([
        "verilator",
        "-Wall",
        "--trace",
        "--cc",
        str(top),
        "--Mdir",
        str(OBJ),
        "--top-module",
        module_name,
        "--coverage",
    ])

    # 2) Compile generated C++ with testbench and coverage support
    verilator_root = subprocess.check_output(["verilator", "-getenv", "VERILATOR_ROOT"]).decode().strip()
    bin_path = BIN_DIR / "counter_cov_sim"
    compile_cmd = [
        "c++",
        "-std=c++17",
        "-O2",
        f"-I{OBJ}",
        f"-I{verilator_root}/include",
        f"-I{verilator_root}/include/vltstd",
        "-DVM_TRACE=1",
        # Model and support sources
        *[str(p) for p in sorted(OBJ.glob("*.cpp"))],
        str(cpp_tb),
        f"{verilator_root}/include/verilated.cpp",
        f"{verilator_root}/include/verilated_threads.cpp",
        f"{verilator_root}/include/verilated_vcd_c.cpp",
        f"{verilator_root}/include/verilated_cov.cpp",
        "-o",
        str(bin_path),
    ]
    run(compile_cmd)

    # 3) Run once; testbench iterates scenarios and writes VCDs and coverage.dat
    run([str(bin_path)])


def parse_lcov(info_path: Path) -> dict:
    """Parse a subset of LCOV .info to aggregate line + branch coverage."""
    data: dict[str, dict] = {}
    current = None
    for line in info_path.read_text().splitlines():
        if line.startswith("SF:"):
            current = line[3:].strip()
            data[current] = data.get(current, {"lines": {"found": 0, "hit": 0}, "branches": {"found": 0, "hit": 0}})
        elif line.startswith("DA:") and current:
            # DA:<line>,<count>
            try:
                _lno, cnt = line[3:].split(",")
                data[current]["lines"]["found"] += 1
                if int(cnt) > 0:
                    data[current]["lines"]["hit"] += 1
            except Exception:
                pass
        elif line.startswith("BRDA:") and current:
            # BRDA:<line>,<block>,<branch>,<taken or ->
            try:
                _lno, _blk, _br, taken = line[5:].split(",")
                data[current]["branches"]["found"] += 1
                if taken != "-" and int(taken) > 0:
                    data[current]["branches"]["hit"] += 1
            except Exception:
                pass
        elif line.startswith("end_of_record"):
            current = None

    # Aggregate totals
    totals = {"lines": {"found": 0, "hit": 0}, "branches": {"found": 0, "hit": 0}}
    for f, v in data.items():
        for k in ("lines", "branches"):
            totals[k]["found"] += v[k]["found"]
            totals[k]["hit"] += v[k]["hit"]

    return {"files": data, "totals": totals}


def pct(hit: int, found: int) -> float:
    return (100.0 * hit / found) if found else 100.0


def write_dashboard(report: dict, out_html: Path):
    totals = report["totals"]
    line_pct = pct(totals["lines"]["hit"], totals["lines"]["found"])
    branch_pct = pct(totals["branches"]["hit"], totals["branches"]["found"])

    rows = []
    for fname, v in sorted(report["files"].items()):
        lp = pct(v["lines"]["hit"], v["lines"]["found"])
        bp = pct(v["branches"]["hit"], v["branches"]["found"])
        # Shorten the filename for display
        display_name = fname.split('/')[-1] if '/' in fname else fname
        rows.append(
            f"<tr><td title='{fname}'>{display_name}</td><td>{v['lines']['hit']}/{v['lines']['found']} ({lp:.1f}%)"\
            f"</td><td>{v['branches']['hit']}/{v['branches']['found']} ({bp:.1f}%)</td></tr>"
        )

    # Status indicators
    line_status = "🟢" if line_pct >= 95 else "🟡" if line_pct >= 80 else "🔴"
    branch_status = "🟢" if branch_pct >= 95 else "🟡" if branch_pct >= 80 else "🔴"

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>WaveSense Coverage Dashboard</title>
  <style>
    body {{ font-family: -apple-system, system-ui, sans-serif; margin: 24px; background: #fafbfc; }}
    .header {{ text-align: center; margin-bottom: 32px; }}
    .header h1 {{ color: #1a1d29; margin-bottom: 8px; }}
    .header p {{ color: #6b7280; margin: 0; }}
    .cards {{ display: flex; gap: 16px; margin-bottom: 24px; justify-content: center; }}
    .card {{ padding: 16px 20px; border-radius: 12px; background: white; border: 1px solid #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 200px; text-align: center; }}
    .card-value {{ font-size: 24px; font-weight: bold; margin-bottom: 4px; }}
    .card-label {{ color: #6b7280; font-size: 14px; }}
    .status {{ font-size: 20px; margin-left: 8px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    th, td {{ padding: 12px 16px; text-align: left; }}
    th {{ background: #f8fafc; font-weight: 600; color: #374151; border-bottom: 1px solid #e5e7eb; }}
    td {{ border-bottom: 1px solid #f3f4f6; }}
    tr:hover td {{ background: #f8fafc; }}
    .footer {{ margin-top: 24px; text-align: center; color: #6b7280; font-size: 14px; }}
    .llm-badge {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 500; margin-left: 12px; }}
  </style>
  </head>
  <body>
    <div class="header">
      <h1>🌊 WaveSense Coverage Dashboard <span class="llm-badge">LLM Generated</span></h1>
      <p>Testbench generated purely from mental model using Codex LLM, then tested against RTL</p>
    </div>
    
    <div class="cards">
      <div class="card">
        <div class="card-value">{totals['lines']['hit']}/{totals['lines']['found']} <span class="status">{line_status}</span></div>
        <div class="card-label">Line Coverage ({line_pct:.1f}%)</div>
      </div>
      <div class="card">
        <div class="card-value">{totals['branches']['hit']}/{totals['branches']['found']} <span class="status">{branch_status}</span></div>
        <div class="card-label">Branch Coverage ({branch_pct:.1f}%)</div>
      </div>
    </div>
    
    <h3 style="margin-bottom: 16px; color: #374151;">📁 Per-file Coverage</h3>
    <table>
      <tr>
        <th>File</th>
        <th>Lines</th>
        <th>Branches</th>
      </tr>
      {''.join(rows)}
    </table>
    
    <div style="margin-top: 24px; text-align: center;">
      <button onclick="optimizeCoverage()" style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        transition: all 0.2s ease;
      " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(102, 126, 234, 0.5)'" 
         onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)'">
        🚀 Optimize Coverage
      </button>
      <p style="margin-top: 8px; color: var(--muted); font-size: 12px;">Generate additional test scenarios to improve coverage</p>
    </div>
    
    <div class="footer">
      <p>🔧 Build artifacts in <code>temp_artifacts/</code> | 📊 Raw data: <code>coverage.dat</code>, <code>coverage.info</code></p>
      <p>Generated testbench: <code>sim_main.cpp</code> | VCD waveforms: <code>waves/</code></p>
    </div>
    
    <script>
      async function optimizeCoverage() {{
        const button = document.querySelector('button');
        const originalText = button.innerHTML;
        button.innerHTML = '⏳ Optimizing...';
        button.disabled = true;
        
        try {{
          const response = await fetch('http://localhost:8080/optimize', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ action: 'optimize_coverage' }})
          }});
          
          if (response.ok) {{
            const result = await response.json();
            if (result.success) {{
              alert('✅ Coverage optimization complete! New scenarios added.\\n\\nReloading dashboard...');
              window.location.reload();
            }} else {{
              alert('❌ Optimization failed: ' + result.error);
            }}
          }} else {{
            alert('❌ Server error during optimization.');
          }}
        }} catch (error) {{
          alert('❌ Network error: ' + error.message);
        }} finally {{
          button.innerHTML = originalText;
          button.disabled = false;
        }}
      }}
    </script>
  </body>
  </html>
"""
    out_html.write_text(html)
    log(f"Wrote enhanced dashboard: {out_html}")


def analyze_coverage_gaps(report: dict, existing_testbench: str) -> str:
    """
    Analyze coverage report and existing testbench to identify gaps.
    """
    gaps = []
    
    # Check overall coverage levels
    totals = report["totals"]
    line_pct = pct(totals["lines"]["hit"], totals["lines"]["found"])
    branch_pct = pct(totals["branches"]["hit"], totals["branches"]["found"])
    
    if line_pct < 100:
        unhit_lines = totals["lines"]["found"] - totals["lines"]["hit"]
        gaps.append(f"Missing line coverage: {unhit_lines} lines not executed")
    
    if branch_pct < 100:
        unhit_branches = totals["branches"]["found"] - totals["branches"]["hit"]
        gaps.append(f"Missing branch coverage: {unhit_branches} branches not taken")
    
    # Analyze testbench patterns to identify missing scenarios
    testbench_lower = existing_testbench.lower()
    
    # Common patterns that might be missing
    if "corner case" not in testbench_lower and "edge" not in testbench_lower:
        gaps.append("Potential missing edge cases and corner conditions")
    
    if line_pct >= 95 and branch_pct < 95:
        gaps.append("Good line coverage but missing conditional branches - need more decision path testing")
    
    if "stress" not in testbench_lower and "continuous" not in testbench_lower:
        gaps.append("Missing stress testing and continuous operation scenarios")
    
    return "; ".join(gaps) if gaps else "Coverage appears comprehensive"


def optimize_coverage(mental_model_path: Path, existing_testbench_path: Path, coverage_report: dict, module_name: str) -> str:
    """
    Generate additional testbench scenarios to improve coverage using LLM.
    """
    if not mental_model_path.exists() or not existing_testbench_path.exists():
        raise RuntimeError("Required files not found for optimization")
    
    mental_model_content = mental_model_path.read_text()
    existing_testbench = existing_testbench_path.read_text()
    
    # Analyze gaps
    coverage_gaps = analyze_coverage_gaps(coverage_report, existing_testbench)
    
    # Get coverage statistics
    totals = coverage_report["totals"]
    line_pct = pct(totals["lines"]["hit"], totals["lines"]["found"])
    branch_pct = pct(totals["branches"]["hit"], totals["branches"]["found"])
    
    prompt = f"""Analyze this existing testbench and generate ADDITIONAL test scenarios to improve coverage.

CURRENT COVERAGE STATUS:
- Line Coverage: {line_pct:.1f}% ({totals['lines']['hit']}/{totals['lines']['found']})
- Branch Coverage: {branch_pct:.1f}% ({totals['branches']['hit']}/{totals['branches']['found']})
- Identified Gaps: {coverage_gaps}

EXISTING TESTBENCH:
```cpp
{existing_testbench}
```

MENTAL MODEL (for reference):
```
{mental_model_content}
```

TASK: Generate ADDITIONAL C++ test scenarios that will increase coverage. Focus on:
1. Testing untested branches and edge cases
2. Corner conditions not covered by existing tests
3. Stress testing and boundary conditions
4. Error/fault injection scenarios
5. State transition edge cases

Generate ONLY the additional C++ code (new functions/scenarios) that can be integrated with the existing testbench. Use the same coding style and patterns as the existing code.

CRITICAL: Output ONLY valid C++ code for new test scenarios. No explanations or markdown."""
    
    try:
        result = subprocess.run([
            "codex", "exec", prompt
        ], capture_output=True, text=True, check=True)
        
        raw_output = result.stdout.strip()
        additional_code = extract_cpp_code(raw_output)
        additional_code = fix_common_cpp_issues(additional_code)
        
        if not additional_code:
            raise RuntimeError("Failed to generate additional test scenarios")
        
        log(f"Generated additional test scenarios for coverage optimization")
        return additional_code
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to generate optimization scenarios: {e.stderr}")


def merge_testbench_with_optimization(original_path: Path, additional_code: str, output_path: Path):
    """
    Merge the original testbench with additional optimization scenarios.
    """
    original_code = original_path.read_text()
    
    # Find a good insertion point (before the final cleanup in main)
    lines = original_code.split('\n')
    insertion_point = -1
    
    # Look for the coverage write or return statement in main
    for i, line in enumerate(lines):
        if ('VerilatedCov::write' in line or 
            'return 0' in line or 
            'delete tfp' in line):
            insertion_point = i
            break
    
    if insertion_point == -1:
        # Fallback: insert before the last closing brace
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == '}':
                insertion_point = i
                break
    
    if insertion_point > 0:
        # Insert additional scenarios
        lines.insert(insertion_point, "")
        lines.insert(insertion_point + 1, "    // === OPTIMIZATION SCENARIOS ===")
        
        # Add the additional code with proper indentation
        additional_lines = additional_code.split('\n')
        for line in additional_lines:
            if line.strip():
                lines.insert(insertion_point + 2, "    " + line)
            else:
                lines.insert(insertion_point + 2, "")
            insertion_point += 1
        
        lines.insert(insertion_point + 2, "    // === END OPTIMIZATION ===")
        lines.insert(insertion_point + 3, "")
    
    merged_code = '\n'.join(lines)
    output_path.write_text(merged_code)
    log(f"Merged optimized testbench saved to: {output_path}")


def main():
    ap = argparse.ArgumentParser(description="Generate testbench from mental_model.md using LLM and run Verilator coverage against RTL")
    ap.add_argument("--top", default=str(ROOT / "rtl/counter.v"), help="Path to top-level RTL file (used only for Verilator compilation)")
    ap.add_argument("--mental-model", default=str(ART / "mental_model.md"), help="Path to mental_model.md (used for testbench generation)")
    ap.add_argument("--out-cpp", default=str(ART / "sim_main.cpp"), help="Output C++ testbench path")
    ap.add_argument("--serve", action="store_true", help="Start optimization server after generating dashboard")
    ap.add_argument("--port", type=int, default=8080, help="Server port for optimization requests (default: 8080)")
    args = ap.parse_args()

    # Tool checks
    for t in ("verilator", "c++", "verilator_coverage", "codex"):
        require_tool(t)

    rtl_path = Path(args.top)
    mental_model_path = Path(args.mental_model)
    cpp_path = Path(args.out_cpp)

    # Extract module name from RTL (only for Verilator compilation)
    rtl_content = rtl_path.read_text()
    module_match = re.search(r'module\s+(\w+)', rtl_content)
    module_name = module_match.group(1) if module_match else "counter"
    
    log(f"Module name (for Verilator): {module_name}")
    log(f"RTL file (for compilation): {rtl_path}")
    log(f"Mental model (for testbench): {mental_model_path}")

    # Generate testbench using LLM (ONLY from mental model, RTL not provided to LLM)
    generate_testbench_with_llm(mental_model_path, module_name, cpp_path)

    # Build and run (RTL is used here for Verilator compilation and simulation)
    build_and_run(rtl_path, cpp_path, module_name)

    # Produce LCOV info
    info_path = ART / "coverage.info"
    run(["verilator_coverage", "--write-info", str(info_path), str(ART / "coverage.dat")])

    # Parse and write a simple HTML dashboard
    report = parse_lcov(info_path)
    write_dashboard(report, ART / "coverage_dashboard_1.html")

    log("Done. Open temp_artifacts/coverage_dashboard_1.html in a browser.")
    
    # Start optimization server if requested
    if args.serve:
        log(f"Starting optimization server on port {args.port}...")
        try:
            import subprocess
            subprocess.run([
                sys.executable, 
                str(HERE / "coverage_server.py"), 
                "--port", str(args.port)
            ])
        except KeyboardInterrupt:
            log("Server stopped by user")
        except Exception as e:
            log(f"Server error: {e}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"[error] Command failed with exit code {e.returncode}: {' '.join(e.cmd)}", file=sys.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)
