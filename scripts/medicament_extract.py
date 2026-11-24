"""Extract supplied medicine PDFs with layout, provenance and conservative matching.
Usage: python scripts/medicament_extract.py DOWNLOADS_DIR WORK_DIR [--render]
PyMuPDF/Pillow are needed for source crops; OCR coordinates are cached separately.
"""
from pathlib import Path
import json,re,sys,unicodedata,hashlib,difflib,collections
import pymupdf as fitz
from PIL import Image
BASE=Path(sys.argv[1]);W=Path(sys.argv[2]);ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public';ASSETS=OUT/'assets/medicament';RENDER='--render' in sys.argv
MAN=json.loads((W/'manifest.json').read_text());META={d['id']:d for d in MAN};ASSETS.mkdir(exist_ok=True)
H=re.compile(r'^(?:Questions?\s*(\d+)\b|QCM\s*(\d+)\s*[.:)]?|Q\s*(\d+)\s*[.:)]|(?:([0-9]+)\s*[.)]\s*)?QCM\b)',re.I)
I=re.compile(r'^\s*(\d{1,3})(?:\s*[.)]\s*|\s+|(?=[A-ZÉÈ]))(.*)',re.I)
Y=re.compile(r'^\s*(20\d{2}|19\d{2})(?:\s*[-/]\s*(?:20)?\d{2})?\s*(LAS|PASS)?\s*:?[\s]*$',re.I)
C=re.compile(r'^(?:R[ée]ponses?|Corrections?)\s*[:：]|(?<![A-Z])[ONVF]{5}(?![A-Z])',re.I)
def flat(s):return re.sub(r'\s+',' ',s.replace('\u200b','').replace('\ufeff','')).strip()
def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def clean(s):return flat(re.sub(r'^(?:T?OUI\s*[/|]\s*NON|oui\s+non)\s*:?[\s]*','',s,flags=re.I)).lstrip(': ').strip()
class Doc:
 def __init__(self,fid):
  self.id=fid;self.meta=META[fid];self.pdf=fitz.open(BASE/self.meta['file']);self.pages=[];ocr=W/'ocr'/f'{fid:03}'/'pages.json'
  cached=W/'layouts'/f'{fid:03}.json';cached.parent.mkdir(exist_ok=True)
  if cached.exists():self.pages=json.loads(cached.read_text())
  else:
   if self.meta['chars']==0 or fid==37:
    if not ocr.exists():raise FileNotFoundError(ocr)
    for pg in json.loads(ocr.read_text()):self.pages.append([dict(p=pg['page']-1,x=l['bbox'][0],y=l['bbox'][1],x2=l['bbox'][2],y2=l['bbox'][3],text=flat(l['text'])) for l in pg['lines']])
   else:
    for p,pg in enumerate(self.pdf):
     lines=[]
     for b in pg.get_text('dict')['blocks']:
      for l in b.get('lines',[]):
       if abs(l.get('dir',(1,0))[1])>.15:continue
       t=flat(''.join(s['text'] for s in l['spans']))
       if t:lines.append(dict(p=p,x=l['bbox'][0],y=l['bbox'][1],x2=l['bbox'][2],y2=l['bbox'][3],text=t))
     self.pages.append(lines)
   cached.write_text(json.dumps(self.pages,ensure_ascii=False))
  embedded=W/'embedded-lines.json'
  if embedded.exists() and fid not in [20,23]:
   for l in json.loads(embedded.read_text()).get(str(fid),[]):
    l=dict(l)
    if re.fullmatch('[ONVF0]{5}',l['text']):l['text']=l['text'].replace('0','O')
    page=self.pages[l['p']];lc=(l['y']+l['y2'])/2
    overlap=[z for z in page if abs((z['y']+z['y2'])/2-lc)<max(5,(l['y2']-l['y'])*.55) and min(z['x2'],l['x2'])-max(z['x'],l['x'])>min(z['x2']-z['x'],l['x2']-l['x'])*.4]
    if overlap:
     existing=flat(' '.join(z['text'] for z in sorted(overlap,key=lambda z:z['x'])))
     if len(norm(existing))>=len(norm(l['text']))*.75:continue
     page[:]=[z for z in page if z not in overlap]
    page.append(l)
  self.lines=[]
  for p,ls in enumerate(self.pages):
   ph=self.pdf[p].rect.height
   groups=[]
   for raw in sorted(ls,key=lambda l:((l['y']+l['y2'])/2,l['x'])):
    center=(raw['y']+raw['y2'])/2
    if groups and abs(groups[-1][0]-center)<3.5:groups[-1][1].append(dict(raw))
    else:groups.append((center,[dict(raw)]))
   rows=[]
   for center,group in groups:
    group.sort(key=lambda l:l['x']);l=dict(group[0])
    for z in group[1:]:l['text']+=' '+z['text'];l['x2']=max(l['x2'],z['x2']);l['y']=min(l['y'],z['y']);l['y2']=max(l['y2'],z['y2'])
    rows.append(l)
   for l in rows:
    t=l['text']
    if re.fullmatch(r'\d{1,3}',t) and l['y']>ph*.87:continue
    if l['y']<14 or l['y']>ph-34:continue
    if re.search(r'^(?:TUTORAT|UE\s*(?:7|N|M[ÉE]DICAMENT)|M[ÉE]DISUP|SCIENCES$|PARIS SACLAY$|Page\s+\d+|Ce document est|Université|Faculté|FIN DU|ERRATA)|^\d{1,2}/\d{1,2}/20\d\d$|^20\d\d\s*[-/]\s*20\d\d$',t,re.I):continue
    if re.fullmatch(r'[\W_]+',t):continue
    self.lines.append(l)
 def blocks(self,kind):
  lines=self.lines;headers=[];year='';section='PASS'
  for i,l in enumerate(lines):
   t=l['text'];ym=Y.fullmatch(t)
   if ym:year=ym[1];section=(ym[2] or 'PASS').upper()
   if 'LAS' in t.upper() and 'SUPPL' in t.upper():section='LAS'
   m=H.match(t)
   if m and (l['p']>=2 if kind=='acc-correction' else l['p']>=1):headers.append((i,next((int(x) for x in m.groups() if x),None),year,section))
  blocks=[]
  for k,(start,number,yr,sec) in enumerate(headers):
   end=headers[k+1][0] if k+1<len(headers) else len(lines);ls=lines[start:end]
   for j,l in enumerate(ls[1:],1):
    if Y.fullmatch(l['text']) or re.match(r'^(?:ERRATA|FIN DU|CORRIGÉ|CORRIGE|ANNALES CLASS|Ce document est|Félicitation|Si cette page est)',l['text'],re.I):ls=ls[:j];break
   blocks.append(dict(number=number,year=yr,section=sec,lines=ls,next=lines[end] if end<len(lines) else None))
  return blocks
 def render(self,ls,name,stop=None):
  if not ls:return []
  paths=[];first,last=ls[0],ls[-1]
  for p in range(first['p'],last['p']+1):
   page=self.pdf[p];top=max(14,first['y']-4) if p==first['p'] else 14;bottom=page.rect.height-34
   if p==last['p']:bottom=min(bottom,stop['y']-4 if stop and stop['p']==p else last['y2']+10)
   if bottom<=top:continue
   pix=page.get_pixmap(matrix=fitz.Matrix(1.65,1.65),clip=fitz.Rect(22,top,page.rect.width-20,bottom),alpha=False);f=ASSETS/f'{name}-p{p+1}.webp'
   Image.frombytes('RGB',(pix.width,pix.height),pix.samples).save(f,'WEBP',quality=86,method=3);paths.append(str(f.relative_to(OUT)))
  return paths

def parse(b,correction=False):
 ls=b['lines'];cut=next((i for i,l in enumerate(ls[1:],1) if C.search(l['text'])),len(ls)) if correction else len(ls)
 if correction and cut==len(ls):
  nums=[]
  for j,l in enumerate(ls):
   m=I.match(l['text'])
   if m:
    if int(m[1]) in nums and re.match(r'(?:OUI|NON|VRAI|FAUX)\b(?!\s*/)',m[2],re.I):cut=j;break
    nums.append(int(m[1]))
 qls=ls[:cut];cls=ls[cut:];items=[];marks=[]
 for i,l in enumerate(qls):
  m=I.match(re.sub(r'^l\.(?=\s*OUI)', '1.', l['text']))
  if m and not H.match(l['text']) and l['x']<260:marks.append((i,int(m[1]),m[2]))
 # Take the five consecutive item markers, allowing numeric values inside formulae.
 chosen=None
 for k in range(len(marks)):
  sub=[marks[k]]
  for candidate in marks[k+1:]:
   if candidate[1]==sub[-1][1]+1:sub.append(candidate)
   if len(sub)==5:chosen=sub;break
  if chosen:break
 if not chosen:
  letters=[]
  for i,l in enumerate(qls):
   lm=re.match(r'^([A-E])\s*[.)]\s*(.*)',l['text'])
   if lm:letters.append((i,ord(lm[1])-64,lm[2]))
  if [x[1] for x in letters]==[1,2,3,4,5]:chosen=letters
 if chosen:
  for j,(i,n,t) in enumerate(chosen):
   end=chosen[j+1][0] if j<4 else len(qls);items.append(clean(' '.join([t]+[l['text'] for l in qls[i+1:end]])))
  title=flat(' '.join(l['text'] for l in qls[:chosen[0][0]]));title=H.sub('',title).lstrip(' .:)-');nums=[x[1] for x in chosen]
 else:title=H.sub('',ls[0]['text']).lstrip(' .:)-');nums=None
 return dict(**{k:b[k] for k in ['number','year','section']},title=title,choices=items,itemNumbers=nums,qlines=qls,clines=cls,next=b['next'])
def key(ls):
 text='\n'.join(l['text'] for l in ls);pat=re.findall(r'(?<![A-Z])[ONVF]{5}(?![A-Z])',text)
 vals=[v.upper() in ('OUI','VRAI') for v in re.findall(r'(?:^|\n)\s*(?:\d{1,3}\s*[.)]\s*)?(OUI|NON|VRAI|FAUX)\b(?!\s*/)',text,re.I)]
 detailed=vals if len(vals)==5 else None;ans=[v in 'OV' for v in pat[0]] if pat else detailed
 return ans,detailed, bool(ans is not None and detailed is not None and ans!=detailed)
def sig(q):return norm(' '.join(q['choices'])) if q['choices'] else ''
def bank_grid(doc):
 grids={}
 for ls in doc.pages[1:3]:
  for l in ls:
   m=re.match(r'^(\d+)\s*\(\s*item',l['text'],re.I)
   if not m:continue
   right=sorted([z for z in ls if z['x']>l['x2']-4 and abs(z['y']-l['y'])<7 and re.fullmatch(r'[ONVF]{5}',z['text'])],key=lambda z:z['x'])
   if right:grids[int(m[1])]=[c in 'OV' for c in right[0]['text']]
 return grids
PAIRS=[('1',16,1),('2',5,3),('3',7,6),('4.1',8,19),('4.2',4,29),('4.3',36,17),('5',13,27),('6',14,28),('7',9,20),('9.1',11,22),('9.2',12,23),('10',10,21),('11',2,18),('12-13',15,24),('eb1',30,25),('eb2',31,26)]
if __name__=='__main__':
 qs=[];audit=[]
 for label,sid,cid in PAIRS:
  sd=Doc(sid);cd=Doc(cid);bs=[parse(b) for b in sd.blocks('bank')];cs=[parse(b,True) for b in cd.blocks('bank')];grid=bank_grid(cd);used=set()
  for ix,b in enumerate(bs,1):
   best=(-1,None)
   for j,c in enumerate(cs):
    if j in used:continue
    sim=difflib.SequenceMatcher(None,sig(b),sig(c),autojunk=False).ratio() if sig(b) and sig(c) else 0
    if sim>best[0]:best=(sim,j)
   sim,j=best;c=cs[j] if sim>=.74 else None
   if c:used.add(j)
   ans,det,conflict=key(c['clines']) if c else (None,None,False);gridans=grid.get(c['number']) if c else None
   if ans is None:ans=gridans
   qid=f'med-b{label}-q{ix:03}';q=dict(id=qid,subject='medicament',category='eb' if label.startswith('eb') else 'banques',sourceId='med-'+label,sourceLabel='Banque '+label if not label.startswith('eb') else 'Examen blanc '+label[-1],number=ix,originalNumber=b['number'],title=b['title'],text='\n'.join(l['text'] for l in b['qlines']),choices=b['choices'],itemNumbers=b['itemNumbers'],answers=ans,explanation='\n'.join(l['text'] for l in c['clines']) if c else '',correctionStatus='conflict' if conflict else 'source' if ans is not None else 'missing',sourceFile=sd.meta['file'],sourcePages=sorted({l['p']+1 for l in b['qlines']}),sourceDocument=sid,correctionDocument=cid if c else None,correctionSourceFile=cd.meta['file'] if c else None,correctionSourcePages=sorted({l['p']+1 for l in c['clines']}) if c else [],matchSimilarity=sim,sourceGrid=gridans,detailedAnswers=det,images=[],correctionImages=[],layout=b,correctionLayout=c)
   if RENDER:q['images']=sd.render(b['qlines'],qid,b['next']);q['correctionImages']=cd.render(c['clines'],qid+'-corr',c['next']) if c else []
   qs.append(q)
  audit.append(dict(label=label,subject=len(bs),correction=len(cs),matched=len(used),unmatched=[cs[j]['number'] for j in range(len(cs)) if j not in used]))
  print(audit[-1],flush=True)
 (W/'banks.json').write_text(json.dumps(qs,ensure_ascii=False));(W/'bank-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 print('Total',len(qs),'statuses',collections.Counter(q['correctionStatus'] for q in qs),'bad items',[q['id'] for q in qs if len(q['choices'])!=5])
