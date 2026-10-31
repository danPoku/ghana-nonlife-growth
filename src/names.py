"""Canonical insurer IDs, shared by step 02 (NIC reports) and step 09 (quarterly returns workbook)."""
import re

CANON=[('ACTIVA',r'^activa'),('ALLIANZ',r'^allianz(?! life)'),('BEDROCK',r'^bedrock'),('BEST',r'^best'),
('CORONATION',r'^(coronation|wapic)'),('DONEWELL',r'^donewell(?! life)'),('ENTERPRISE',r'^enterprise(?! life)'),
('GUA',r'^(gua(?! life)|ghana union)'),('GLICO_GEN',r'^glico general'),('HERITAGE',r'^heritage'),('HOLLARD',r'^hollard(?! life)'),
('IMPERIAL',r'^imperial'),('LOYALTY',r'^loyalty'),('MILLENNIUM',r'^millennium'),('MULTI',r'^multi'),('NSIA',r'^nsia'),
('PHOENIX',r'^phoenix(?! life)'),('PRIME',r'^prime'),('PRIORITY',r'^priority'),('PROVIDENT',r'^provident'),('QUALITY',r'^quality(?! life)'),
('REGENCYNEM',r'^regencynem'),('SAHAM_SANLAM',r'^(saham|sanlam)(?!.*life)'),('SERENE',r'^serene'),('SIC',r'^sic(?! life)'),
('STAR',r'^star(?!life)'),('SUNU',r'^sunu'),('UNIQUE',r'^unique'),('VANGUARD',r'^vanguard(?! life)')]
def canon(n):
    n2=n.lower().replace('*','').strip()
    for cid,pat in CANON:
        if re.search(pat,n2): return cid
    return None
