"""Extract ACC and annual exams, preserving each occurrence before deduplication."""
import medicament_extract as m
from pathlib import Path
import re,json,collections
W=m.W
PAIRS=[(77,61),(79,62),(81,63),(84,64),(80,68),(82,59),(83,66),(85,69),(86,70),(76,60),(89,65),(78,67),(87,71),(88,72),(90,73),(91,75),(92,None),(50,45),(47,46),(49,48),(44,43),(42,41),(53,54),(38,55),(39,56),(40,57),(51,52)]
GY=re.compile(r'^(20\d{2}|19\d{2})\s*(LAS|PASS)?$',re.I)
GA=re.compile(r'^[QO0]\s*(\d+)\s*[:.]\s*(.*)',re.I)
def grid(doc):
 result=[]
 for p,ls in enumerate(doc.pages[1:],1):
  if any('corrigedetaille' in m.norm(l['text']) for l in ls):break
  years=[]
  for l in ls:
   t=m.flat(l['text']);ym=GY.fullmatch(t)
   if ym:years.append(dict(**l,year=ym[1],section=(ym[2] or 'PASS').upper(),center=(l['x']+l['x2'])/2))
  # Year labels share a horizontal row, which defines the answer column boundaries.
  groups=[]
  for y in sorted(years,key=lambda x:(x['y'],x['x'])):
   if groups and abs(groups[-1][0]['y']-y['y'])<9:groups[-1].append(y)
   else:groups.append([y])
  for l in ls:
   a=GA.match(m.flat(l['text']))
   if not a:continue
   above=[g for g in groups if max(y['y'] for y in g)<l['y']+3]
   if not above:continue
   g=above[-1];center=(l['x']+l['x2'])/2;y=min(g,key=lambda y:abs(center-y['center']));body=a[2]
   n=int(a[1]);start=(n-1)*5+1
   # A response cell can wrap onto the next line (e.g. 56, 57, 58 / 59, 60).
   for continuation in ls:
    text=continuation['text'].strip()
    if 0<continuation['y']-l['y']<23 and abs((continuation['x']+continuation['x2'])/2-center)<35 and re.fullmatch(r'[\d,; .]+',text) and not GY.fullmatch(text):
     extra=[int(n) for n in re.findall(r'\d+',text)]
     if extra and all(start<=v<start+5 for v in extra):body+=' '+text
   nums=[int(n) for n in re.findall(r'\d+',body)]
   valid=all(start<=v<start+5 for v in nums)
   if 'TOUT' in body.upper():answers=[not bool(re.search('NON|FAUX',body,re.I))]*5
   elif nums and valid:answers=[v in nums for v in range(start,start+5)]
   else:answers=None
   result.append(dict(number=n,year=y['year'],section=y['section'],answers=answers,raw=body,page=p+1,bbox=[l['x'],l['y'],l['x2'],l['y2']]))
 return result

def record(doc,b,ix,category='acc',sourceLabel=None):
 qid=f'med-d{doc.id:03}-q{ix:03}';year=b['year'];sec=b['section']
 return dict(id=qid,subject='medicament',category=category,sourceId=f'med-d{doc.id:03}',sourceLabel=sourceLabel or doc.meta['file'].split('/')[-1].removesuffix('.pdf'),number=ix,originalNumber=b['number'],year=year,section=sec,title=b['title'],text='\n'.join(l['text'] for l in b['qlines']),choices=b['choices'],itemNumbers=b['itemNumbers'],answers=None,explanation='',correctionStatus='missing',sourceFile=doc.meta['file'],sourcePages=sorted({l['p']+1 for l in b['qlines']}),sourceDocument=doc.id,correctionDocument=None,correctionSourceFile=None,correctionSourcePages=[],images=[],correctionImages=[],layout=b)
if __name__=='__main__':
 qs=[];audits=[];grids={};details={}
 for sid,cid in PAIRS:
  sd=m.Doc(sid);cd=m.Doc(cid) if cid else None;bs=[m.parse(b) for b in sd.blocks('acc-subject')];cs=cd.blocks('acc-correction') if cd else [];gs=grid(cd) if cd else [];grids[str(cid)]=gs;details[str(cid)]=cs
  for ix,b in enumerate(bs,1):
   q=record(sd,b,ix);num=b['number'] or (((b['itemNumbers'][0]-1)//5+1) if b['itemNumbers'] else None)
   matches=[c for c in cs if c['year']==b['year'] and c['section']==b['section'] and c['number']==num]
   # The item index is safer than a mistyped Q heading in some supplied corrections.
   if not matches and b['itemNumbers']:
    matches=[c for c in cs if c['year']==b['year'] and c['section']==b['section'] and any(re.match(r'^'+str(b['itemNumbers'][0])+r'\s*[.)]\s*(?:OUI|NON)',l['text'],re.I) for l in c['lines'])]
   c=matches[0] if len(matches)==1 else None;g=next((g for g in gs if g['number']==num and g['year']==b['year'] and g['section']==b['section']),None)
   ans,det,conflict=m.key(c['lines']) if c else (None,None,False)
   if ans is None and g:ans=g['answers']
   if c and g and ans is not None and g['answers'] is not None and ans!=g['answers']:conflict=True
   q.update(answers=ans,explanation='\n'.join(l['text'] for l in c['lines']) if c else '',correctionStatus='conflict' if conflict else 'source' if ans is not None else 'missing',correctionDocument=cid if c or g else None,correctionSourceFile=cd.meta['file'] if c or g else None,correctionSourcePages=sorted({l['p']+1 for l in c['lines']}) if c else [g['page']] if g else [],sourceGrid=g,correctionLayout=c)
   if m.RENDER:
    q['images']=sd.render(b['qlines'],q['id'],b['next']);q['correctionImages']=cd.render(c['lines'],q['id']+'-corr',c['next']) if c else []
   qs.append(q)
  audits.append(dict(subject=sid,correction=cid,count=len(bs),bad=[q['id'] for q in qs if q['sourceDocument']==sid and len(q['choices'])!=5],statuses=dict(collections.Counter(q['correctionStatus'] for q in qs if q['sourceDocument']==sid))))
  print(audits[-1],flush=True)
 for fid,year in [(37,'2020-2021'),(32,'2021-2022'),(35,'2022-2023'),(33,'2023-2024'),(34,'2024-2025')]:
  d=m.Doc(fid);bs=[m.parse(b) for b in d.blocks('exam')]
  for ix,b in enumerate(bs,1):
   q=record(d,b,ix,'annales','Annale '+year);q['year']=year[-4:];q['section']='LAS';qs.append(q)
  print('Exam',fid,year,len(bs), 'bad',sum(len(b['choices'])!=5 for b in bs),flush=True)
 (W/'acc-exams.json').write_text(json.dumps(qs,ensure_ascii=False));(W/'acc-audit.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2));(W/'acc-grids.json').write_text(json.dumps(grids,ensure_ascii=False,indent=2));(W/'acc-details.json').write_text(json.dumps(details,ensure_ascii=False))
 print('Total',len(qs),collections.Counter(q['correctionStatus'] for q in qs))
