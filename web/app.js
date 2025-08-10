// Minimal client to parse mental_model.md and render waveforms

const MENTAL_MODEL_PATH = '../temp_artifacts/mental_model.md';
const WAVES_BASE = '../temp_artifacts/waves/';

const COLORS = {
  clk: '#6ea8fe',
  rst: '#f97066',
  en: '#f7c948',
  count: '#30c48d',
  axis: '#2a2f3a',
  text: '#9aa4b2',
  highlight: '#f7c948',
  grid: '#1a1d29',
};

// Global state for interactions
let globalState = {
  hoveredTime: null,
  hoveredSignal: null,
  zoomLevel: 1,
  panOffset: 0,
  loadedFiles: new Map(),
};

// WaveJSON Converter
class WaveformConverter {
  static parseWaveTxt(content) {
    const lines = content.trim().split('\n');
    const colMap = {};
    const dataRows = [];
    
    let i = 0;
    
    // Parse header section
    while (i < lines.length) {
      const line = lines[i].trim();
      if (!line) {
        i++;
        continue;
      }
      
      if (/^\d+(\s+\d+)+\s*$/.test(line) || line.includes('=====')) {
        break;
      }
      
      const match = line.match(/^(\d+)\s+(.+)$/);
      if (match) {
        colMap[parseInt(match[1])] = match[2].trim();
      }
      i++;
    }
    
    // Skip separator
    while (i < lines.length && !lines[i].includes('=====')) {
      i++;
    }
    i++;
    
    // Parse data rows
    while (i < lines.length) {
      const line = lines[i].trim();
      if (!line || line.includes('=====')) {
        i++;
        continue;
      }
      
      const tokens = line.split(/\s+/);
      if (tokens.length >= Object.keys(colMap).length) {
        dataRows.push(tokens);
      }
      i++;
    }
    
    return { colMap, dataRows };
  }
  
  static generateWaveString(values, signalType = 'digital') {
    if (!values || values.length === 0) return { wave: "0" };
    
    if (signalType === 'clock') {
      return { wave: "P" + ".".repeat(Math.max(0, values.length - 1)) };
    }
    
    if (signalType === 'data') {
      let wave = "";
      const data = [];
      let currentVal = null;
      
      for (const val of values) {
        if (currentVal === null || val !== currentVal) {
          wave += "=";
          data.push(`0x${val.toString(16).padStart(2, '0')}`);
          currentVal = val;
        } else {
          wave += ".";
        }
      }
      
      return { wave, data };
    }
    
    // Digital signal
    let wave = "";
    let currentVal = null;
    
    for (const val of values) {
      if (currentVal === null) {
        wave += val === 0 ? "0" : "1";
        currentVal = val;
      } else if (val !== currentVal) {
        wave += val === 0 ? "0" : "1";
        currentVal = val;
      } else {
        wave += ".";
      }
    }
    
    return { wave };
  }
  
  static txtToWaveJSON(content, title = "Waveform") {
    const { colMap, dataRows } = this.parseWaveTxt(content);
    
    // Build series data
    const series = {};
    const sortedIndices = Object.keys(colMap).map(k => parseInt(k)).sort((a, b) => a - b);
    
    for (const idx of sortedIndices) {
      series[colMap[idx]] = [];
    }
    
    for (const row of dataRows) {
      for (const idx of sortedIndices) {
        if (idx < row.length) {
          const signalName = colMap[idx];
          const value = row[idx];
          
          if (signalName.toLowerCase().includes('count')) {
            try {
              series[signalName].push(parseInt(value, 16));
            } catch {
              series[signalName].push(0);
            }
          } else {
            try {
              series[signalName].push(parseInt(value));
            } catch {
              series[signalName].push(0);
            }
          }
        }
      }
    }
    
    // Generate WaveJSON
    const signals = [];
    const signalNames = sortedIndices.map(i => colMap[i]).filter(name => 
      !name.toLowerCase().includes('time')
    );
    
    for (const signalName of signalNames) {
      if (!series[signalName]) continue;
      
      const values = series[signalName];
      let signalType = 'digital';
      
      if (signalName.toLowerCase().includes('clk')) {
        signalType = 'clock';
      } else if (signalName.toLowerCase().includes('count')) {
        signalType = 'data';
      }
      
      const result = this.generateWaveString(values, signalType);
      const signal = {
        name: signalName,
        wave: result.wave
      };
      
      if (result.data) {
        signal.data = result.data;
      }
      
      signals.push(signal);
    }
    
    return {
      signal: signals,
      config: {
        hscale: 2,
        skin: "narrow"
      },
      head: {
        text: title
      }
    };
  }
}

async function loadText(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to fetch ${path}: ${res.status}`);
  return await res.text();
}

function parseMentalModel(md) {
  const lines = md.split(/\r?\n/);
  const features = [];
  for (const line of lines) {
    const m = /^-\s+([^:]+):\s*(.*)$/i.exec(line.trim());
    if (!m) continue;
    const feature = m[1].trim();
    const codePaths = Array.from(m[2].matchAll(/`([^`]+\.txt)`/g)).map(x => x[1]);
    if (codePaths.length) {
      features.push({ feature, waveFiles: codePaths });
    }
  }
  return features;
}

function parseWaveTxt(text) {
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
  const colMap = new Map(); // index -> name
  let i = 0;
  // Parse mapping lines like "0 time" / "1 TOP.clk"
  for (; i < lines.length; i++) {
    const ln = lines[i];
    if (/^\d+\s+[-=]+$/.test(ln) || /^\d+(\s+\d+)+$/.test(ln)) break; // reached header row
    const m = /^(\d+)\s+(.+)$/.exec(ln);
    if (m) {
      colMap.set(parseInt(m[1], 10), m[2]);
    }
  }
  // Skip until after the ====== separator
  while (i < lines.length && !/^=+$/.test(lines[i].replace(/\s+/g, ''))) i++;
  // Now data rows start after separator
  i++;
  const rows = [];
  for (; i < lines.length; i++) {
    const ln = lines[i];
    if (!ln || /^=+$/.test(ln.replace(/\s+/g, ''))) continue;
    const toks = ln.split(/\s+/);
    if (toks.length < colMap.size) continue;
    rows.push(toks);
  }

  // Build series per signal
  const series = {};
  const colIndices = Array.from(colMap.keys()).sort((a,b)=>a-b);
  for (const col of colIndices) {
    const name = colMap.get(col);
    series[name] = [];
  }
  for (const toks of rows) {
    for (const col of colIndices) {
      const name = colMap.get(col);
      let v = toks[col];
      // count is hexadecimal; others are decimal
      if (/count/i.test(name)) {
        v = parseInt(v, 16);
      } else {
        v = parseInt(v, 10);
      }
      series[name].push(v);
    }
  }

  // Derive time vector (col 0 is time)
  const timeName = colMap.get(0);
  const time = series[timeName] || Array.from({length: rows.length}, (_,k)=>k);
  return { time, series, colMap };
}

function createEl(tag, attrs={}, ...children) {
  const el = document.createElement(tag);
  for (const [k,v] of Object.entries(attrs)) {
    if (k === 'class') el.className = v; else if (k === 'text') el.textContent = v; else el.setAttribute(k, v);
  }
  for (const c of children) {
    if (typeof c === 'string') el.appendChild(document.createTextNode(c));
    else if (c) el.appendChild(c);
  }
  return el;
}

function renderLegend(container, names) {
  const map = {
    clk: 'clk',
    rst: 'rst',
    en: 'en',
    count: 'count',
  };
  const wrap = createEl('div', { class: 'tracks-legend' });
  for (const name of names) {
    let key = 'count';
    if (/clk/i.test(name)) key = 'clk';
    else if (/rst/i.test(name)) key = 'rst';
    else if (/en\b/i.test(name)) key = 'en';
    wrap.appendChild(createEl('span', { class: `pill ${key}` }, name));
  }
  container.appendChild(wrap);
}

function createWaveControls(container, data, canvasId) {
  const controls = createEl('div', { class: 'wave-controls' });
  
  const zoomIn = createEl('button', { text: 'Zoom In' });
  const zoomOut = createEl('button', { text: 'Zoom Out' });
  const reset = createEl('button', { text: 'Reset View' });
  const status = createEl('span', { class: 'status loaded', text: `${data.time.length} samples` });
  
  zoomIn.addEventListener('click', () => {
    globalState.zoomLevel = Math.min(globalState.zoomLevel * 1.5, 10);
    reRenderCanvas(container, data, canvasId);
  });
  
  zoomOut.addEventListener('click', () => {
    globalState.zoomLevel = Math.max(globalState.zoomLevel / 1.5, 0.1);
    reRenderCanvas(container, data, canvasId);
  });
  
  reset.addEventListener('click', () => {
    globalState.zoomLevel = 1;
    globalState.panOffset = 0;
    reRenderCanvas(container, data, canvasId);
  });
  
  const zoomControls = createEl('div', { class: 'zoom-controls' }, zoomIn, zoomOut, reset);
  controls.appendChild(zoomControls);
  controls.appendChild(status);
  
  return controls;
}

function reRenderCanvas(container, data, canvasId) {
  const existingCanvas = container.querySelector(`canvas[data-canvas-id="${canvasId}"]`);
  if (existingCanvas) {
    const parent = existingCanvas.parentElement;
    parent.removeChild(existingCanvas);
    const maxSamples = parseInt(document.getElementById('maxSamples').value, 10) || 160;
    const canvasWidth = parseInt(document.getElementById('canvasWidth').value, 10) || 1000;
    renderWaveformCanvas(parent, data, { maxSamples, width: canvasWidth, canvasId });
  }
}

function renderWaveform(container, data, opts={}) {
  const canvasId = opts.canvasId || `canvas_${Math.random().toString(36).substr(2, 9)}`;
  
  // Add controls
  const controls = createWaveControls(container, data, canvasId);
  container.appendChild(controls);
  
  // Add canvas wrapper
  const canvasWrapper = createEl('div', { class: 'canvas-wrap' });
  container.appendChild(canvasWrapper);
  
  // Render the actual waveform
  renderWaveformCanvas(canvasWrapper, data, { ...opts, canvasId });
  
  // Add signal info panel
  const signalInfo = createEl('div', { class: 'signal-info', id: `info_${canvasId}` });
  container.appendChild(signalInfo);
}

function renderWaveformCanvas(container, data, opts={}) {
  const maxSamples = Math.floor((opts.maxSamples || 160) * globalState.zoomLevel);
  const width = opts.width || 1000;
  const trackH = 60;
  const paddingL = 70;
  const paddingR = 10;
  const paddingT = 10;
  const paddingB = 20;
  const canvasId = opts.canvasId || 'default';

  const names = Array.from(data.colMap.keys()).sort((a,b)=>a-b).map(i => data.colMap.get(i));
  const signalNames = names.filter(n => !/time/i.test(n));
  const totalH = paddingT + paddingB + signalNames.length * trackH;
  const canvas = createEl('canvas', { 
    width: String(width), 
    height: String(totalH),
    'data-canvas-id': canvasId 
  });
  const ctx = canvas.getContext('2d');

  // Add mouse interaction
  addCanvasInteraction(canvas, data, signalNames, canvasId);

  renderLegend(container.parentElement, signalNames);

  const time = data.time.slice(0, maxSamples);
  const tMin = time[0];
  const tMax = time[time.length - 1] || 1;
  const xScale = (t) => paddingL + (t - tMin) * ((width - paddingL - paddingR) / Math.max(1, (tMax - tMin)));

  // Draw vertical grid
  ctx.strokeStyle = COLORS.axis;
  ctx.lineWidth = 1;
  const tickStep = Math.max(1, Math.round((tMax - tMin) / 10));
  for (let t = tMin; t <= tMax; t += tickStep) {
    const x = Math.round(xScale(t)) + 0.5;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, totalH);
    ctx.stroke();
    ctx.fillStyle = COLORS.text;
    ctx.fillText(String(t), x + 2, 10);
  }

  let trackIndex = 0;
  for (const name of signalNames) {
    const yTop = paddingT + trackIndex * trackH;
    const yBase = yTop + trackH - 15;

    // Label
    ctx.fillStyle = COLORS.text;
    ctx.fillText(name, 8, yTop + 14);

    // Baseline
    ctx.strokeStyle = COLORS.axis;
    ctx.beginPath();
    ctx.moveTo(paddingL, yBase);
    ctx.lineTo(width - paddingR, yBase);
    ctx.stroke();

    const vals = data.series[name].slice(0, maxSamples);
    const isDigital = /clk|rst|en\b/i.test(name);
    const color = /clk/i.test(name) ? COLORS.clk : /rst/i.test(name) ? COLORS.rst : /en\b/i.test(name) ? COLORS.en : COLORS.count;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;

    if (isDigital) {
      const y0 = yBase - (trackH - 24); // logical 1 level
      const y1 = yBase; // logical 0 level
      ctx.beginPath();
      for (let k = 0; k < time.length; k++) {
        const x = xScale(time[k]);
        const v = vals[k] ? y0 : y1;
        if (k === 0) ctx.moveTo(x, v);
        else {
          // vertical transition if changed
          const prev = vals[k-1] ? y0 : y1;
          if (prev !== v) ctx.lineTo(x, prev);
          ctx.lineTo(x, v);
        }
      }
      ctx.stroke();
    } else {
      // Analog-ish step plot for count
      const maxVal = 255; // 8-bit
      const yScale = (val) => yBase - (trackH - 24) * Math.max(0, Math.min(1, val / maxVal));
      ctx.beginPath();
      for (let k = 0; k < time.length; k++) {
        const x = xScale(time[k]);
        const y = yScale(vals[k] ?? 0);
        if (k === 0) ctx.moveTo(x, y);
        else {
          // step: horizontal from prev x to this x, then vertical
          const xPrev = xScale(time[k-1]);
          const yPrev = yScale(vals[k-1] ?? 0);
          ctx.lineTo(x, yPrev);
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Optional: annotate at some points
      ctx.fillStyle = color;
      ctx.font = '11px monospace';
      const annotationStep = Math.max(4, Math.floor(time.length/12));
      for (let k = 0; k < time.length; k += annotationStep) {
        const x = xScale(time[k]);
        const y = yBase - 4;
        const val = vals[k] ?? 0;
        if (val !== (vals[k-annotationStep] ?? -1)) { // Only show when value changes
          ctx.fillText('0x' + val.toString(16).padStart(2, '0'), x + 2, y);
        }
      }
      
      // Highlight current value if hovered
      if (globalState.hoveredTime !== null && globalState.hoveredSignal === trackIndex) {
        const hoverX = xScale(time[globalState.hoveredTime]);
        const hoverY = yScale(vals[globalState.hoveredTime] ?? 0);
        ctx.fillStyle = COLORS.highlight;
        ctx.beginPath();
        ctx.arc(hoverX, hoverY, 4, 0, 2 * Math.PI);
        ctx.fill();
      }
    }

    trackIndex++;
  }

  container.appendChild(canvas);
}

async function render() {
  const app = document.getElementById('app');
  app.innerHTML = '';
  const maxSamples = parseInt(document.getElementById('maxSamples').value, 10) || 160;
  const canvasWidth = parseInt(document.getElementById('canvasWidth').value, 10) || 1000;

  // Load mental model
  let md;
  try {
    md = await loadText(MENTAL_MODEL_PATH);
  } catch (e) {
    app.appendChild(createEl('div', { class: 'feature' },
      createEl('div', { class: 'body' },
        createEl('div', { class: 'hint' }, `Error loading mental model: ${e.message}`),
        createEl('div', { class: 'hint' }, 'If opening from file://, use a local server to enable fetch()')
      )));
    return;
  }

  const items = parseMentalModel(md);
  if (!items.length) {
    app.appendChild(createEl('div', { class: 'hint' }, 'No features found in mental_model.md'));
    return;
  }

  for (const { feature, waveFiles } of items) {
    const card = createEl('section', { class: 'feature' });
    const head = createEl('header');
    head.appendChild(createEl('h2', {}, feature));
    head.appendChild(createEl('small', {}, `${waveFiles.length} waveform${waveFiles.length>1?'s':''}`));
    const body = createEl('div', { class: 'body' });

    for (const wf of waveFiles) {
      const waveCard = createEl('div', { class: 'wave-card' });
      const meta = createEl('div', { class: 'meta' },
        createEl('span', { class: 'pill' }, wf),
        createEl('span', { class: 'hint' }, '(clk, rst, en, count)')
      );
      waveCard.appendChild(meta);

      try {
        const txt = await loadText(WAVES_BASE + wf.split('/').pop());
        const parsed = parseWaveTxt(txt);
        renderWaveform(waveCard, parsed, { maxSamples, width: canvasWidth });
      } catch (e) {
        waveCard.appendChild(createEl('div', { class: 'hint' }, `Failed to load ${wf}: ${e.message}`));
      }

      body.appendChild(waveCard);
    }

    card.appendChild(head);
    card.appendChild(body);
    app.appendChild(card);
  }
}

function addCanvasInteraction(canvas, data, signalNames, canvasId) {
  const tooltip = document.getElementById('tooltip');
  const infoPanel = document.getElementById(`info_${canvasId}`);
  
  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Calculate time and signal from mouse position
    const paddingL = 70;
    const paddingT = 10;
    const trackH = 60;
    
    if (x < paddingL) return;
    
    const timeIndex = Math.floor((x - paddingL) / ((canvas.width - paddingL - 10) / data.time.length));
    const signalIndex = Math.floor((y - paddingT) / trackH);
    
    if (timeIndex >= 0 && timeIndex < data.time.length && 
        signalIndex >= 0 && signalIndex < signalNames.length) {
      
      const time = data.time[timeIndex];
      const signal = signalNames[signalIndex];
      const value = data.series[signal] ? data.series[signal][timeIndex] : 'N/A';
      
      // Show tooltip
      tooltip.style.display = 'block';
      tooltip.style.left = (e.clientX + 10) + 'px';
      tooltip.style.top = (e.clientY - 10) + 'px';
      tooltip.innerHTML = `
        <strong>Time:</strong> ${time}<br>
        <strong>Signal:</strong> ${signal}<br>
        <strong>Value:</strong> ${typeof value === 'number' ? 
          (/count/i.test(signal) ? `0x${value.toString(16).padStart(2, '0')} (${value})` : value) : value}
      `;
      
      // Update info panel
      if (infoPanel) {
        updateSignalInfo(infoPanel, data, signalNames, timeIndex);
      }
      
      globalState.hoveredTime = timeIndex;
      globalState.hoveredSignal = signalIndex;
    }
  });
  
  canvas.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
    globalState.hoveredTime = null;
    globalState.hoveredSignal = null;
  });
}

function updateSignalInfo(infoPanel, data, signalNames, timeIndex) {
  infoPanel.innerHTML = '';
  const time = data.time[timeIndex];
  
  const timeRow = createEl('div', { class: 'signal-row' });
  timeRow.appendChild(createEl('span', { class: 'signal-name', text: 'Time:' }));
  timeRow.appendChild(createEl('span', { class: 'signal-value', text: String(time) }));
  infoPanel.appendChild(timeRow);
  
  for (const signal of signalNames) {
    const value = data.series[signal] ? data.series[signal][timeIndex] : 'N/A';
    const row = createEl('div', { class: 'signal-row' });
    row.appendChild(createEl('span', { class: 'signal-name', text: signal + ':' }));
    
    let displayValue = value;
    if (typeof value === 'number' && /count/i.test(signal)) {
      displayValue = `0x${value.toString(16).padStart(2, '0')} (${value})`;
    }
    
    row.appendChild(createEl('span', { class: 'signal-value', text: String(displayValue) }));
    infoPanel.appendChild(row);
  }
}

// File loading functionality
function loadWaveFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const parsed = parseWaveTxt(text);
        globalState.loadedFiles.set(file.name, parsed);
        resolve(parsed);
      } catch (error) {
        reject(error);
      }
    };
    reader.onerror = () => reject(new Error('Failed to read file'));
    reader.readAsText(file);
  });
}

async function renderLoadedFile() {
  const fileInput = document.getElementById('waveFileInput');
  const app = document.getElementById('app');
  
  if (!fileInput.files.length) {
    alert('Please select a waveform file first');
    return;
  }
  
  const file = fileInput.files[0];
  
  try {
    app.innerHTML = '<div class="status loading">Loading waveform...</div>';
    
    const data = await loadWaveFile(file);
    
    app.innerHTML = '';
    const card = createEl('section', { class: 'feature' });
    const head = createEl('header');
    head.appendChild(createEl('h2', {}, `Loaded: ${file.name}`));
    head.appendChild(createEl('small', {}, `${data.time.length} time samples`));
    
    const body = createEl('div', { class: 'body' });
    const waveCard = createEl('div', { class: 'wave-card' });
    
    const maxSamples = parseInt(document.getElementById('maxSamples').value, 10) || 160;
    const canvasWidth = parseInt(document.getElementById('canvasWidth').value, 10) || 1000;
    
    renderWaveform(waveCard, data, { maxSamples, width: canvasWidth });
    
    // Add WaveJSON export
    const waveJSONCard = createEl('div', { class: 'wave-card' });
    const waveJSONMeta = createEl('div', { class: 'meta' },
      createEl('span', { class: 'pill', text: 'WaveJSON Export' }),
      createEl('span', { class: 'hint', text: 'Standardized waveform format' })
    );
    waveJSONCard.appendChild(waveJSONMeta);
    
    try {
      // Read file content for WaveJSON conversion
      const fileContent = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result);
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
      });
      
      const waveJSON = WaveformConverter.txtToWaveJSON(fileContent, file.name);
      
      const jsonContainer = createEl('div', { class: 'signal-info' });
      const jsonPre = createEl('pre', { 
        style: 'white-space: pre-wrap; font-size: 11px; max-height: 300px; overflow-y: auto;',
        text: JSON.stringify(waveJSON, null, 2)
      });
      jsonContainer.appendChild(jsonPre);
      
      const downloadBtn = createEl('button', { 
        text: 'Download WaveJSON',
        style: 'margin-top: 8px; padding: 4px 8px; font-size: 11px;'
      });
      downloadBtn.addEventListener('click', () => {
        const blob = new Blob([JSON.stringify(waveJSON, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = createEl('a', { href: url, download: file.name.replace('.txt', '.json') });
        a.click();
        URL.revokeObjectURL(url);
      });
      
      waveJSONCard.appendChild(jsonContainer);
      waveJSONCard.appendChild(downloadBtn);
      
    } catch (error) {
      waveJSONCard.appendChild(createEl('div', { class: 'hint', text: `WaveJSON conversion error: ${error.message}` }));
    }
    
    body.appendChild(waveCard);
    body.appendChild(waveJSONCard);
    card.appendChild(head);
    card.appendChild(body);
    app.appendChild(card);
    
  } catch (error) {
    app.innerHTML = `<div class="status error">Error loading file: ${error.message}</div>`;
  }
}

// Event listeners
document.getElementById('reloadBtn').addEventListener('click', render);
document.getElementById('loadFileBtn').addEventListener('click', renderLoadedFile);

// Initial render
render();

