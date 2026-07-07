import argparse
import json
from pathlib import Path
from urllib.request import urlopen

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"


def parse_grades(grades_path: Path):
    rows = []
    with grades_path.open("r", encoding="utf-8") as handle:
        in_table = False
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if not in_table:
                if line.strip().startswith("POS"):
                    in_table = True
                continue

            if not line.strip():
                continue
            if line.lstrip().startswith("*"):
                break

            parts = line.split()
            if len(parts) < 4:
                continue
            if not parts[0].isdigit():
                continue

            pos = int(parts[0])
            aa = parts[1]
            score = float(parts[2])
            color_raw = parts[3]
            grade = int(color_raw.replace("*", ""))
            low_conf = "*" in color_raw
            rows.append(
                {
                    "pos": pos,
                    "aa": aa,
                    "score": score,
                    "grade": grade,
                    "low_conf": low_conf,
                }
            )

    if not rows:
        raise ValueError(f"No rows parsed from {grades_path}")

    rows.sort(key=lambda r: r["pos"])
    return rows


def make_plotly_script(embed_plotly: bool):
    if not embed_plotly:
        return f'<script src="{PLOTLY_CDN}"></script>'

    with urlopen(PLOTLY_CDN, timeout=30) as response:
        plotly_js = response.read().decode("utf-8")
    return f"<script>{plotly_js}</script>"


def gather_data(project_root: Path):
    cfg = {
        "RAD21": {
            "Full": project_root / "ConSurf/output/RAD21/rad21_consurf_full/Human_RAD21_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/RAD21/rad21_consurf_vertebrates/Human_RAD21_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/RAD21/rad21_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
        },
        "STAG1": {
            "Full": project_root / "ConSurf/output/STAG1/stag1_consurf_full/Human_STAG1_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/STAG1/stag1_consurf_vertebrates/Human_STAG1_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/STAG1/stag1_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
        },
        "STAG2": {
            "Full": project_root / "ConSurf/output/STAG2/stag2_consurf_full/Human_STAG2_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/STAG2/stag2_consurf_vertebrates/Human_STAG2_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/STAG2/stag2_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
        },
        "CTCF": {
            "Full": project_root / "ConSurf/output/ctcf_consurf_run/Human_CTCF_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/ctcf_consurf_vertebrates/Human_CTCF_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/ctcf_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
        },
    }

    payload = {}
    for protein, datasets in cfg.items():
        payload[protein] = {}
        for dataset_name, path in datasets.items():
            if not path.exists():
                raise FileNotFoundError(f"Missing expected grades file: {path}")
            payload[protein][dataset_name] = parse_grades(path)
    return payload


def build_html(payload, plotly_script_tag: str):
    datasets_json = json.dumps(payload)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>ConSurf Interactive Viewer</title>
  {plotly_script_tag}
  <style>
    body {{
      font-family: Segoe UI, Arial, sans-serif;
      margin: 0;
      background: #f7f9fc;
      color: #1f2937;
    }}
    .wrap {{
      max-width: 1280px;
      margin: 20px auto;
      padding: 0 16px;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 12px;
    }}
    .tab {{
      border: 1px solid #cbd5e1;
      background: #fff;
      border-radius: 8px;
      padding: 7px 12px;
      cursor: pointer;
      font-weight: 600;
      color: #334155;
    }}
    .tab.active {{
      background: #1d4ed8;
      border-color: #1d4ed8;
      color: white;
    }}
    .toolbar {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 10px;
    }}
    select, input, button {{
      font-size: 14px;
      padding: 6px 10px;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      background: #fff;
    }}
    button {{
      cursor: pointer;
      background: #eef2ff;
      border-color: #c7d2fe;
    }}
    button:hover {{
      background: #e0e7ff;
    }}
    .hint {{
      font-size: 13px;
      color: #475569;
    }}
    .status {{
      font-size: 12px;
      color: #334155;
      min-height: 18px;
      margin-bottom: 8px;
    }}
    .panel {{
      display: grid;
      grid-template-columns: 1fr 330px;
      gap: 12px;
    }}
    #plot {{
      width: 100%;
      height: 740px;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
    }}
    .highlights {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      padding: 10px;
      max-height: 740px;
      overflow: auto;
    }}
    .highlights h3 {{
      margin: 2px 0 8px 0;
      font-size: 15px;
    }}
    .highlights ul {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .highlights li {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 6px 8px;
      font-size: 12px;
      background: #f8fafc;
    }}
    .chip {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
      display: inline-block;
      margin-right: 6px;
      border: 1px solid #94a3b8;
    }}
    .empty {{
      color: #64748b;
      font-size: 12px;
    }}
    @media (max-width: 1000px) {{
      .panel {{
        grid-template-columns: 1fr;
      }}
      .highlights {{
        max-height: none;
      }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h2>ConSurf Interactive Viewer</h2>
    <div class=\"tabs\" id=\"protein-tabs\"></div>

    <div class=\"toolbar\">
      <label for=\"dataset\">Dataset:</label>
      <select id=\"dataset\"></select>
      <div class=\"hint\">Hover points for exact residue number, amino acid, score, and grade.</div>
    </div>

    <div class=\"toolbar\">
      <input id=\"hl-label\" type=\"text\" placeholder=\"Label\" value=\"Region\" />
      <input id=\"hl-color\" type=\"color\" value=\"#f59e0b\" />
      <button id=\"hl-pick\" type=\"button\">Pick from plot</button>
      <button id=\"hl-clear\" type=\"button\">Clear all</button>
    </div>

    <div class=\"status\" id=\"status\"></div>

    <div class=\"panel\">
      <div id=\"plot\"></div>
      <div class=\"highlights\">
        <h3>Highlights</h3>
        <ul id=\"highlight-list\"></ul>
      </div>
    </div>
  </div>

  <script>
    const proteinDatasets = {datasets_json};

    const proteinTabs = document.getElementById('protein-tabs');
    const datasetSelect = document.getElementById('dataset');
    const plotEl = document.getElementById('plot');
    const listEl = document.getElementById('highlight-list');
    const statusEl = document.getElementById('status');
    const pickBtn = document.getElementById('hl-pick');
    const clearBtn = document.getElementById('hl-clear');
    const labelInput = document.getElementById('hl-label');
    const colorInput = document.getElementById('hl-color');

    const proteins = Object.keys(proteinDatasets);
    let currentProtein = proteins[0];
    let currentDataset = Object.keys(proteinDatasets[currentProtein])[0];

    const highlights = {{}};
    proteins.forEach((protein) => {{
      highlights[protein] = {{}};
      Object.keys(proteinDatasets[protein]).forEach((dataset) => {{
        highlights[protein][dataset] = [];
      }});
    }});

    let pickMode = false;
    let pickStart = null;

    function setStatus(message) {{
      statusEl.textContent = message;
    }}

    function makeHighlightId() {{
      return `hl_${{Date.now()}}_${{Math.floor(Math.random() * 10000)}}`;
    }}

    function normalizeRange(a, b) {{
      return [Math.min(a, b), Math.max(a, b)];
    }}

    function renderTabs() {{
      proteinTabs.innerHTML = '';
      proteins.forEach((protein) => {{
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'tab' + (protein === currentProtein ? ' active' : '');
        btn.textContent = protein;
        btn.addEventListener('click', () => {{
          currentProtein = protein;
          currentDataset = Object.keys(proteinDatasets[currentProtein])[0];
          renderAll();
        }});
        proteinTabs.appendChild(btn);
      }});
    }}

    function renderDatasetSelect() {{
      datasetSelect.innerHTML = '';
      Object.keys(proteinDatasets[currentProtein]).forEach((dataset) => {{
        const opt = document.createElement('option');
        opt.value = dataset;
        opt.textContent = dataset;
        datasetSelect.appendChild(opt);
      }});
      datasetSelect.value = currentDataset;
    }}

    function renderHighlightList() {{
      const rows = highlights[currentProtein][currentDataset];
      listEl.innerHTML = '';
      if (!rows.length) {{
        const empty = document.createElement('div');
        empty.className = 'empty';
        empty.textContent = 'No highlights yet.';
        listEl.appendChild(empty);
        return;
      }}

      rows.forEach((row) => {{
        const li = document.createElement('li');
        const left = document.createElement('div');

        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.style.background = row.color;
        left.appendChild(chip);

        const text = document.createElement('span');
        text.textContent = `${{row.label}}: ${{row.start}}-${{row.end}}`;
        left.appendChild(text);

        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = 'Delete';
        del.addEventListener('click', () => {{
          highlights[currentProtein][currentDataset] = highlights[currentProtein][currentDataset].filter((r) => r.id !== row.id);
          renderPlot();
          setStatus(`Removed highlight ${{row.start}}-${{row.end}}`);
        }});

        li.appendChild(left);
        li.appendChild(del);
        listEl.appendChild(li);
      }});
    }}

    function buildHighlightShapes() {{
      return highlights[currentProtein][currentDataset].map((row) => ({{
        type: 'rect',
        xref: 'x',
        yref: 'paper',
        x0: row.start - 0.5,
        x1: row.end + 0.5,
        y0: 0,
        y1: 1,
        fillcolor: row.color,
        opacity: 0.18,
        line: {{ width: 1, color: row.color }},
        layer: 'below'
      }}));
    }}

    function addHighlight(start, end, label, color) {{
      const [s, e] = normalizeRange(start, end);
      highlights[currentProtein][currentDataset].push({{
        id: makeHighlightId(),
        start: s,
        end: e,
        label: label || `Region ${{highlights[currentProtein][currentDataset].length + 1}}`,
        color: color || '#f59e0b'
      }});
      renderPlot();
      setStatus(`Added highlight ${{s}}-${{e}}`);
    }}

    function renderPlot() {{
      const data = proteinDatasets[currentProtein][currentDataset];
      const x = data.map((r) => r.pos);
      const score = data.map((r) => r.score);
      const grade = data.map((r) => r.grade);
      const custom = data.map((r) => [r.aa, r.grade, r.low_conf ? 'yes' : 'no', r.score]);

      const scoreTrace = {{
        x: x,
        y: score,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Normalized score',
        line: {{ color: '#1d4ed8', width: 1.8 }},
        marker: {{ size: 5, color: '#1d4ed8' }},
        customdata: custom,
        hovertemplate:
          'Residue: %{{x}}<br>' +
          'AA: %{{customdata[0]}}<br>' +
          'Score: %{{y:.4f}}<br>' +
          'Grade: %{{customdata[1]}}<br>' +
          'Low confidence: %{{customdata[2]}}<extra></extra>',
        yaxis: 'y'
      }};

      const gradeTrace = {{
        x: x,
        y: grade,
        type: 'scatter',
        mode: 'markers',
        name: 'ConSurf grade',
        marker: {{
          size: 7,
          color: grade,
          colorscale: 'Viridis',
          cmin: 1,
          cmax: 9,
          opacity: 0.85,
          colorbar: {{ title: 'Grade' }}
        }},
        customdata: custom,
        hovertemplate:
          'Residue: %{{x}}<br>' +
          'AA: %{{customdata[0]}}<br>' +
          'Grade: %{{y}}<br>' +
          'Score: %{{customdata[3]:.4f}}<br>' +
          'Low confidence: %{{customdata[2]}}<extra></extra>',
        yaxis: 'y2'
      }};

      const layout = {{
        title: `${{currentProtein}} - ${{currentDataset}}`,
        margin: {{ l: 65, r: 65, t: 55, b: 55 }},
        hovermode: 'x unified',
        xaxis: {{ title: 'Residue position' }},
        yaxis: {{
          title: 'Normalized score',
          zeroline: true,
          zerolinecolor: '#94a3b8',
          domain: [0.35, 1.0]
        }},
        yaxis2: {{
          title: 'ConSurf grade',
          domain: [0.0, 0.24],
          range: [0.5, 9.5],
          tickvals: [1,2,3,4,5,6,7,8,9]
        }},
        shapes: buildHighlightShapes(),
        legend: {{ orientation: 'h' }}
      }};

      Plotly.newPlot(plotEl, [scoreTrace, gradeTrace], layout, {{ responsive: true }});

      if (typeof plotEl.removeAllListeners === 'function') {{
        plotEl.removeAllListeners('plotly_click');
      }}
      plotEl.on('plotly_click', (ev) => {{
        if (!pickMode) return;
        const xVal = ev?.points?.[0]?.x;
        if (!Number.isFinite(xVal)) return;
        const residue = Math.round(xVal);
        if (pickStart === null) {{
          pickStart = residue;
          setStatus(`Pick mode: start set to ${{residue}}. Click an end residue.`);
        }} else {{
          addHighlight(pickStart, residue, labelInput.value.trim(), colorInput.value);
          pickStart = null;
          pickMode = false;
          pickBtn.textContent = 'Pick from plot';
        }}
      }});

      renderHighlightList();
      if (!pickMode) {{
        setStatus('Click Pick from plot, then click two residues to create a highlight.');
      }}
    }}

    pickBtn.addEventListener('click', () => {{
      pickMode = !pickMode;
      pickStart = null;
      if (pickMode) {{
        setStatus('Pick mode: click first residue, then second residue.');
        pickBtn.textContent = 'Cancel pick';
      }} else {{
        setStatus('Pick mode cancelled.');
        pickBtn.textContent = 'Pick from plot';
      }}
    }});

    clearBtn.addEventListener('click', () => {{
      highlights[currentProtein][currentDataset] = [];
      renderPlot();
      setStatus('Cleared highlights for current selection.');
    }});

    datasetSelect.addEventListener('change', () => {{
      currentDataset = datasetSelect.value;
      renderPlot();
    }});

    function renderAll() {{
      renderTabs();
      renderDatasetSelect();
      renderPlot();
    }}

    renderAll();
  </script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Build multi-protein ConSurf viewer site")
    parser.add_argument("--output", type=Path, default=Path("index.html"), help="Output HTML path")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to alignment_work project root (default: parent of this script dir)",
    )
    parser.add_argument(
        "--cdn",
        action="store_true",
        help="Use Plotly from CDN instead of embedding JS",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    project_root = args.project_root.resolve() if args.project_root else script_dir.parent.resolve()

    payload = gather_data(project_root)
    plotly_script_tag = make_plotly_script(embed_plotly=not args.cdn)
    html = build_html(payload, plotly_script_tag)

    out_path = args.output if args.output.is_absolute() else script_dir / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    mode = "cdn" if args.cdn else "standalone"
    print(f"Wrote {mode} site: {out_path}")


if __name__ == "__main__":
    main()
