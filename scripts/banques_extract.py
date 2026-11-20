"""Extract source-faithful QCM images and answer keys from the supplied PDFs.
Run with pymupdf + Pillow. No generated scientific answers are introduced.
"""
import json, re, unicodedata, difflib, collections, io
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'sante-qcm/public'
ASSETS=OUT/'assets/banques';ASSETS.mkdir(parents=True,exist_ok=True)
TMP=ROOT/'sante-qcm/tmp';TMP.mkdir(exist_ok=True)

def norm(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub(r'[^a-z0-9]','',re.sub(r'\b(?:oui|non|question|reponse|correction)\b','',s))
def find(folder,pat):
 ps=list((ROOT/folder).rglob(pat));assert len(ps)==1,(folder,pat,ps);return ps[0]
CONFIG=[
 ('acides-amines','Acides aminés','structurale','*AA-2025.pdf','*AA-2025.pdf'),
 ('architecture','Architecture des protéines','structurale','2425*','2425*'),
 ('methodes','Méthodes d’étude','structurale','*Methodes*','*Methodes*'),
 ('structure-fonction','Structure-fonction','structurale','BANQUE-3.pdf','CORRECTION-BANQUE-3.pdf'),
 ('genome','Génome','biomol','*introduction*','*introduction*'),
 ('acides-nucleiques','Acides nucléiques','biomol','*Acides-Nucleiques*','*Acides-Nucleiques*'),
 ('techniques-bm','Techniques de biologie moléculaire','biomol','*techniqueBM*','*techniquesBM*'),
 ('replication','Réplication','biomol','*replication*','*replication*'),
 ('transcription','Transcription','biomol','*transcription*','*transcription*'),
 ('traduction','Traduction','biomol','*TRADUCTION*','*TRADUCTION*'),
 ('regulation','Régulation','biomol','*regulation*','*regulation*'),
 ('enzymologie-1','Enzymologie 1','enzymologie','*enzymo1*','*enzymo1*'),
 ('enzymologie-2','Enzymologie 2','enzymologie','*Enzymologie2*','*Enzymologie2*'),
 ('enzymologie-3','Enzymologie 3','enzymologie','*15*','*15*'),
 ('vue-metabolisme',"Vue d’ensemble du métabolisme",'metabolisme','*densembke*','*densemble*'),
 ('krebs','Cycle de Krebs','metabolisme','*Krebs*','*Krebs*'),
 ('glycolyse','Glycolyse','metabolisme','BU-Glycolyse*','BU-Correction-Glycolyse*'),
 ('lipides','Métabolisme des lipides','metabolisme','*transport*','*transport*'),
 ('biosynthese','Biosynthèse des acides gras','metabolisme','*Biosynthese*','*biosynthese*'),
 ('interrelations','Interrelations métaboliques','metabolisme','*interrelation*','*Interrelation*'),
]
H=re.compile(r'^\s*[QǪ]uestions?\s*(\d+(?:\s+\d)?)(?=\s*[:.)–—-]|\s*\(|\s*$)',re.I)

class Doc:
 def __init__(self,path,iscorr=False):
  self.path=path;self.pdf=fitz.open(path);self.lines=[];self.bounds=[];self.iscorr=iscorr;self._images={}
  for p,page in enumerate(self.pdf):
   arr=[]
   for b in page.get_text('dict')['blocks']:
    for ln in b.get('lines',[]):
     s=''.join(x['text'] for x in ln['spans']).strip()
     if s:arr.append({'p':p,'x':ln['bbox'][0],'y':ln['bbox'][1],'y2':ln['bbox'][3],'text':s})
   arr.sort(key=lambda x:(round(x['y']/2),x['x']))
   merged=[]
   for ln in arr:
    if merged and abs(ln['y']-merged[-1]['y'])<3.4:
     merged[-1]['text']+=' '+ln['text'];merged[-1]['y2']=max(merged[-1]['y2'],ln['y2'])
    else:merged.append(ln.copy())
   # Header and footer locations vary. Clip just inside them.
   top=65;bottom=page.rect.height-55
   for ln in merged:
    if re.search(r'TUTORAT|Page\s*\d+\s*sur|UE1\s*Biochimie|UE1 BIOCHIMIE|UEN NOM',ln['text'],re.I):
     if ln['y']<110:top=max(top,ln['y2']+3)
     elif ln['y']>page.rect.height-100:bottom=min(bottom,ln['y']-5)
   self.bounds.append((top,bottom))
   self.lines.extend([ln for ln in merged if top<=ln['y']<bottom])
  self.lines.sort(key=lambda ln:(ln['p'],ln['y'],ln['x']))
  self.headers=[]
  for i,ln in enumerate(self.lines):
   m=H.match(ln['text'])
   if m:self.headers.append({'idx':i,'p':ln['p'],'y':ln['y'],'n':int(m[1].replace(' ','')),'head':ln['text']})
  self.blocks=[]
  for k,h in enumerate(self.headers):
   end=self.headers[k+1]['idx'] if k+1<len(self.headers) else len(self.lines)
   lines=self.lines[h['idx']:end]
   # End before errata, closing matter and repeated cover pages.
   for j,ln in enumerate(lines[1:],1):
    if re.match(r'^(?:ERRATA|FIN DU SUJET|FIN DE LA CORRECTION|Ce document est)',ln['text'],re.I):lines=lines[:j];break
   # Sometimes last source page is completely empty; only actual content pages survive.
   txt='\n'.join(x['text'] for x in lines)
   cut=self.correction_start(lines) if iscorr else None
   qlines=lines[:cut] if cut is not None else lines
   clines=lines[cut:] if cut is not None else []
   if iscorr and cut is None and lines:
    # Several tutorat corrections are pasted raster boxes, absent from text extraction.
    lim=self.headers[k+1] if k+1<len(self.headers) else None
    for pp in range(lines[0]['p'],lines[-1]['p']+1):
     page=self.pdf[pp]
     for image in [None]:
      for rect in self.image_rects(pp):
       before=[ln for ln in lines if ln['p']<pp or ln['y2']<rect.y0+3]
       after=[ln for ln in lines if ln['p']>pp or ln['y']>rect.y1-3]
       # A correction box follows all five propositions, unlike a question diagram.
       bt='\n'.join(ln['text'] for ln in before)
       if rect.width>220 and rect.height>45 and len(re.findall(r'OUI\s*/\s*NON',bt,re.I))>=5 and (not lim or pp<lim['p'] or rect.y1<lim['y']+2):
        clines=[{'p':pp,'x':rect.x0,'y':rect.y0,'y2':rect.y1,'text':'Correction du document source (image).'}]
        qlines=before
        break
      if clines:break
     if clines:break
   self.blocks.append(dict(header=h,lines=lines,qlines=qlines,clines=clines,text=txt,question='\n'.join(x['text'] for x in qlines),index=k))
 def image_rects(self,p):
  if p not in self._images:self._images[p]=[fitz.Rect(im['bbox']) for im in self.pdf[p].get_image_info()]
  return self._images[p]
 def correction_start(self,lines):
  for i,ln in enumerate(lines[1:],1):
   s=ln['text']
   if re.search(r'\b(?:R[ée]ponse|Correction)\s*:',s,re.I):return i
   if re.search(r'(?<![A-Z])[ONVF]{5}(?![A-Z])',s):return i
   if re.match(r'^\s*\d{1,3}\s*[.)]\s*(?:OUI|NON|VRAI|FAUX)(?!\s*/)',s,re.I):return i
  return None
 def render(self,lines,name,stop=None):
  if not lines:return []
  first,last=lines[0],lines[-1];pages=range(first['p'],last['p']+1);out=[]
  for p in pages:
   page=self.pdf[p];top,bottom=self.bounds[p]
   if p==first['p']:top=max(top,first['y']-3)
   # Include figures between last text and boundary. Explicit next question/correction bounds win.
   if p==last['p']:
    bottom=min(bottom,last['y2']+8)
    if stop and stop['p']==p:bottom=min(self.bounds[p][1],stop['y']-5)
   if bottom-top<5:continue
   left,right=46,page.rect.width-37
   for entry in [None]:
    for ir in self.image_rects(p):
     if ir.width<page.rect.width*.94 and ir.y1>top and ir.y0<bottom:
      left=min(left,max(0,ir.x0-3));right=max(right,min(page.rect.width,ir.x1+3))
      if ir.y0>=top-55:top=min(top,ir.y0-2)
      if (not stop or p<stop['p'] or ir.y1<stop['y']-2):bottom=max(bottom,min(self.bounds[p][1],ir.y1+3))
   rect=fitz.Rect(left,top,right,bottom)
   path=ASSETS/f'{name}-{p+1}.webp'
   if path.exists() and left==46 and right==page.rect.width-37 and not any(x in name for x in ('lipides','td-1','eb-2','architecture')):
    out.append(str(path.relative_to(OUT)));continue
   pix=page.get_pixmap(matrix=fitz.Matrix(1.8,1.8),clip=rect,alpha=False)
   im=Image.open(io.BytesIO(pix.tobytes('png')))
   path=ASSETS/f'{name}-{p+1}.webp';im.save(path,'WEBP',quality=86,method=2)
   out.append(str(path.relative_to(OUT)))
  return out

def answer_info(block):
 text='\n'.join(ln['text'] for ln in block['clines'])
 patterns=re.findall(r'(?<![A-Z])[ONVF]{5}(?![A-Z])',text)
 patterns=[p.translate(str.maketrans('VF','ON')) for p in patterns]
 labels=[]
 for m in re.finditer(r'(?:^|\n)\s*(\d{1,3})\s*[.)]\s*(OUI|NON|VRAI|FAUX)(?!\s*/)',text,re.I):
  labels.append((int(m[1]),m[2].upper() in ('OUI','VRAI')))
 detailed=None
 if len(labels)>=5:
  # Take first 5 distinct propositions only; duplicate discussion ignored.
  uniq=[]
  for n,v in labels:
   if n not in [x[0] for x in uniq]:uniq.append((n,v))
  if len(uniq)==5:detailed=[v for n,v in uniq]
 ans=[c=='O' for c in patterns[0]] if patterns else detailed
 if patterns and detailed is not None and re.search('inexact',block['question'],re.I) and ans==[not x for x in detailed]:detailed=ans
 conflict=bool(patterns and detailed is not None and ans!=detailed)
 return (None if conflict else ans),('conflict' if conflict else 'source' if ans is not None else 'missing'),text

def cleanq(t):
 t=re.sub(r'Question\s*\d+','',t,flags=re.I)
 t=re.sub(r'\d+\s*[.)]','',t)
 return norm(t)

def match_blocks(sub,corr):
 used=set();matches={};scores={}
 for i,b in enumerate(sub.blocks):
  s=cleanq(b['question']);candidates=[]
  for j,c in enumerate(corr.blocks):
   if j in used:continue
   cs=cleanq(c['question']);sim=difflib.SequenceMatcher(None,s,cs,autojunk=False).ratio()
   # Very short generic heading should not match alone.
   candidates.append((sim + (.04 if i == j else 0),j))
  if candidates:
   sim,j=max(candidates)
   sim -= (.04 if i == j else 0)
   if sim>=.60:
    matches[i]=j;scores[i]=sim;used.add(j)
 return matches,scores,used

def classify(text):
 low=text.lower(); choices=[
 ('biomol','Techniques de biologie moléculaire',['pcr','séquenç','sanger','amorce','restriction']),
 ('biomol','Réplication',['réplication','réparation','polymérase']),
 ('biomol','Traduction',['traduction','ribosom','codon','trna','arnt']),
 ('biomol','Transcription',['transcription','promoteur']),
 ('biomol','Régulation',['chromatine','méthylation','régulation de l’expression','histone']),
 ('biomol','Acides nucléiques',['adn','arn','nuclé','bases azotées']),
 ('enzymologie','Enzymologie 2',['michaelis','vmax','vitesse initiale','inhibiteur','km','cinétique']),
 ('enzymologie','Enzymologie 1',['enzyme','catalyse','cofacteur']),
 ('metabolisme','Glycolyse',['glycolyse','glucose','glycogène','néoglucogenèse']),
 ('metabolisme','Cycle de Krebs',['krebs','respiratoire','phosphorylation oxydative']),
 ('metabolisme','Métabolisme des lipides',['lipide','lipoproté','chylomicron','acide gras','cétog','lipogen']),
 ('structurale','Structure-fonction',['hémoglob','myoglob','bohr','hb']),
 ('structurale','Méthodes d’étude',['chromatograph','électrophor','trypsine','chymotrypsine','edman','sds','cnbr']),
 ('structurale','Architecture des protéines',['hélice','structure','collag','prion','ramachandran','feuillet','liaison peptid']),
 ('structurale','Acides aminés',['acide amin',' aa ','pka','titration','proline','tyrosine'])]
 best=max(choices,key=lambda z:sum(low.count(w) for w in z[2]));return best[:2]

def get_items(text):
 nums=re.findall(r'(?:^|\n)\s*(\d{1,3})\s*[.)]\s*(?:OUI\s*/\s*NON)?',text)
 if len(nums)==5:return list(map(int,nums))
 return None

allq=[];report=[];detail=[]

def process(sid,label,chapter,subpath,corrpath,category='banques'):
 sub=Doc(subpath);corr=Doc(corrpath,True);matches,scores,used=match_blocks(sub,corr)
 print(sid,len(sub.blocks),len(corr.blocks),'matched',len(matches),flush=True)
 # Grids only safe when numbering is unique throughout correction document.
 grid={}
 if True:
  full='\n'.join(p.get_text(sort=True) for p in corr.pdf)
  for m in re.finditer(r'(\d{1,2})\s*\(\s*item[^)]*\)\s*([ONVF]{5})\b',full,re.I):grid[int(m[1])]=[x in 'OV' for x in m[2].upper()]
 rows=[]
 for i,b in enumerate(sub.blocks):
  c=corr.blocks[matches[i]] if i in matches else None
  qid=f'{category}-{sid}-{i+1}'
  nexthead=sub.headers[i+1] if i+1<len(sub.headers) else None
  imgs=sub.render(b['qlines'],qid, nexthead)
  ans,status,expl=answer_info(c) if c else (None,'missing','')
  if c and status=='missing' and (c['index']+1) in grid:ans=grid[c['index']+1];status='source'
  if c and status=='source' and (c['index']+1) in grid and ans!=grid[c['index']+1]:ans=None;status='conflict'
  ci=[]
  if c and c['clines']:
   ci=corr.render(c['clines'],qid+'-correction',corr.headers[c['index']+1] if c['index']+1<len(corr.headers) else None)
  ch,tp=(chapter,label) if chapter else classify(b['question'])
  head=re.sub(r'^\s*Question\s*\d+\s*(?:\([^)]*\))?\s*:?', '', b['header']['head'],flags=re.I).strip()
  row={'id':qid,'category':category,'sourceId':f'{category}-{sid}','sourceLabel':label,'number':i+1,'originalNumber':b['header']['n'],'chapter':ch,'topic':tp,'title':head or f'Question {i+1}','text':b['question'],'images':imgs,'choices':['A','B','C','D','E'],'answers':ans,'explanation':expl,'correctionImages':ci,'correctionStatus':status,'sourcePages':sorted(set(x['p']+1 for x in b['qlines'])),'sourceFile':str(subpath.relative_to(ROOT))}
  nums=get_items(b['question'])
  if nums:row['itemNumbers']=nums
  if c:row['correctionSourceFile']=str(corrpath.relative_to(ROOT));row['correctionSourcePages']=sorted(set(x['p']+1 for x in c['lines']));row['matchScore']=round(scores[i],3)
  rows.append(row)
 # Corrections with genuinely different/new questions need source-safe boundary.
 for j,c in enumerate(corr.blocks):
  if j in used:continue
  # A low match can simply reflect substantial wording changes: report for manual audit.
  best=max((difflib.SequenceMatcher(None,cleanq(c['question']),cleanq(s['question']),autojunk=False).ratio(),i) for i,s in enumerate(sub.blocks))
  detail.append({'source':sid,'unmatchedCorrection':j+1,'number':c['header']['n'],'bestScore':round(best[0],3),'bestSubject':best[1]+1,'question':c['question'][:900]})
  if best[0]>.48 or re.search(r'Item \d+',c['question']):continue
  if not c['clines']:continue
  qid=f'{category}-{sid}-complement-{j+1}'
  ans,status,expl=answer_info(c)
  if status=='missing' and c['header']['n'] in grid:ans=grid[c['header']['n']];status='source'
  if status=='source' and c['header']['n'] in grid and ans!=grid[c['header']['n']]:ans=None;status='conflict'
  ch,tp=(chapter,label) if chapter else classify(c['question'])
  row={'id':qid,'category':category,'sourceId':f'{category}-{sid}','sourceLabel':label,'number':len(rows)+1,'originalNumber':c['header']['n'],'chapter':ch,'topic':tp,'title':'Complément du corrigé · '+re.sub(r'^Question\s*\d+\s*:?','',c['header']['head'],flags=re.I).strip(),'text':c['question'],'images':corr.render(c['qlines'],qid,c['clines'][0]),'choices':['A','B','C','D','E'],'answers':ans,'explanation':expl,'correctionImages':corr.render(c['clines'],qid+'-correction',corr.headers[j+1] if j+1<len(corr.headers) else None),'correctionStatus':status,'sourcePages':sorted(set(x['p']+1 for x in c['qlines'])),'sourceFile':str(corrpath.relative_to(ROOT))}
  nums=get_items(c['question'])
  if nums:row['itemNumbers']=nums
  rows.append(row)
 allq.extend(rows)
 report.append({'source':sid,'label':label,'subjectQuestions':len(sub.blocks),'correctionQuestions':len(corr.blocks),'totalPublished':len(rows),'matched':len(matches),'statuses':dict(collections.Counter(q['correctionStatus'] for q in rows)),'unmatchedSubject':[i+1 for i in range(len(sub.blocks)) if i not in matches],'lowMatches':[{ 'subject':i+1,'correction':matches[i]+1,'score':round(s,3)} for i,s in scores.items() if s<.85]})

for sid,label,chapter,sp,cp in CONFIG:
 subject=find('QCM/SUJETS',sp);correction=find('QCM/CORRECTION',cp)
 if sid=='enzymologie-3':subject,correction=correction,subject
 process(sid,label,chapter,subject,correction)
process('eb-1','EB 1 · 2025–2026',None,find('EB','EB-1-sujet*'),find('EB','EB-1-CORRECTION*'),'eb')
process('eb-2','EB 2 · 2025–2026',None,find('EB','*2-sujet*'),find('EB','*EB2-CORRECTION*'),'eb')
process('td-1','TD 1 · 2025–2026',None,find('TD','*sujet*'),find('TD','*correction*'),'td')
(OUT/'data/banques.json').write_text(json.dumps(allq,ensure_ascii=False,indent=2))
(TMP/'banques-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(TMP/'banques-unmatched.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2))
print('TOTAL',len(allq),collections.Counter(q['correctionStatus'] for q in allq))
