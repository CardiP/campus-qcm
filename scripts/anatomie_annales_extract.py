"""Extract anatomy exams and EB2; share the source-faithful PDF cropper."""
from pathlib import Path
import sys,json,re,collections
# Reuse definitions without running the bank import.
scope={'__file__':str(Path(__file__).with_name('anatomie_extract.py'))}
exec(Path(__file__).with_name('anatomie_extract.py').read_text().split('files=sorted(SRC.glob')[0],scope)
Doc=scope['Doc'];SRC=scope['SRC'];TMP=scope['TMP'];RENDER=scope['RENDER'];ITEM=scope['ITEM'];H=scope['H'];getitems=scope['items']
manifest=json.loads((TMP/'manifest.json').read_text());files={m['id']:SRC/m['file'] for m in manifest}
qs=[];layouts={}
for fid,year in [(57,'2020-2021'),(52,'2021-2022'),(47,'2022-2023'),(53,'2023-2024'),(54,'2024-2025'),(58,'eb2')]:
 doc=Doc(files[fid]);is_eb=year=='eb2'
 if fid==57:
  ocr=TMP/'scan2021/ocr.json'
  if not ocr.exists():ocr=Path(__file__).parent/'data/anatomie-2021-ocr.json'
  pages=json.loads(ocr.read_text());doc.lines=[]
  for pg in pages:
   p=pg['page']-1
   for ln in pg['lines']:
    x,y,x2,y2=ln['bbox'];t=ln['text']
    if 35<y<doc.pdf[p].rect.height-55:doc.lines.append(dict(p=p,x=x,y=y,y2=y2,text=t))
  doc.lines.sort(key=lambda l:(l['p'],round(l['y']/3),l['x']))
 if is_eb:blocks=doc.blocks
 else:
  lines=[l for l in doc.lines if l['p']>0];inds=[]
  for i,l in enumerate(lines):
   m=ITEM.match(l['text'])
   if m and l['x']<130:inds.append((i,int(m[1])))
  expected=list(range(1,176));actual=[n for i,n in inds]
  print(year,'items',len(actual),'missing',sorted(set(expected)-set(actual)),'duplicates',[n for n,k in collections.Counter(actual).items() if k>1])
  starts=[]
  for k in range(0,len(inds),5):
   i,n=inds[k];prev=inds[k-1][0] if k else -1
   start=prev+1
   # Keep only the new page when the previous question ended on the preceding page.
   while start<i and lines[start]['p']<lines[i]['p']:start+=1
   starts.append(start)
  blocks=[]
  for k,start in enumerate(starts):
   stop=starts[k+1] if k+1<len(starts) else len(lines)
   ls=lines[start:stop];nxt=lines[stop] if stop<len(lines) else None
   blocks.append(dict(number=k+1,qlines=ls,question='\n'.join(l['text'] for l in ls),next=nxt))
 for i,b in enumerate(blocks,1):
  it=getitems(b);qid=f'anat-{year}-q{i:02}';ps=sorted({l['p']+1 for l in b['qlines']})
  q={'id':qid,'subject':'anatomie','category':'eb' if is_eb else 'annales','sourceId':f'anat-{year}','sourceLabel':'Examen blanc 2 · 2026–2027' if is_eb else f'Annale {year}','number':i,'chapter':'transversal','topic':'À classer','title':it[0] if it else b['qlines'][0]['text'],'text':b['question'],'choices':it[2] if it else ['Voir la proposition '+c+' sur l’image' for c in 'ABCDE'],'itemNumbers':it[1] if it else None,'answers':None,'explanation':'','images':doc.render(b['qlines'],qid,b['next']) if RENDER else [],'correctionImages':[],'correctionStatus':'missing','sourceFile':files[fid].name,'sourcePages':ps}
  qs.append(q);layouts[qid]={'file':fid,'lines':b['qlines'],'next':b['next']}
 print(year,'questions',len(blocks),'bad',[q['id'] for q in qs if q['sourceId']==f'anat-{year}' and q['itemNumbers'] is None])
(TMP/'exams.json').write_text(json.dumps(qs,ensure_ascii=False,indent=2));(TMP/'exam-layouts.json').write_text(json.dumps(layouts,ensure_ascii=False))
for year in ['2020-2021','2021-2022','2022-2023','2023-2024','2024-2025','eb2']:
 (TMP/f'exam-{year}.txt').write_text('\n\n'.join(q['id']+'\n'+q['title']+'\n'+'\n'.join(chr(65+i)+'. '+t for i,t in enumerate(q['choices'])) for q in qs if q['sourceId']==f'anat-{year}'))
