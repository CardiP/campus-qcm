"""Rebuild using original PDFs and the committed OCR/layout cache.
Usage: python scripts/medicament_import.py /path/to/Downloads /tmp/campus-meds
Dependencies: PyMuPDF, Pillow. No network service or OCR dependency needed.
"""
import gzip,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent;source=Path(sys.argv[1]).resolve();work=Path(sys.argv[2]).resolve();work.mkdir(parents=True,exist_ok=True)
cache=json.loads(gzip.decompress((ROOT/'data/medicament-layout-cache.json.gz').read_bytes()))
for name,data in cache.items():
 p=work/name
 if not p.resolve().is_relative_to(work):raise ValueError(name)
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False))
for script,args in [('medicament_extract.py',[source,work]),('medicament_acc_extract.py',[source,work]),('medicament_supplement.py',[source,work]),('medicament_prepare.py',[work]),('medicament_dedupe.py',[work]),('medicament_curate.py',[]),('medicament_build.py',[source,work,'--render'])]:
 subprocess.run([sys.executable,str(ROOT/script),*map(str,args)],check=True)
