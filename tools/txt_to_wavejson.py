#!/usr/bin/env python3
"""
Convert waveform txt files to WaveJSON format for easy rendering.

WaveJSON is a standardized format for digital timing diagrams:
https://github.com/wavedrom/schema/blob/master/WaveJSON.md
"""

import json
import sys
import argparse
from pathlib import Path
import re


def parse_wave_txt(content):
    """Parse the waveform txt format into structured data."""
    lines = content.strip().split('\n')
    col_map = {}  # index -> signal name
    data_rows = []
    
    # Parse header section (signal mappings)
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        # Check if we've hit the data section
        if re.match(r'^\d+(\s+\d+)+\s*$', line) or '=====' in line:
            break
            
        # Parse signal mapping: "index signal_name"
        match = re.match(r'^(\d+)\s+(.+)$', line)
        if match:
            index = int(match.group(1))
            signal_name = match.group(2).strip()
            col_map[index] = signal_name
        
        i += 1
    
    # Skip until after separator
    while i < len(lines) and '=====' not in lines[i]:
        i += 1
    i += 1  # Skip the separator line
    
    # Parse data rows
    while i < len(lines):
        line = lines[i].strip()
        if not line or '=====' in line:
            i += 1
            continue
            
        tokens = line.split()
        if len(tokens) >= len(col_map):
            data_rows.append(tokens)
        i += 1
    
    # Build time series data
    series = {}
    sorted_indices = sorted(col_map.keys())
    
    for idx in sorted_indices:
        signal_name = col_map[idx]
        series[signal_name] = []
    
    for row in data_rows:
        for idx in sorted_indices:
            if idx < len(row):
                signal_name = col_map[idx]
                value = row[idx]
                
                # Convert hex values for count signals
                if 'count' in signal_name.lower():
                    try:
                        series[signal_name].append(int(value, 16))
                    except ValueError:
                        series[signal_name].append(0)
                else:
                    try:
                        series[signal_name].append(int(value))
                    except ValueError:
                        series[signal_name].append(0)
    
    return col_map, series


def generate_wave_string(values, signal_type='digital'):
    """Generate WaveJSON wave string from values."""
    if not values:
        return "0"
    
    if signal_type == 'digital':
        # For digital signals, create transitions
        wave = ""
        current_val = None
        
        for val in values:
            if current_val is None:
                wave += "0" if val == 0 else "1"
                current_val = val
            elif val != current_val:
                wave += "0" if val == 0 else "1"
                current_val = val
            else:
                wave += "."
        
        return wave
    
    elif signal_type == 'data':
        # For data signals (like count), show value changes
        wave = ""
        data = []
        current_val = None
        
        for val in values:
            if current_val is None or val != current_val:
                wave += "="
                data.append(f"0x{val:02x}")
                current_val = val
            else:
                wave += "."
        
        return wave, data
    
    return "0"


def txt_to_wavejson(txt_content, title="Waveform"):
    """Convert txt waveform data to WaveJSON format."""
    col_map, series = parse_wave_txt(txt_content)
    
    # Identify signal types
    signal_names = [col_map[i] for i in sorted(col_map.keys()) if 'time' not in col_map[i].lower()]
    
    # Build WaveJSON structure
    wavejson = {
        "signal": []
    }
    
    # Add config for better rendering
    wavejson["config"] = {
        "hscale": 2,
        "skin": "narrow"
    }
    
    # Add head with title
    if title:
        wavejson["head"] = {
            "text": title
        }
    
    for signal_name in signal_names:
        if signal_name not in series:
            continue
            
        values = series[signal_name]
        
        # Determine signal type
        if 'clk' in signal_name.lower():
            # Clock signal - special handling
            wave = "P" + "." * (len(values) - 1)
            signal_entry = {
                "name": signal_name,
                "wave": wave
            }
        elif 'count' in signal_name.lower():
            # Data signal
            wave, data = generate_wave_string(values, 'data')
            signal_entry = {
                "name": signal_name,
                "wave": wave,
                "data": data
            }
        else:
            # Digital signal (rst, en, etc.)
            wave = generate_wave_string(values, 'digital')
            signal_entry = {
                "name": signal_name,
                "wave": wave
            }
        
        wavejson["signal"].append(signal_entry)
    
    return wavejson


def main():
    parser = argparse.ArgumentParser(description='Convert waveform txt to WaveJSON')
    parser.add_argument('input_file', help='Input txt waveform file')
    parser.add_argument('-o', '--output', help='Output JSON file (default: stdout)')
    parser.add_argument('-t', '--title', default='Waveform', help='Waveform title')
    parser.add_argument('--pretty', action='store_true', help='Pretty print JSON')
    
    args = parser.parse_args()
    
    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found", file=sys.stderr)
        return 1
    
    try:
        with open(input_path, 'r') as f:
            txt_content = f.read()
        
        # Convert to WaveJSON
        wavejson = txt_to_wavejson(txt_content, args.title)
        
        # Output
        json_str = json.dumps(wavejson, indent=2 if args.pretty else None)
        
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                f.write(json_str)
            print(f"WaveJSON written to {output_path}")
        else:
            print(json_str)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
