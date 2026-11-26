"""Reading rules for the NIC quarterly returns workbook, shared by step 09 (total assets) and step 12 (returns panel).

The workbook is published by the NIC on its website (data/raw/quarterly/SOURCE.md); its figures are insurers' unaudited
quarterly submissions (data_issues A15, A17). It is tracked in git and checked against its SHA-256 before it is read.
Moved unchanged from step 09 (v2, Part 2), plus the sheet-name parser; step 09's outputs are identical.
"""
import re, sys, hashlib
from names import canon
from config import QUARTERLY_FILE, QUARTERLY_SHA256, QUARTERLY_LAST

def open_workbook():
    """The NIC quarterly returns workbook, after its SHA-256 is checked against data/raw/CHECKSUMS."""
    if not QUARTERLY_FILE.exists():
        sys.exit(f"Missing {QUARTERLY_FILE} (tracked in git: restore it with git checkout).")
    if hashlib.sha256(QUARTERLY_FILE.read_bytes()).hexdigest() != QUARTERLY_SHA256:
        sys.exit(f"Checksum mismatch for {QUARTERLY_FILE.name}: the reading rules are only valid for the recorded edition.")
    import openpyxl
    return openpyxl.load_workbook(QUARTERLY_FILE, data_only=True, read_only=True)

def in_scope(qy):
    """True for a (quarter, year) sheet up to QUARTERLY_LAST (Q1 2026)."""
    return qy is not None and (qy[1], qy[0]) <= QUARTERLY_LAST

HDR_NAME = ('company', 'non-life insurer', 'non life insurers')
ALIASES = [(r'^gn insurance', 'BEDROCK', None), (r'^equity assurance', 'SUNU', None),
           (r'^regency insurance', 'REGENCYNEM', 2016)]          # (pattern, id, last year valid)
# Regency is the continuing company of RegencyNem; it is listed under the old name until Q1 2016 (authors' decision
# after the v2 Part 2 review; previously 2015). Step 09 reads only Q3/Q4 sheets, where the old name does not occur in 2016.
EXCLUDE = [r'^nem insurance', r'^industrial\s*(&|and)\s*general']  # not in the Tier 1 panel
SHEET = re.compile(r'^\s*q\s*([1-4])\s*,?\s*(\d{4})\s*$', re.I)      # 'Q4, 2015', 'Q4 2020', 'Q2,2018', 'Q4,2014'

def norm(v):
    return re.sub(r'\s+', ' ', str(v)).strip().lower() if v is not None else ''

def map_id(name, year):
    """Canonical insurer ID, 'EXCLUDED' for insurers outside the panel, or None if unmapped."""
    n = norm(name).replace('*', '')
    if any(re.search(p, n) for p in EXCLUDE): return 'EXCLUDED'
    for p, cid, last in ALIASES:
        if re.search(p, n) and (last is None or year <= last): return cid
    return canon(str(name))

def sheet_quarter(name):
    """(quarter, year) for a quarterly sheet name, else None."""
    m = SHEET.match(name)
    return (int(m.group(1)), int(m.group(2))) if m else None

def header_row(rows):
    """Index of the LAST header row (earlier ones are INDEX lookup blocks) and the name column."""
    h = [i for i, r in enumerate(rows) if any(norm(c) in HDR_NAME for c in r)][-1]
    hn = [norm(c) for c in rows[h]]
    return h, hn, next(i for i, c in enumerate(hn) if c in HDR_NAME)

def data_rows(rows, h, nc):
    """Rows below the header with a name, stopping at a total/industry row."""
    for r in rows[h + 1:]:
        nm = r[nc] if nc < len(r) else None
        if nm is None or not str(nm).strip(): continue
        if re.match(r'^\s*(total|industry|grand)', str(nm), re.I): break
        yield r, str(nm).strip()
