#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hs2_aps_tool.py — Unpack / repack .aps archives (Hidden Stroke II / Sudden Strike 2)

Format "FZFF" (reverse-engineered and verified on lang.aps, 1562/1562 files):

    "FZFF" + u32 body_len
    body   : for each file, its data deflate-compressed in chunks of max
             16384 uncompressed bytes, zlib streams back to back
             (a 0-byte file has no stream)
    tail   : u32 comp_len, u32 count,  u32 20      + zlib(records)
             u32 comp_len, u32 1,      u32 nameslen + zlib(name table)
    record : u32 name_off, u32 8, u32 (index + streams_before), u32 size,
             u32 16384

Usage:
    python3 hs2_aps_tool.py                  -> opens the GUI in your browser
    python3 hs2_aps_tool.py list    ARCHIVE
    python3 hs2_aps_tool.py unpack  ARCHIVE [--only UNITS] [--out DIR] [--flat]
    python3 hs2_aps_tool.py pack    ARCHIVE --section UNITS --from DIR
                                    [--out FILE] [--delete-missing]

Stdlib only. Works on macOS and Windows (Python 3.8+).
"""

import argparse
import datetime
import io
import json
import os
import re
import shutil
import struct
import sys
import threading
import webbrowser
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

MAGIC = b"FZFF"
CHUNK = 16384
ENC = "cp1252"

SCRIPT_DIR = Path(__file__).resolve().parent
GAME_ROOT = SCRIPT_DIR.parent  # Tools/ lives at the game root


# ----------------------------------------------------------------------------
# APS archive library
# ----------------------------------------------------------------------------


class ApsError(Exception):
    pass


def _parse_directory(head8, tail, path):
    """Parse the FZFF directory (the compressed blocks after the body).
    head8 = the first 8 bytes, tail = everything after the body.
    Returns list of (name, size)."""
    body_len = struct.unpack("<I", head8[4:8])[0]
    if len(tail) < 24:
        raise ApsError("%s: truncated directory" % path)
    comp_len, count, rec_size = struct.unpack("<III", tail[:12])
    if rec_size != 20:
        raise ApsError("%s: unexpected record size %d" % (path, rec_size))
    recs = zlib.decompress(tail[12 : 12 + comp_len])
    p2 = 12 + comp_len
    comp2, _cnt2, names_len = struct.unpack("<III", tail[p2 : p2 + 12])
    names = zlib.decompress(tail[p2 + 12 : p2 + 12 + comp2])
    if len(names) != names_len:
        raise ApsError("%s: name table size mismatch" % path)

    entries = []
    for i in range(count):
        noff, _f2, _f3, size, _chunksz = struct.unpack(
            "<IIIII", recs[i * 20 : i * 20 + 20]
        )
        name = names[noff : names.index(b"\x00", noff)].decode(ENC)
        entries.append((name, size))
    del body_len
    return entries


def read_aps_index(path):
    """Cheap listing: (name, size) pairs WITHOUT decompressing any file data.
    Reads only the 8-byte header plus the directory at the end of the file,
    so it is instant even on multi-hundred-MB archives."""
    with open(path, "rb") as f:
        head8 = f.read(8)
        if head8[:4] != MAGIC:
            raise ApsError("%s: not an FZFF archive (header %r)" % (path, head8[:4]))
        body_len = struct.unpack("<I", head8[4:8])[0]
        f.seek(8 + body_len)
        tail = f.read()
    return _parse_directory(head8, tail, path)


def read_aps(path):
    """Return list of (name, bytes) in archive order."""
    data = Path(path).read_bytes()
    if data[:4] != MAGIC:
        raise ApsError("%s: not an FZFF archive (header %r)" % (path, data[:4]))
    body_len = struct.unpack("<I", data[4:8])[0]
    end = 8 + body_len
    if end > len(data):
        raise ApsError("%s: truncated body" % path)
    entries = _parse_directory(data[:8], data[end:], path)

    # body: sequential zlib streams, sized per directory
    out = []
    pos = 8
    for name, size in entries:
        got = bytearray()
        while len(got) < size:
            d = zlib.decompressobj()
            got += d.decompress(data[pos:end])
            pos += (end - pos) - len(d.unused_data)
        if len(got) != size:
            raise ApsError("%s: size mismatch for %s" % (path, name))
        out.append((name, bytes(got)))
    if pos != end:
        raise ApsError("%s: %d unread bytes in body" % (path, end - pos))
    return out


def write_aps(path, entries, level=6):
    """Write entries (list of (name, bytes)) as an FZFF archive."""
    body = bytearray()
    recs = bytearray()
    names = bytearray()
    stream_count = 0
    for i, (name, data) in enumerate(entries):
        noff = len(names)
        names += name.encode(ENC) + b"\x00"
        recs += struct.pack("<IIIII", noff, 8, i + stream_count, len(data), CHUNK)
        for off in range(0, len(data), CHUNK):
            body += zlib.compress(data[off : off + CHUNK], level)
            stream_count += 1

    crecs = zlib.compress(bytes(recs), level)
    cnames = zlib.compress(bytes(names), level)
    blob = (
        MAGIC
        + struct.pack("<I", len(body))
        + body
        + struct.pack("<III", len(crecs), len(entries), 20)
        + crecs
        + struct.pack("<III", len(cnames), 1, len(names))
        + cnames
    )
    Path(path).write_bytes(blob)


def verify_aps(path, expected_entries):
    """Re-read archive and compare against intended content. Returns error or None."""
    try:
        back = read_aps(path)
    except Exception as e:  # noqa: BLE001
        return "re-read failed: %s" % e
    if len(back) != len(expected_entries):
        return "entry count differs (%d vs %d)" % (len(back), len(expected_entries))
    for (na, da), (nb, db) in zip(expected_entries, back):
        if na != nb:
            return "name mismatch: %r vs %r" % (na, nb)
        if da != db:
            return "content mismatch for %s" % na
    return None


def timestamp():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def backup_file(path):
    path = Path(path)
    bak = path.with_name(path.name + ".bak-" + timestamp())
    shutil.copy2(path, bak)
    return bak


# ----------------------------------------------------------------------------
# High-level operations
# ----------------------------------------------------------------------------


def op_sections(archive):
    """Section summary from the directory only — no data decompression."""
    sections = {}
    for name, size in read_aps_index(archive):
        sec = name.split("\\")[0] if "\\" in name else "(root)"
        n, b = sections.get(sec, (0, 0))
        sections[sec] = (n + 1, b + size)
    return sections


def op_list(archive):
    entries = read_aps(archive)
    sections = {}
    for name, data in entries:
        sec = name.split("\\")[0] if "\\" in name else "(root)"
        n, b = sections.get(sec, (0, 0))
        sections[sec] = (n + 1, b + len(data))
    return entries, sections


def op_unpack(archive, only=None, out_dir=None, flat=False, progress=None):
    """Extract files. only='UNITS' filters on section. flat drops the folder."""
    tell = progress or (lambda m: None)
    tell("reading %s…" % Path(archive).name)
    entries = read_aps(archive)
    prefix = (only + "\\") if only else None
    out_dir = (
        Path(out_dir)
        if out_dir
        else Path(archive).parent / (Path(archive).stem + "_extracted")
    )
    total = sum(1 for n, _ in entries if not prefix or n.startswith(prefix))
    written = 0
    skipped = 0
    for name, data in entries:
        if prefix and not name.startswith(prefix):
            skipped += 1
            continue
        rel = name[len(prefix) :] if (prefix and flat) else name.replace("\\", os.sep)
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written += 1
        if written % 25 == 0:
            tell("writing files… %d / %d" % (written, total))
    return {"written": written, "skipped": skipped, "out_dir": str(out_dir)}


def op_pack(
    archive,
    section,
    src_dir,
    out=None,
    delete_missing=False,
    make_backup=True,
    progress=None,
):
    """Rebuild archive using `archive` as template: entries of `section` are
    replaced by the files found in src_dir (matched by file name). New files
    are added, missing ones kept (or dropped with delete_missing)."""
    tell = progress or (lambda m: None)
    tell("reading %s…" % Path(archive).name)
    entries = read_aps(archive)
    src_dir = Path(src_dir)
    if not src_dir.is_dir():
        raise ApsError("source folder not found: %s" % src_dir)
    prefix = section + "\\"

    disk = {}
    for f in sorted(src_dir.iterdir(), key=lambda p: p.name.lower()):
        if f.is_file() and not f.name.startswith("."):
            disk[f.name] = f.read_bytes()

    new_entries = []
    updated = kept = deleted = unchanged = 0
    seen = set()
    last_sec_idx = -1
    for name, data in entries:
        if name.startswith(prefix):
            key = name[len(prefix) :]
            if key in disk:
                seen.add(key)
                if disk[key] == data:
                    unchanged += 1
                else:
                    updated += 1
                new_entries.append((name, disk[key]))
            elif delete_missing:
                deleted += 1
                continue
            else:
                kept += 1
                new_entries.append((name, data))
            last_sec_idx = len(new_entries) - 1
        else:
            new_entries.append((name, data))

    added_names = sorted(set(disk) - seen, key=str.lower)
    for j, key in enumerate(added_names):
        new_entries.insert(last_sec_idx + 1 + j, (prefix + key, disk[key]))

    out_path = Path(out) if out else Path(archive)
    bak = None
    if make_backup and out_path.exists():
        tell("writing backup…")
        bak = backup_file(out_path)
    tell("compressing %d entries…" % len(new_entries))
    write_aps(out_path, new_entries)
    tell("verifying result…")
    err = verify_aps(out_path, new_entries)
    if err:
        # restore backup: never leave a corrupt archive in place
        if bak:
            shutil.copy2(bak, out_path)
        raise ApsError(
            "verification failed (%s)%s"
            % (err, ", original restored from backup" if bak else "")
        )
    return {
        "out": str(out_path),
        "backup": str(bak) if bak else None,
        "updated": updated,
        "unchanged": unchanged,
        "added": len(added_names),
        "kept_not_on_disk": kept,
        "deleted": deleted,
        "total_entries": len(new_entries),
    }


# ----------------------------------------------------------------------------
# Background jobs: long operations (unpack/pack) run in a worker thread so no
# HTTP request ever hangs for more than an instant — the browser polls status.
# ----------------------------------------------------------------------------

JOBS = {}
_jobs_lock = threading.Lock()
_job_seq = [0]


def start_job(fn, *args, **kwargs):
    with _jobs_lock:
        _job_seq[0] += 1
        jid = "job%d" % _job_seq[0]
        JOBS[jid] = {"status": "running", "progress": "starting…"}

    def tell(m):
        JOBS[jid]["progress"] = m

    def run():
        try:
            res = fn(*args, progress=tell, **kwargs)
            JOBS[jid].update(status="done", result=res)
        except Exception as e:  # noqa: BLE001
            JOBS[jid].update(status="error", error=str(e))

    threading.Thread(target=run, daemon=True).start()
    return jid


# ----------------------------------------------------------------------------
# unit stats — values interpreted exactly as the Unit Comparator HTML does.
# The comparator (Tools/HS2_Unit_Comparator_*.html) embeds `const units=[...]`
# with the interpreted stats (armor per side, penetration, Overall, AT Skill…).
# We join those rows to the unit files via their `name "..."` field.
# ----------------------------------------------------------------------------

_unitstats_cache = None


def unit_stats():
    global _unitstats_cache
    if _unitstats_cache is not None:
        return _unitstats_cache
    by_name = {}
    src = None
    files = sorted(SCRIPT_DIR.glob("HS2_Unit_Comparator_*.html"))
    if files:
        try:
            html = files[-1].read_text(encoding="utf-8", errors="replace")
            m = re.search(r"const units=(\[.*?\]);", html, re.S)
            for r in json.loads(m.group(1)) if m else []:
                # one comparator name carries a stray leading quote — strip it
                nm = (r.get("Nom de l'unité") or "").lstrip('"').strip()
                by_name.setdefault(nm, r)
            src = files[-1].name
        except (OSError, ValueError):
            pass
    units = {}
    units_dir = GAME_ROOT / "Modding" / "UNITS"
    if units_dir.is_dir():
        for f in sorted(units_dir.iterdir()):
            if not f.is_file() or f.name.startswith("."):
                continue
            try:
                head = f.read_bytes()[:4096].decode(ENC, "replace")
            except OSError:
                continue
            m = re.search(r'^name "([^"]*)"', head, re.M)
            name = m.group(1) if m else ""
            units[f.name] = {"name": name, "row": by_name.get(name)}
    _unitstats_cache = {"source": src, "units": units}
    return _unitstats_cache


# ----------------------------------------------------------------------------
# GUI (local web app, stdlib only)
# ----------------------------------------------------------------------------

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>HS2 APS Tool</title>
<style>
:root { --bg:#14171c; --panel:#1d2129; --line:#2c313c; --tx:#d7dbe2;
        --dim:#8a91a0; --acc:#5aa0e8; --ok:#5cbf74; --warn:#e8b45a; --err:#e86a5a; }
* { box-sizing:border-box; }
body { margin:0; font:14px/1.5 -apple-system,'Segoe UI',Roboto,sans-serif;
       background:var(--bg); color:var(--tx); padding:24px; }
h1 { font-size:20px; margin:0 0 4px; }
h1 small { color:var(--dim); font-weight:normal; font-size:13px; }
.card { background:var(--panel); border:1px solid var(--line); border-radius:10px;
        padding:18px 20px; margin:16px 0; max-width:880px; }
.card h2 { margin:0 0 10px; font-size:16px; color:var(--acc); }
label { display:block; margin:10px 0 3px; color:var(--dim); font-size:12px;
        text-transform:uppercase; letter-spacing:.4px; }
select, input[type=text] { width:100%; background:#12151a; color:var(--tx);
        border:1px solid var(--line); border-radius:6px; padding:7px 10px; font:inherit; }
.row { display:flex; gap:16px; } .row > div { flex:1; }
button { background:var(--acc); color:#fff; border:none; border-radius:6px;
         padding:9px 18px; font:inherit; font-weight:600; cursor:pointer; margin-top:14px; }
button.secondary { background:#333a47; }
button:disabled { opacity:.5; cursor:default; }
.chk { margin-top:12px; color:var(--tx); font-size:13px; display:flex;
       align-items:center; gap:8px; }
.chk input { accent-color: var(--acc); }
#log { background:#0e1013; border:1px solid var(--line); border-radius:8px;
       padding:12px 14px; font:12px/1.6 ui-monospace,Menlo,Consolas,monospace;
       white-space:pre-wrap; min-height:80px; max-width:880px; }
.ok { color:var(--ok); } .warn { color:var(--warn); } .err { color:var(--err); }
.hint { color:var(--dim); font-size:12px; margin-top:6px; }
table.sections { border-collapse:collapse; margin-top:8px; font-size:13px; }
table.sections td { padding:2px 14px 2px 0; color:var(--dim); }
table.sections td:first-child { color:var(--tx); }
table.stats { border-collapse:collapse; margin-top:12px; font-size:13px; width:100%; }
table.stats td { padding:4px 12px 4px 0; border-top:1px solid var(--line); }
table.stats td:first-child { color:var(--dim); white-space:nowrap; width:220px; }
table.stats td.armor-red { color:var(--err); font-weight:600; }
table.stats td.armor-orange { color:var(--warn); font-weight:600; }
table.stats td.score { color:var(--acc); font-weight:700; }
</style></head><body>
<h1>HS2 APS Tool <small>— unpack / repack FZFF archives (lang.aps &amp; co.)</small></h1>

<div class="card">
  <h2>1 · Unpack an archive</h2>
  <div class="row">
    <div>
      <label>Archive (.aps)</label>
      <select id="u_archive"></select>
    </div>
    <div>
      <label>Section (folder inside the archive)</label>
      <select id="u_section"><option value="">— whole archive —</option></select>
    </div>
  </div>
  <label>Destination folder</label>
  <input type="text" id="u_target">
  <div class="chk"><input type="checkbox" id="u_flat" checked>
    <span>Flat: drop the section folder (write <code>UNITS\\zis-2</code> as <code>zis-2</code>)</span></div>
  <div class="hint">Preset already filled in: <b>lang.aps → Modding/UNITS</b> (779 unit
    files). Existing files in the destination are overwritten.</div>
  <button id="u_go">Unpack</button>
  <div id="u_sections"></div>
</div>

<div class="card">
  <h2>2 · Repack a folder into the archive</h2>
  <div class="row">
    <div>
      <label>Archive to update (.aps)</label>
      <select id="p_archive"></select>
    </div>
    <div>
      <label>Section to replace</label>
      <select id="p_section"></select>
    </div>
  </div>
  <label>Source folder (your edited files)</label>
  <input type="text" id="p_source">
  <div class="chk"><input type="checkbox" id="p_delete">
    <span>Remove archive entries that no longer exist in the folder
      (default: keep them)</span></div>
  <div class="hint">A timestamped backup of the archive is written next to it before
    anything is changed, and the result is fully re-read and verified. If
    verification fails the original is restored automatically.</div>
  <button id="p_go">Repack + verify</button>
</div>

<div class="card">
  <h2>3 · Unit stats <small style="color:var(--dim);font-weight:normal">— values
    interpreted as in the Unit Comparator</small></h2>
  <label>Unit file (id from Modding/UNITS — type to search)</label>
  <input type="text" id="s_unit" list="s_ids" placeholder="e.g. m19, tiger, zis-2 …">
  <datalist id="s_ids"></datalist>
  <div class="hint" id="s_src"></div>
  <div id="s_out"></div>
</div>

<div class="card" style="padding:12px 20px">
  <h2 style="margin-bottom:8px">Log</h2>
  <div id="log">Ready.</div>
</div>

<script>
const $ = id => document.getElementById(id);
let INFO = null;

function log(msg, cls) {
  const el = $('log');
  const line = document.createElement('div');
  if (cls) line.className = cls;
  line.textContent = msg;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function api(path, body) {
  // retry transient network hiccups; give a clear message if the server is gone
  let lastErr;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const r = await fetch(path, body ? {method:'POST', body: JSON.stringify(body)} : {});
      const j = await r.json();
      if (j.error) throw new Error(j.error);
      return j;
    } catch (e) {
      lastErr = e;
      if (!(e instanceof TypeError)) throw e;   // server-side error: don't retry
      await sleep(600);
    }
  }
  throw new Error('cannot reach the APS Tool server — its terminal window was ' +
    'probably closed. Relaunch "APS Tool" and reload this page. (' +
    lastErr.message + ')');
}

async function runJob(path, body, onProgress) {
  const {job} = await api(path, body);
  let lastProg = '';
  while (true) {
    await sleep(600);
    let j;
    try { j = await api('/api/job?id=' + job); }
    catch (e) {
      if (String(e.message).startsWith('cannot reach')) throw e;
      continue;  // transient poll failure: keep waiting
    }
    if (j.progress && j.progress !== lastProg) {
      lastProg = j.progress;
      if (onProgress) onProgress(j.progress);
    }
    if (j.status === 'done') return j.result;
    if (j.status === 'error') throw new Error(j.error);
  }
}

function progressLine() {
  const el = $('log');
  const line = document.createElement('div');
  line.style.color = 'var(--dim)';
  el.appendChild(line);
  return t => { line.textContent = '   … ' + t; el.scrollTop = el.scrollHeight; };
}

function fillArchives(sel) {
  sel.innerHTML = '';
  for (const a of INFO.archives) {
    const o = document.createElement('option');
    o.value = a; o.textContent = a;
    sel.appendChild(o);
  }
}

async function refreshSections(which) {
  const arch = $(which + '_archive').value;
  try {
    const j = await api('/api/sections', {archive: arch});
    const sel = $(which + '_section');
    const keep = which === 'u' ? '<option value="">— whole archive —</option>' : '';
    sel.innerHTML = keep;
    let table = '<table class="sections">';
    for (const [sec, [n, bytes]] of Object.entries(j.sections)) {
      const o = document.createElement('option');
      o.value = sec === '(root)' ? '' : sec;
      o.textContent = sec + '  (' + n + ' files)';
      if (sec === 'UNITS') o.selected = true;
      if (!(which === 'p' && sec === '(root)')) sel.appendChild(o);
      table += '<tr><td>' + sec + '</td><td>' + n + ' files</td><td>' +
               (bytes/1024).toFixed(0) + ' KB</td></tr>';
    }
    table += '</table>';
    if (which === 'u') $('u_sections').innerHTML = table;
  } catch (e) { log('Cannot read ' + arch + ': ' + e.message, 'err'); }
}

async function init() {
  INFO = await api('/api/info');
  fillArchives($('u_archive'));
  fillArchives($('p_archive'));
  const def = INFO.archives.find(a => a.toLowerCase().endsWith('lang.aps'));
  if (def) { $('u_archive').value = def; $('p_archive').value = def; }
  $('u_target').value = INFO.default_units_dir;
  $('p_source').value = INFO.default_units_dir;
  await refreshSections('u');
  await refreshSections('p');
  $('u_archive').onchange = () => refreshSections('u');
  $('p_archive').onchange = () => refreshSections('p');
  log('Game root: ' + INFO.root);
}

$('u_go').onclick = async () => {
  $('u_go').disabled = true;
  try {
    log('Unpacking ' + $('u_archive').value + ' ...');
    const j = await runJob('/api/unpack', {
      archive: $('u_archive').value, section: $('u_section').value,
      target: $('u_target').value, flat: $('u_flat').checked }, progressLine());
    log('Done: ' + j.written + ' file(s) written to ' + j.out_dir +
        (j.skipped ? ' (' + j.skipped + ' outside section skipped)' : ''), 'ok');
  } catch (e) { log('FAILED: ' + e.message, 'err'); }
  $('u_go').disabled = false;
};

$('p_go').onclick = async () => {
  $('p_go').disabled = true;
  try {
    log('Repacking ' + $('p_archive').value + ' from ' + $('p_source').value + ' ...');
    const j = await runJob('/api/pack', {
      archive: $('p_archive').value, section: $('p_section').value,
      source: $('p_source').value, delete_missing: $('p_delete').checked },
      progressLine());
    log('Done: ' + j.updated + ' updated, ' + j.unchanged + ' unchanged, ' +
        j.added + ' added, ' + j.deleted + ' deleted, ' +
        j.kept_not_on_disk + ' kept (not on disk). Total ' + j.total_entries +
        ' entries.', 'ok');
    if (j.backup) log('Backup: ' + j.backup, 'warn');
    log('Archive re-read and verified OK.', 'ok');
  } catch (e) { log('FAILED: ' + e.message, 'err'); }
  $('p_go').disabled = false;
};

/* ----- unit stats card: same interpretation rules as the comparator HTML ----- */
let USTATS = null;
// column order + English labels, as in the comparator's `cols`
const STAT_COLS = [
  ['Nation','Nation'],['Overall','Overall'],['AT Skill','AT Skill'],
  ['PV','Hit points (PV)'],['Immobilisation','Immobilisation'],
  ['Blindage frontal (mm)','Front armor (mm)'],['Blindage latéral (mm)','Side armor (mm)'],
  ['Blindage arrière (mm)','Rear armor (mm)'],['Pénétration (mm)','Penetration (mm)'],
  ['Portée','Range'],['Précision','Accuracy'],['Temps de rechargement','Reload time'],
  ['Silhouette','Silhouette'],['Vitesse','Speed'],['Vision','Vision'],
  ['Bonus vision','Vision bonus'],['seltype','seltype'],['targettype','targettype'],
  ['Tourelle','Turret'],['Arme secondaire','Secondary weapon'],
  ['Vulnérable / ouvert','Vulnerable / open-top']
];
const ARMOR_KEYS = new Set(['Blindage frontal (mm)','Blindage latéral (mm)','Blindage arrière (mm)']);
const YESNO = {OUI:'YES', NON:'NO'};
const SECW = {'Mitrailleuse standard':'Standard machine gun',
  'Mitrailleuse lourde / 12,7 mm':'Heavy machine gun / .50 cal',
  'Canon secondaire':'Secondary cannon','Lance-flammes':'Flamethrower','—':'—'};
function statFmt(k, v){
  if (v === null || v === undefined || v === '') return '—';
  if (k === 'Tourelle' || k === 'Vulnérable / ouvert') return YESNO[v] || v;
  if (k === 'Arme secondaire') return SECW[v] || v;
  return String(v);
}
// same rule as the comparator's armorClass(): <43 red, <=50 orange
function statArmorClass(k, v){
  if (!ARMOR_KEYS.has(k) || typeof v !== 'number') return '';
  if (v < 43) return 'armor-red';
  if (v <= 50) return 'armor-orange';
  return '';
}
function renderUnitStats(){
  const id = $('s_unit').value.trim();
  const out = $('s_out');
  if (!USTATS || !id) { out.innerHTML = ''; return; }
  const u = USTATS.units[id];
  if (!u) { out.innerHTML = '<div class="hint">Unknown unit id.</div>'; return; }
  if (!u.row) {
    out.innerHTML = '<div class="hint"><b>' + (u.name || id) + '</b> — not rated by ' +
      'the comparator (infantry, guns and planes are outside its scope).</div>';
    return;
  }
  let html = '<table class="stats"><tr><td>Unit</td><td><b>' +
    (u.name || id) + '</b></td></tr>';
  for (const [k, label] of STAT_COLS) {
    const v = u.row[k];
    const cls = (k === 'Overall' || k === 'AT Skill') ? 'score' : statArmorClass(k, v);
    html += '<tr><td>' + label + '</td><td class="' + cls + '">' + statFmt(k, v) + '</td></tr>';
  }
  html += '</table>';
  out.innerHTML = html;
}
async function initStats(){
  try { USTATS = await api('/api/unitstats'); }
  catch (e) { $('s_src').textContent = 'Unit stats unavailable: ' + e.message; return; }
  const dl = $('s_ids');
  let rated = 0;
  for (const [id, u] of Object.entries(USTATS.units)) {
    const o = document.createElement('option');
    o.value = id; o.label = u.name || '';
    dl.appendChild(o);
    if (u.row) rated++;
  }
  $('s_src').textContent = USTATS.source
    ? Object.keys(USTATS.units).length + ' unit files, ' + rated +
      ' rated — scores from ' + USTATS.source
    : 'Comparator HTML not found in Tools/ — names only, no stats.';
  $('s_unit').oninput = renderUnitStats;
}

init().catch(e => log('Startup failed: ' + e.message, 'err'));
initStats();
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence default logging
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, "application/json", json.dumps(obj).encode("utf-8"))

    def do_GET(self):
        if self.path == "/":
            self._send(200, "text/html; charset=utf-8", HTML.encode("utf-8"))
        elif self.path.startswith("/api/job"):
            from urllib.parse import parse_qs, urlparse

            jid = parse_qs(urlparse(self.path).query).get("id", [""])[0]
            job = JOBS.get(jid)
            self._json(job if job else {"error": "unknown job"})
        elif self.path == "/api/info":
            archives = []
            run = GAME_ROOT / "Run"
            if run.is_dir():
                for p in sorted(run.rglob("*.aps")):
                    archives.append(str(p.relative_to(GAME_ROOT)))
            self._json(
                {
                    "root": str(GAME_ROOT),
                    "archives": archives,
                    "default_units_dir": str(GAME_ROOT / "Modding" / "UNITS"),
                }
            )
        elif self.path == "/api/unitstats":
            self._json(unit_stats())
        else:
            self._send(404, "text/plain", b"not found")

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/sections":
                # directory-only read: instant even on huge archives
                sections = op_sections(GAME_ROOT / req["archive"])
                self._json({"sections": sections})
            elif self.path == "/api/unpack":
                jid = start_job(
                    op_unpack,
                    GAME_ROOT / req["archive"],
                    only=req.get("section") or None,
                    out_dir=req.get("target") or None,
                    flat=bool(req.get("flat")),
                )
                self._json({"job": jid})
            elif self.path == "/api/pack":
                jid = start_job(
                    op_pack,
                    GAME_ROOT / req["archive"],
                    section=req["section"],
                    src_dir=req["source"],
                    delete_missing=bool(req.get("delete_missing")),
                )
                self._json({"job": jid})
            else:
                self._json({"error": "unknown endpoint"}, 404)
        except Exception as e:  # noqa: BLE001
            self._json({"error": str(e)}, 500)


def run_gui(port=8766):
    httpd = None
    for p in range(port, port + 20):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        print("No free port found.")
        sys.exit(1)
    url = "http://127.0.0.1:%d/" % port
    print("HS2 APS Tool running at %s  (Ctrl+C to quit)" % url)
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("list", help="list archive contents")
    s.add_argument("archive")

    s = sub.add_parser("unpack", help="extract files")
    s.add_argument("archive")
    s.add_argument("--only", help="only this section (e.g. UNITS)")
    s.add_argument("--out", help="destination folder")
    s.add_argument(
        "--flat", action="store_true", help="drop the section folder in output paths"
    )

    s = sub.add_parser("pack", help="rebuild archive from a folder")
    s.add_argument("archive")
    s.add_argument("--section", required=True)
    s.add_argument("--from", dest="src", required=True)
    s.add_argument("--out", help="write result here instead of in place")
    s.add_argument("--delete-missing", action="store_true")

    sub.add_parser("gui", help="open the browser GUI (default)")

    args = ap.parse_args()
    if args.cmd in (None, "gui"):
        run_gui()
    elif args.cmd == "list":
        entries, sections = op_list(args.archive)
        for name, data in entries:
            print("%9d  %s" % (len(data), name))
        print("--")
        for sec, (n, b) in sections.items():
            print("%s: %d files, %d bytes" % (sec, n, b))
    elif args.cmd == "unpack":
        res = op_unpack(args.archive, only=args.only, out_dir=args.out, flat=args.flat)
        print(
            "%d file(s) written to %s (%d skipped)"
            % (res["written"], res["out_dir"], res["skipped"])
        )
    elif args.cmd == "pack":
        res = op_pack(
            args.archive,
            section=args.section,
            src_dir=args.src,
            out=args.out,
            delete_missing=args.delete_missing,
        )
        print(json.dumps(res, indent=2))
        print("Archive verified OK.")


if __name__ == "__main__":
    main()
