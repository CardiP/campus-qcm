"""Audited extraction exceptions and final asset validation.
Run after banques_extract.py. Changes refer only to supplied source PDFs.
"""
import json, collections, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'public/data/banques.json'
data=json.loads(p.read_text())
# The detailed correction to Krebs Q30 contains unfilled placeholder propositions.
# Its actual answer key is nevertheless explicitly printed in the source's grid, p.2.
q=next(q for q in data if q['id']=='banques-krebs-30')
q.update(answers=[True,False,True,False,True],correctionStatus='source',
 explanation='Grille de réponses du corrigé, page 2 : ONONO. Le corrigé détaillé de cette question contient des espaces réservés (« Item 96 », etc.) ; seule la grille de réponses est reproduite ici.',
 correctionImages=[],correctionSourceFile='QCM/CORRECTION/4 Métabolisme/Correction-banque-unique-cycle-de-Krebs.pdf',correctionSourcePages=[2])
# Keep ambiguity visible; never silently decide between contradictory supplied keys.
for q in data:
 if q['correctionStatus']=='conflict' and not q['explanation'].startswith('Le document'):
  q['explanation']='Le document source contient des réponses contradictoires entre la grille et le corrigé détaillé, ou au sein du corrigé. Cette question est exclue du score automatique.\n\n'+q['explanation']
 assert len(q['choices'])==5,q['id']
 assert q['answers'] is None or len(q['answers'])==5,q['id']
 assert q['images'],q['id']
 assert q['answers'] is not None or q['correctionStatus'] in ('missing','conflict'),q['id']
 for file in q['images']+q['correctionImages']:
  assert (ROOT/'public'/file).is_file(),(q['id'],file)
assert len({q['id'] for q in data})==len(data)
assert collections.Counter(q['category'] for q in data)=={'banques':664,'eb':50,'td':25}
assert len(data)==739,len(data)
p.write_text(json.dumps(data,ensure_ascii=False,indent=2))
refs={file for q in data for file in q['images']+q['correctionImages']}
removed=0
for image in (ROOT/'public/assets/banques').glob('*.webp'):
 if str(image.relative_to(ROOT/'public')) not in refs:
  image.unlink();removed+=1
report={'total':len(data),'categories':dict(collections.Counter(q['category'] for q in data)),
 'statuses':dict(collections.Counter(q['correctionStatus'] for q in data)),
 'assets':len(refs),'unreferencedAssetsRemoved':removed,
 'exceptions':[{'id':q['id'],'status':q['correctionStatus'],'source':q['sourceFile'],'pages':q['sourcePages']} for q in data if q['correctionStatus'] in ('missing','conflict')],
 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(ROOT/'tmp/banques-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='exceptions'},ensure_ascii=False,indent=2))
