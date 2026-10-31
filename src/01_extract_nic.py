"""Step 1: verify raw NIC text files, normalise line endings, parse all table blocks."""
import hashlib, json, sys
from config import RAW_NIC, INTERIM, REPORT_YEARS, CHECKSUMS
from nic_parser import parse_blocks

def main():
    blocks = []
    for y in REPORT_YEARS:
        f = RAW_NIC / f"NIC_Annual_Report_{y}.txt"
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        if h != CHECKSUMS[y]:
            sys.exit(f"Checksum mismatch for {f.name}. The parser line map is only valid for the bundled file.")
        text = f.read_bytes().decode("utf-8", errors="ignore").replace("\r", "")
        out = INTERIM / f"nic_{y}.txt"
        out.write_text(text, encoding="utf-8")
        b = parse_blocks(str(out), y)
        blocks += b
        print(f"{y}: {len(b)} table blocks parsed")
    (INTERIM / "blocks.json").write_text(json.dumps(blocks))

if __name__ == "__main__":
    main()
