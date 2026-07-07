import argparse
import json
from pathlib import Path
from urllib.request import urlopen

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"


def read_fasta(path: Path):
    records = []
    header = None
    buf = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(buf)))
            header = line[1:].strip()
            buf = []
        else:
            if header is None:
                raise ValueError(f"Invalid FASTA: {path}")
            buf.append(line)
    if header is not None:
        records.append((header, "".join(buf)))
    return records


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


def query_name_from_grades_path(grades_path: Path):
    return grades_path.stem.removesuffix("_consurf")


def parse_msa_for_viewer(msa_path: Path, query_name: str):
    records = read_fasta(msa_path)
    if not records:
        return None

    query_seq = None
    for header, seq in records:
        if header == query_name:
            query_seq = seq
            break

    if query_seq is None:
        return None

    pos_to_col = {}
    query_pos = 0
    for col_idx, aa in enumerate(query_seq):
        if aa != "-":
            query_pos += 1
            pos_to_col[query_pos] = col_idx

    return {
        "query_name": query_name,
        "aligned_length": len(query_seq),
        "pos_to_col": pos_to_col,
        "records": [{"name": header, "seq": seq} for header, seq in records],
    }


def make_plotly_script(embed_plotly: bool):
    if not embed_plotly:
        return f'<script src="{PLOTLY_CDN}"></script>'

    with urlopen(PLOTLY_CDN, timeout=30) as response:
        plotly_js = response.read().decode("utf-8")
    return f"<script>{plotly_js}</script>"


def compute_human_mapping_from_source(source_path: Path, source_query_key: str):
    records = read_fasta(source_path)
    human_seq = None
    query_seq = None
    for header, seq in records:
        lower = header.lower()
        if human_seq is None and ("homo_sapiens" in lower or "human" in lower):
            human_seq = seq
        if query_seq is None and source_query_key.lower() in lower:
            query_seq = seq

    if human_seq is None or query_seq is None:
        return None
    if len(human_seq) != len(query_seq):
        return None

    human_index = 0
    mapping = []
    for human_char, query_char in zip(human_seq, query_seq):
        if human_char != "-":
            human_index += 1
        if query_char != "-":
            if human_char != "-":
                mapping.append(
                    {
                        "present": 1,
                        "aa": human_char,
                        "count": human_index,
                    }
                )
            else:
                mapping.append(
                    {
                        "present": None,
                        "aa": None,
                        "count": None,
                    }
                )
    return mapping


def gather_data(project_root: Path):
    cfg = {
        "RAD21": {
            "Full": project_root / "ConSurf/output/RAD21/rad21_consurf_full/Human_RAD21_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/RAD21/rad21_consurf_vertebrates/Human_RAD21_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/RAD21/rad21_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
            "_source": project_root / "ConSurf/output/RAD21/updated_RAD21alignment_0625.fas",
            "_source_query": "Ciona_intestinalis",
        },
        "STAG1": {
            "Full": project_root / "ConSurf/output/STAG1/stag1_consurf_full/Human_STAG1_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/STAG1/stag1_consurf_vertebrates/Human_STAG1_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/STAG1/stag1_consurf_invertebrates/Branchiostoma_lanceolatum_consurf.grades",
            "_source": Path(r"C:/Users/Nat/Downloads/Bioinformatics/updated_STAG1alignment_0612.fas"),
            "_source_query": "Branchiostoma_lanceolatum",
        },
        "STAG2": {
            "Full": project_root / "ConSurf/output/STAG2/stag2_consurf_full/Human_STAG2_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/STAG2/stag2_consurf_vertebrates/Human_STAG2_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/STAG2/stag2_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
            "_source": project_root / "alignments_out/STAG2/01_STAG2_aligned.fasta",
            "_source_query": "Ciona_intestinalis",
        },
        "CTCF": {
            "Full": project_root / "ConSurf/output/CTCF/ctcf_consurf_run/Human_CTCF_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/CTCF/ctcf_consurf_vertebrates/Human_CTCF_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/CTCF/ctcf_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
            "_source": project_root / "alignments_out/CTCF/01_CTCF_aligned.fasta",
            "_source_query": "Ciona_intestinalis",
        },
        "WAPL": {
            "Full": project_root / "ConSurf/output/WAPL/wapl_consurf_full/Human_WAPL_consurf.grades",
            "Vertebrates": project_root / "ConSurf/output/WAPL/wapl_consurf_vertebrates/Human_WAPL_consurf.grades",
            "Invertebrates": project_root / "ConSurf/output/WAPL/wapl_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
            "_source": project_root / "ConSurf/output/WAPL/WAPLalignment_0708.fas",
            "_source_query": "Ciona_intestinalis",
        },
        "SMC1": {
          "Full": project_root / "ConSurf/output/SMC1/smc1_consurf_full/Human_SMC1_consurf.grades",
          "Vertebrates": project_root / "ConSurf/output/SMC1/smc1_consurf_vertebrates/Human_SMC1_consurf.grades",
          "Invertebrates": project_root / "ConSurf/output/SMC1/smc1_consurf_invertebrates/Ciona_intestinalis_consurf.grades",
          "_source": project_root / "ConSurf/output/SMC1/SMC1_0708.fas",
          "_source_query": "Ciona_intestinalis",
        },
    }

    payload = {}
    for protein, datasets in cfg.items():
        payload[protein] = {}
        source_path = datasets.get("_source")
        source_query_key = datasets.get("_source_query")
        invertebrate_mapping = None
        if source_path:
            if not source_path.exists():
                raise FileNotFoundError(f"Missing expected source alignment: {source_path}")
            if source_query_key:
                invertebrate_mapping = compute_human_mapping_from_source(source_path, source_query_key)

        for dataset_name, path in datasets.items():
            if dataset_name.startswith("_"):
                continue
            if not path.exists():
                raise FileNotFoundError(f"Missing expected grades file: {path}")
            rows = parse_grades(path)
            query_name = query_name_from_grades_path(path)
            msa_path = path.with_name(f"{query_name}_msa_file.fas")
            msa_data = None
            if msa_path.exists():
                msa_data = parse_msa_for_viewer(msa_path, query_name)
            human_presence = None
            if dataset_name == "Full":
                human_presence = [
                    {"present": 1, "aa": row["aa"], "count": row["pos"]}
                    for row in rows
                ]
            elif dataset_name == "Invertebrates" and invertebrate_mapping is not None:
                if len(invertebrate_mapping) == len(rows):
                    human_presence = invertebrate_mapping

            payload[protein][dataset_name] = {
                "rows": rows,
                "human_presence": human_presence,
                "msa": msa_data,
            }
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
      width: min(98vw, 2200px);
      max-width: 2200px;
      margin: 12px auto;
      padding: 0 12px;
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
      grid-template-columns: minmax(0, 1fr) 280px;
      gap: 12px;
    }}
    #plot {{
      width: 100%;
      height: 82vh;
      min-height: 740px;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
    }}
    .highlights {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      background: #fff;
      padding: 10px;
      max-height: 82vh;
      min-height: 740px;
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
      cursor: pointer;
    }}
    .highlights li.selected {{
      border-color: #2563eb;
      background: #dbeafe;
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
    .msa-box {{
      margin-top: 12px;
      border-top: 1px solid #e2e8f0;
      padding-top: 10px;
    }}
    .msa-box h4 {{
      margin: 0 0 8px 0;
      font-size: 14px;
    }}
    .msa-meta {{
      font-size: 12px;
      color: #475569;
      margin-bottom: 8px;
    }}
    .msa-pre {{
      font-family: Consolas, "Courier New", monospace;
      font-size: 11px;
      line-height: 1.35;
      white-space: pre;
      overflow: auto;
      max-height: 360px;
      background: #0f172a;
      color: #e2e8f0;
      border-radius: 8px;
      padding: 10px;
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


    <div class="toolbar">
      <input id="seq-query" type="text" placeholder="Find motif in current reference sequence (e.g. FGF)" />
      <button id="seq-find" type="button">Find sequence</button>
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
        <div class="msa-box">
          <h4>MSA slice</h4>
          <div class="msa-meta" id="msa-meta">Select or create a highlight to view the aligned region.</div>
          <pre class="msa-pre" id="msa-view"></pre>
        </div>
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
    const msaMetaEl = document.getElementById('msa-meta');
    const msaViewEl = document.getElementById('msa-view');
    const pickBtn = document.getElementById('hl-pick');
    const clearBtn = document.getElementById('hl-clear');
    const findBtn = document.getElementById('seq-find');
    const labelInput = document.getElementById('hl-label');
    const colorInput = document.getElementById('hl-color');
    const seqQueryInput = document.getElementById('seq-query');

    const proteins = Object.keys(proteinDatasets);
    let currentProtein = proteins[0];
    let currentDataset = Object.keys(proteinDatasets[currentProtein])[0];
    let selectedHighlightId = null;

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

    function removeSearchHighlights() {{
      highlights[currentProtein][currentDataset] = highlights[currentProtein][currentDataset].filter((row) => !row.isSearch);
    }}

    function getCurrentHighlights() {{
      return highlights[currentProtein][currentDataset];
    }}

    function getSelectedHighlight() {{
      return getCurrentHighlights().find((row) => row.id === selectedHighlightId) || null;
    }}

    function setSelectedHighlight(id) {{
      selectedHighlightId = id;
      renderHighlightList();
      renderMsaSlice();
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
      const rows = getCurrentHighlights();
      listEl.innerHTML = '';
      if (!rows.length) {{
        const empty = document.createElement('div');
        empty.className = 'empty';
        empty.textContent = 'No highlights yet.';
        listEl.appendChild(empty);
        selectedHighlightId = null;
        renderMsaSlice();
        return;
      }}

      if (!rows.some((row) => row.id === selectedHighlightId)) {{
        selectedHighlightId = rows[rows.length - 1].id;
      }}

      rows.forEach((row) => {{
        const li = document.createElement('li');
        if (row.id === selectedHighlightId) {{
          li.classList.add('selected');
        }}
        li.addEventListener('click', () => setSelectedHighlight(row.id));
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
        del.addEventListener('click', (ev) => {{
          ev.stopPropagation();
          highlights[currentProtein][currentDataset] = highlights[currentProtein][currentDataset].filter((r) => r.id !== row.id);
          renderPlot();
          setStatus(`Removed highlight ${{row.start}}-${{row.end}}`);
        }});

        li.appendChild(left);
        li.appendChild(del);
        listEl.appendChild(li);
      }});
      renderMsaSlice();
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
        color: color || '#f59e0b',
        isSearch: false
      }});
      selectedHighlightId = highlights[currentProtein][currentDataset][highlights[currentProtein][currentDataset].length - 1].id;
      renderPlot();
      setStatus(`Added highlight ${{s}}-${{e}}`);
    }}

    function addSearchHighlights(query) {{
      const datasetObj = proteinDatasets[currentProtein][currentDataset];
      const rows = datasetObj.rows;
      const motif = query.trim().toUpperCase();
      if (!motif) {{
        setStatus('Enter a sequence motif to search.');
        return;
      }}

      const sequence = rows.map((r) => r.aa).join('');
      const matches = [];
      let start = 0;
      while (true) {{
        const idx = sequence.indexOf(motif, start);
        if (idx === -1) break;
        matches.push([rows[idx].pos, rows[idx + motif.length - 1].pos]);
        start = idx + 1;
      }}

      removeSearchHighlights();
      if (!matches.length) {{
        renderPlot();
        setStatus(`No matches found for ${{motif}}.`);
        return;
      }}

      matches.forEach(([s, e], i) => {{
        highlights[currentProtein][currentDataset].push({{
          id: makeHighlightId(),
          start: s,
          end: e,
          label: `${{motif}} #${{i + 1}}`,
          color: '#ef4444',
          isSearch: true
        }});
      }});
      if (highlights[currentProtein][currentDataset].length) {{
        selectedHighlightId = highlights[currentProtein][currentDataset][highlights[currentProtein][currentDataset].length - matches.length].id;
      }}
      renderPlot();
      setStatus(`Found ${{matches.length}} match(es) for ${{motif}}.`);
    }}

    function renderMsaSlice() {{
      const datasetObj = proteinDatasets[currentProtein][currentDataset];
      const msa = datasetObj.msa;
      const hl = getSelectedHighlight();
      if (!hl) {{
        msaMetaEl.textContent = 'Select or create a highlight to view the aligned region.';
        msaViewEl.textContent = '';
        return;
      }}
      if (!msa || !msa.pos_to_col) {{
        msaMetaEl.textContent = `MSA slice unavailable for ${{hl.label}}.`;
        msaViewEl.textContent = '';
        return;
      }}

      const startCol = msa.pos_to_col[String(hl.start)] ?? msa.pos_to_col[hl.start];
      const endCol = msa.pos_to_col[String(hl.end)] ?? msa.pos_to_col[hl.end];
      if (startCol === undefined || endCol === undefined) {{
        msaMetaEl.textContent = `Could not map ${{hl.start}}-${{hl.end}} onto the aligned MSA.`;
        msaViewEl.textContent = '';
        return;
      }}

      const flank = 5;
      const fromCol = Math.max(0, Math.min(startCol, endCol) - flank);
      const toCol = Math.min(msa.aligned_length - 1, Math.max(startCol, endCol) + flank);
      const width = Math.max(...msa.records.map((r) => r.name.length), 12);
      const lines = msa.records.map((r) => `${{r.name.padEnd(width)}}  ${{r.seq.slice(fromCol, toCol + 1)}}`);
      msaMetaEl.textContent = `${{hl.label}} | query residues ${{hl.start}}-${{hl.end}} | aligned columns ${{fromCol + 1}}-${{toCol + 1}}`;
      msaViewEl.textContent = lines.join('\n');
    }}

    function renderPlot() {{
      const datasetObj = proteinDatasets[currentProtein][currentDataset];
      const data = datasetObj.rows;
      const x = data.map((r) => r.pos);
      const score = data.map((r) => r.score);
      const grade = data.map((r) => r.grade);
      const custom = data.map((r) => [r.aa, r.grade, r.low_conf ? 'yes' : 'no', r.score]);
      const humanPresence = datasetObj.human_presence || null;
      const showHumanTrack =
        (currentDataset === 'Full' || currentDataset === 'Invertebrates') &&
        Array.isArray(humanPresence) &&
        humanPresence.length === x.length;
      const humanPresenceY = showHumanTrack ? humanPresence.map((r) => r.present) : null;
      const humanPresenceCustom = showHumanTrack
        ? humanPresence.map((r) => [r.aa, r.count])
        : null;

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

      const humanPresenceTrace = {{
        x: x,
        y: humanPresenceY,
        type: 'scatter',
        mode: 'lines',
        name: 'Human sequence present',
        line: {{ color: '#059669', width: 6, shape: 'hv' }},
        customdata: humanPresenceCustom,
        hovertemplate:
          'Residue: %{{x}}<br>' +
          'Human sequence present here: yes<br>' +
          'Human residue: %{{customdata[0]}}<br>' +
          'Human residue number: %{{customdata[1]}}<extra></extra>',
        yaxis: 'y3'
      }};

      const traces = showHumanTrack ? [scoreTrace, gradeTrace, humanPresenceTrace] : [scoreTrace, gradeTrace];

      const layout = {{
        title: `${{currentProtein}} - ${{currentDataset}}`,
        margin: {{ l: 65, r: 65, t: 55, b: 55 }},
        hovermode: 'x unified',
        xaxis: {{ title: 'Residue position' }},
        yaxis: {{
          title: 'Normalized score',
          zeroline: true,
          zerolinecolor: '#94a3b8',
          domain: showHumanTrack ? [0.46, 1.0] : [0.35, 1.0]
        }},
        yaxis2: {{
          title: 'ConSurf grade',
          domain: showHumanTrack ? [0.16, 0.32] : [0.0, 0.24],
          range: [0.5, 9.5],
          tickvals: [1,2,3,4,5,6,7,8,9]
        }},
        yaxis3: {{
          title: 'Human present',
          domain: showHumanTrack ? [0.0, 0.07] : [0.0, 0.0],
          range: [0, 1.2],
          tickvals: [1],
          ticktext: ['yes'],
          visible: showHumanTrack,
          showgrid: false,
          zeroline: false
        }},
        shapes: buildHighlightShapes(),
        legend: {{ orientation: 'h' }}
      }};

      Plotly.newPlot(plotEl, traces, layout, {{ responsive: true }});

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
        if ((currentDataset === 'Full' || currentDataset === 'Invertebrates') && !showHumanTrack) {{
          setStatus('Click Pick from plot, then click two residues to create a highlight. Human-presence track unavailable for this dataset.');
        }} else {{
          setStatus('Click Pick from plot, then click two residues to create a highlight.');
        }}
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
      selectedHighlightId = null;
      renderPlot();
      setStatus('Cleared highlights for current selection.');
    }});

    findBtn.addEventListener('click', () => {{
      addSearchHighlights(seqQueryInput.value);
    }});

    seqQueryInput.addEventListener('keydown', (ev) => {{
      if (ev.key === 'Enter') {{
        addSearchHighlights(seqQueryInput.value);
      }}
    }});

    datasetSelect.addEventListener('change', () => {{
      currentDataset = datasetSelect.value;
      renderPlot();
    }});

    function renderAll() {{
      selectedHighlightId = null;
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
