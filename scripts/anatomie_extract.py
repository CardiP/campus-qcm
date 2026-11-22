"""Import the supplied anatomy subjects without changing existing biology data.
Usage: python scripts/anatomie_extract.py SOURCE_DIR WORK_DIR [--render]
Requires PyMuPDF and Pillow. The work directory is intentionally outside public/.
"""
from pathlib import Path
import sys,json,re,hashlib,unicodedata,difflib,collections
import pymupdf as fitz
from PIL import Image
SRC=Path(sys.argv[1]);TMP=Path(sys.argv[2]);TMP.mkdir(parents=True,exist_ok=True)
OUT=Path(__file__).resolve().parents[1]/'public';ASSETS=OUT/'assets/anatomie';ASSETS.mkdir(parents=True,exist_ok=True)
RENDER='--render' in sys.argv
H=re.compile(r'^\s*[QǪ]uestions?\s*(?:n[°ºo]\s*)?(\d+)\b\s*[:.)–—-]?',re.I)
ITEM=re.compile(r'^\s*(\d{1,3})\s*[.)–—-]\s*(.*)')
CORR=re.compile(r'\bR[ée]ponses?\s*[:：]|\bCorrection\b|(?<![A-Z])[ONVF]{5}(?![A-Z])|^\s*\d{1,3}\s*[.)]\s*(?:OUI|NON|VRAI|FAUX)(?:\s*[,.:;!]|\s*$)',re.I)
def clean(s):
 s=re.sub(r'(?:TU)?TORAT\s+SANT[ÉE]\s+PARIS[-–]SACLAY|OUI\s*/\s*NON|Archives\s*20\d\d\s*[-–]\s*20\d\d\s*:?|FIN DU SUJET','',s,flags=re.I)
 return re.sub(r'\s+',' ',s).strip()
def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',clean(s)).encode('ascii','ignore').decode().lower())
class Doc:
 def __init__(self,path,iscorr=False):
  self.path=path;self.pdf=fitz.open(path);self.lines=[];self.bounds=[];self.iscorr=iscorr
  for p,page in enumerate(self.pdf):
   ls=[]
   for b in page.get_text('dict')['blocks']:
    for ln in b.get('lines',[]):
     if abs(ln.get('dir',(1,0))[1])>.15:continue
     s=''.join(x['text'] for x in ln['spans']).strip().replace('\u200b','')
     if s and not re.fullmatch(r'[\W_]+|\d{1,2}/\d{1,2}/\d{4}',s):ls.append(dict(p=p,x=ln['bbox'][0],y=ln['bbox'][1],y2=ln['bbox'][3],text=s))
   ls.sort(key=lambda x:(round(x['y']/2),x['x']));top=22;bottom=page.rect.height-30
   self.bounds.append((top,bottom))
   for ln in ls:
    if re.search(r'TUTORAT|Page\s*\d+\s*sur|UE6\s*ANATOMIE|Ce document est la propri',ln['text'],re.I) and not H.match(ln['text']) and not ITEM.match(ln['text']):continue
    if top<=ln['y']<bottom:self.lines.append(ln)
  # Banque 5 omits the question-39 heading in both PDFs; its five items are present.
  if re.search(r'n°5_banque_',path.name):
   for i,ln in enumerate(self.lines):
    if re.match(r'^191\s*[.)]\s*(?:1\s+est|$)',ln['text']):
     first=dict(ln);first['text']='Question 39 : À propos du schéma :'
     first['y']=self.bounds[ln['p']][0]+38;first['y2']=first['y']+1
     self.lines.insert(i,first);break
  self.headers=[]
  for i,ln in enumerate(self.lines):
   m=H.match(ln['text'])
   if m:self.headers.append(dict(idx=i,p=ln['p'],y=ln['y'],n=int(m[1])))
  self.blocks=[]
  for k,h in enumerate(self.headers):
   nxt=self.headers[k+1] if k+1<len(self.headers) else None
   lines=self.lines[h['idx']:nxt['idx'] if nxt else len(self.lines)]
   for j,ln in enumerate(lines[1:],1):
    if re.match(r'^(?:ERRATA|FIN DU SUJET|FIN DE LA CORRECTION|Ce document est|Félicitation)',ln['text'],re.I):lines=lines[:j];break
   cut=next((j for j,ln in enumerate(lines[1:],1) if CORR.search(ln['text'])),None) if iscorr else None
   qlines=lines[:cut] if cut is not None else lines;clines=lines[cut:] if cut is not None else []
   self.blocks.append(dict(number=h['n'],header=h,next=nxt,qlines=qlines,clines=clines,question='\n'.join(x['text'] for x in qlines),correction='\n'.join(x['text'] for x in clines)))
 def render(self,lines,name,stop=None):
  if not lines:return []
  paths=[];first,last=lines[0],lines[-1];figure_seen=False
  wants_figure=bool(re.search(r'sch[ée]ma|dessin|image|figure|structure\s+\d|repr[ée]sent|num[ée]ro|l[ée]gende|\ben\s*\(?\d', ' '.join(l['text'] for l in lines),re.I)) and not name.endswith('-corr')
  for p in range(first['p'],last['p']+1):
   page=self.pdf[p];top,bottom=self.bounds[p]
   if p==first['p']:top=max(top,first['y']-3)
   if p==last['p']:
    bottom=min(bottom,last['y2']+7)
    if stop and stop['p']==p:bottom=min(self.bounds[p][1],stop['y']-4)
    elif wants_figure:bottom=self.bounds[p][1]
   if bottom<=top:continue
   # Never extend a full-width question crop into the preceding question.
   # Figures crossing a text boundary are attached separately, without adjacent answers.
   figures=[]
   for im in page.get_image_info():
    r=fitz.Rect(im['bbox'])
    if r.width>page.rect.width*.94 or r.width<45 or r.height<40:continue
    if r.y1>top and r.y0<bottom:
     figure_seen=True
     if wants_figure and (r.y0<top or r.y1>bottom):figures.append(r)
   pix=page.get_pixmap(matrix=fitz.Matrix(1.7,1.7),clip=fitz.Rect(25,top,page.rect.width-22,bottom),alpha=False)
   path=ASSETS/f'{name}-p{p+1}.webp'
   Image.frombytes('RGB',[pix.width,pix.height],pix.samples).save(path,'WEBP',quality=87,method=3)
   paths.append(str(path.relative_to(OUT)))
   for fi,r in enumerate(figures):
    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=r,alpha=False)
    path=ASSETS/f'{name}-p{p+1}-figure{fi+1}.webp'
    Image.frombytes('RGB',[pix.width,pix.height],pix.samples).save(path,'WEBP',quality=90,method=3)
    paths.append(str(path.relative_to(OUT)))
  if wants_figure and not figure_seen:
   # Some banks ask several consecutive questions about one diagram. Reattach
   # only its image rectangle, never the preceding question or its correction.
   previous=[]
   for p in range(max(1,first['p']-1),first['p']+1):
    for im in self.pdf[p].get_image_info():
     r=fitz.Rect(im['bbox'])
     if 45<r.width<self.pdf[p].rect.width*.94 and r.height>40 and (p<first['p'] or r.y1<first['y']):previous.append((p,r))
   if previous:
    p,r=max(previous,key=lambda z:(z[0],z[1].y1));pix=self.pdf[p].get_pixmap(matrix=fitz.Matrix(2,2),clip=r,alpha=False)
    path=ASSETS/f'{name}-shared-figure.webp';Image.frombytes('RGB',[pix.width,pix.height],pix.samples).save(path,'WEBP',quality=90,method=3);paths.append(str(path.relative_to(OUT)))
  return paths

def items(b):
 ls=b['qlines'];first=next((int(ITEM.match(l['text'])[1]) for l in ls if ITEM.match(l['text']) and l['x']<130),None)
 if first is None:return None
 text=' '.join(l['text'] for l in ls if not re.match(r'^(?:20\d\d\s*[-–]|Sch[ée]ma|\d+$)',l['text']))
 marks=[];pos=0
 for n in range(first,first+5):
  m=re.search(r'(?<!\d)'+str(n)+r'\s*[.)–—-]\s*',text[pos:])
  if not m:return None
  marks.append((pos+m.start(),pos+m.end()));pos+=m.end()
 choices=[text[end:marks[i+1][0] if i<4 else len(text)].strip() for i,(start,end) in enumerate(marks)]
 choices=[clean(re.sub(r'^100\.\s*','',s)) for s in choices]
 title=H.sub('',text[:marks[0][0]]).strip()
 return title,list(range(first,first+5)),choices

def key(b):
 text=b['correction'];pat=re.findall(r'(?<![A-Z])[ONVF]{5}(?![A-Z])',text)
 det=re.findall(r'(?:^|\n)\s*(\d{1,3})\s*[.)]\s*(OUI|NON|VRAI|FAUX)\b',text,re.I)
 vals=[v.upper() in ['OUI','VRAI'] for _,v in det]
 if not det:vals=[v.upper() in ['OUI','VRAI'] for v in re.findall(r'(?:^|\n)\s*(OUI|NON|VRAI|FAUX)\b(?!\s*/)',text,re.I)]
 ds=vals if len(vals)==5 else None
 ans=[v in 'OV' for v in pat[0]] if pat else ds
 conflict=bool(ans is not None and ds is not None and ans!=ds)
 return ans,ds,conflict

def signature(b):
 it=items(b)
 return norm(' '.join(it[2]) if it else H.sub('',b['question']))

files=sorted(SRC.glob('*.pdf'));manifest=[]
for i,p in enumerate(files,1):
 manifest.append(dict(id=i,file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pages=len(fitz.open(p))))
(TMP/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
chapters={1:'Généralités et orientations',2:'Système osseux, articulaire et musculaire',3:'Os de la ceinture scapulaire et du bras',4:'Os de l’avant-bras et de la main',5:'Épaule et bras',6:'Coude et avant-bras',7:'Poignet et main',8:'Vaisseaux du membre thoracique',9:'Innervation du membre thoracique',10:'Os de la ceinture pelvienne et de la cuisse',11:'Os de la jambe et du pied',12:'Hanche et cuisse',13:'Genou et jambe',14:'Cheville et pied',15:'Vaisseaux du membre pelvien',16:'Innervation du membre pelvien',17:'Colonne vertébrale',18:'Paroi thoracique et médiastin',19:'Glande mammaire',20:'Appareil circulatoire',21:'Parois, cavités et valves cardiaques',22:'Vaisseaux et nerfs cardiaques',23:'Diaphragme',24:'Voies aériennes'}
pairs=[(n,next(i for i,p in enumerate(files,1) if re.search(fr'n°{n}_banque_sujet',p.name)),next(i for i,p in enumerate(files,1) if re.search(fr'n°{n}_banque_correction',p.name))) for n in range(1,25) if n not in [2,7]]+[(2,48,50),(7,49,51)]
pairs.sort();pairs += [('eb1',46,45),('td1',55,56)]
qs=[];audit=[]
for n,sid,cid in pairs:
 sub=Doc(files[sid-1]);cor=Doc(files[cid-1],True);used=set();corr_sigs=[signature(c) for c in cor.blocks];chapter=n if isinstance(n,int) else None
 for ix,b in enumerate(sub.blocks):
  sig=signature(b);candidates=[]
  exact=[j for j,ss in enumerate(corr_sigs) if j not in used and ss==sig]
  for j,c in enumerate(cor.blocks):
   if j in used or (exact and j not in exact):continue
   sim=difflib.SequenceMatcher(None,sig,corr_sigs[j],autojunk=False).ratio();candidates.append((sim+(0.025 if b['number']==c['number'] else 0),sim,j))
  best=max(candidates) if candidates else (0,0,-1);sim,j=best[1:];match=cor.blocks[j] if sim>=.75 else None
  if match:used.add(j)
  qid=f'anat-{n}-q{ix+1:03}';it=items(b);ans,det,conflict=key(match) if match else (None,None,False)
  q={'id':qid,'subject':'anatomie','category':'banques' if chapter else 'eb' if n=='eb1' else 'td','sourceId':f'anat-{n}','sourceLabel':f'Banque {n:02} · {chapters[n]}' if chapter else 'Examen blanc 1 · 2026–2027' if n=='eb1' else 'TD 1 · 2026–2027','number':ix+1,'originalNumber':b['number'],'chapter':('generalites' if n in [1,2] else 'membre-thoracique' if chapter and n<=9 else 'membre-pelvien' if chapter and n<=16 else 'tronc' if chapter and n<=19 else 'cardiorespiratoire' if chapter else 'transversal'),'topic':chapters[n] if chapter else 'À classer','title':it[0] if it else b['qlines'][0]['text'],'text':b['question'],'choices':it[2] if it else ['Voir la proposition '+c+' sur l’image' for c in 'ABCDE'],'itemNumbers':it[1] if it else None,'answers':None if conflict else ans,'sourceAnswers':ans,'detailedAnswers':det,'explanation':match['correction'] if match else '', 'images':[], 'correctionImages':[],'correctionStatus':'conflict' if conflict else 'source' if ans is not None else 'missing','sourceFile':sub.path.name,'sourcePages':sorted({x['p']+1 for x in b['qlines']}),'correctionSourceFile':cor.path.name if match else None,'correctionSourcePages':sorted({x['p']+1 for x in match['clines']}) if match else [],'matchSimilarity':round(sim,4)}
  if RENDER:
   q['images']=sub.render(b['qlines'],qid,b['next']);q['correctionImages']=cor.render(match['clines'],qid+'-corr',match['next']) if match else []
  qs.append(q)
 print('Processed',n,len(sub.blocks),'questions',flush=True)
 audit.append({'source':n,'subjectQuestions':len(sub.blocks),'correctionQuestions':len(cor.blocks),'matched':len(used),'unmatchedCorrectionNumbers':[c['number'] for j,c in enumerate(cor.blocks) if j not in used]})
(TMP/'banks.json').write_text(json.dumps(qs,ensure_ascii=False,indent=2));(TMP/'bank-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
for x in audit:print(x)
print('Total',len(qs),'statuses',collections.Counter(q['correctionStatus'] for q in qs),'bad items',[q['id'] for q in qs if not q['itemNumbers']])
