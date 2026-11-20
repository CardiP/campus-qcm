"""Extract faithfully cropped annale questions; never infer an answer key.
Run with PyMuPDF and Pillow. The scanned 2024 paper requires annales_ocr.swift first.
"""
import json,re,unicodedata
from pathlib import Path
import pymupdf as pdf
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[2]
SITE=ROOT/'sante-qcm'
OUT=SITE/'public/assets/annales'
OUT.mkdir(parents=True,exist_ok=True)

def norm(s):
 return ''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c))

def header(s):
 return bool(re.match(r'^[QO]UEST[ILT1I]O[NM](?:\d+)?[.:]',re.sub(r'\s+','',s),re.I))

def native_lines(page):
 lines=[]
 for b in page.get_text('dict')['blocks']:
  for l in b.get('lines',[]):
   t=''.join(s['text'] for s in l['spans']).strip()
   r=pdf.Rect(l['bbox'])*page.rotation_matrix
   if t:lines.append({'text':t,'bbox':list(r)})
 return sorted(lines,key=lambda l:(round(l['bbox'][1]/3),l['bbox'][0]))

def topic_for(title,chapter):
 t=norm(title)
 if chapter=='structurale':
  if any(x in t for x in ['titration','acide amine']): return 'Acides aminés'
  if any(x in t for x in ['oxygene','hemoglob','structure-activite']): return 'Relations structure-fonction'
  if any(x in t for x in ['analyse','methodes','melange','octapeptide designe','peptides (a)','structures peptidiques']): return 'Méthodes d’étude des protéines'
  return 'Structure des protéines'
 if chapter=='biomol':
  if 'genome' in t:return 'Introduction au génome'
  if 'nucleique' in t:return 'Acides nucléiques'
  if any(x in t for x in ['replication','reparation']):return 'Réplication et réparation'
  if any(x in t for x in ['pcr','sanger','sequencage','techniques']):return 'Techniques de biologie moléculaire'
  if 'regulation' in t:return 'Régulation de l’expression des gènes'
  if any(x in t for x in ['traduction','vaccin']):return 'Traduction'
  return 'Transcription'
 if chapter=='enzymologie':
  if any(x in t for x in ['allost','regulation']):return 'Enzymologie 3'
  if any(x in t for x in ['michael','mlchael','lineweaver','inhibiteur','modulations']):return 'Enzymologie 2'
  return 'Enzymologie 1'
 if any(x in t for x in ['glycogene','neoglucogenese']):return 'Néoglucogenèse et glycogène'
 if any(x in t for x in ['krebs','respiratoire','cycle de l']):return 'Cycle de Krebs et phosphorylation oxydative'
 if any(x in t for x in ['biosynthese','corps cetonique']):return 'Biosynthèse des acides gras et cétogenèse'
 if any(x in t for x in ['lipoproteine','lipides','cholesterol','oxydation des acides gras']):return 'Métabolisme et transport des lipides'
 if any(x in t for x in ['glycol','glucokinase','hexokinase','glucides']):return 'Glycolyse'
 if any(x in t for x in ['organe','glucose-6-phosphatase']):return 'Interrelations métaboliques'
 return 'Vue d’ensemble du métabolisme'

def chapter_for(year,number,title):
 if year=='2020-2021':
  if number<=8:return 'biomol'
  if number<=14 or number==16:return 'structurale'
  if number==15 or number>=21:return 'metabolisme'
  return 'enzymologie'
 if number<=8:return 'structurale'
 if number<=16:return 'biomol'
 if number<=20:return 'enzymologie'
 return 'metabolisme'

def make():
 questions=[];report=[]
 existing_path=SITE/'public/data/annales.json'
 existing={q['id']:q for q in json.loads(existing_path.read_text())} if existing_path.exists() else {}
 for file in sorted((ROOT/'ANNALES').glob('*.pdf')):
  year=file.stem.replace(' ','-');doc=pdf.open(file)
  if year=='2024-2025':
   op=SITE/'tmp/annales-2024-ocr.json'
   if not op.exists():continue
   pages=json.loads(op.read_text());lines=[sorted(x['lines'],key=lambda l:(round(l['bbox'][1]/3),l['bbox'][0])) for x in pages]
  else:lines=[native_lines(p) for p in doc]
  heads=[]
  for pi,ls in enumerate(lines):
   if pi==0:continue
   for l in ls:
    if header(l['text']):heads.append((pi,l['bbox'][1],l['text']))
  heads.sort()
  assert len(heads)==(30 if year=='2020-2021' else 25),(year,len(heads))
  rendered={}
  for qi,(pi,top,title) in enumerate(heads):
   number=qi+1
   ep,ey,_=heads[qi+1] if qi+1<len(heads) else (len(doc)-1,doc[-1].rect.height-40,'')
   paths=[];texts=[];sourcepages=[]
   for idx in range(pi,ep+1):
    page=doc[idx];start=top-5 if idx==pi else 22
    end=ey-5 if idx==ep and qi+1<len(heads) else page.rect.height-38
    # Remove source footer/page number from crop, without removing original scientific content.
    feet=[l['bbox'][1] for l in lines[idx] if 'ce document' in norm(l['text']) or 'reproduction' in norm(l['text'])]
    if feet:end=min(end,min(feet)-14)
    if end<=start+8:continue
    segment=[l for l in lines[idx] if start<=l['bbox'][1]<end]
    useful=[l for l in segment if not re.match(r'^\d+$',l['text']) and norm(l['text']) not in ['biochimie structurale','enzymologle','biochimle metabolique']]
    if not useful:continue
    page_numbers=[l['bbox'][1] for l in segment if re.match(r'^\d+$',l['text']) and l['bbox'][1]>page.rect.height*0.88]
    if page_numbers:end=min(end,min(page_numbers)-5)
    if idx not in rendered:
     pix=page.get_pixmap(matrix=pdf.Matrix(2.5,2.5),alpha=False)
     rendered[idx]=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
    im=rendered[idx];sx=im.width/page.rect.width;sy=im.height/page.rect.height
    crop=im.crop((int(22*sx),int(max(0,start)*sy),int((page.rect.width-22)*sx),int(end*sy)))
    # White margin trimming keeps the original diagram and proposition geometry intact.
    mask=crop.convert('L').point(lambda p:255 if p<165 else 0)
    box=mask.getbbox()
    if not box:continue
    if box[3]-box[1]<8:continue
    pad=12;box=(max(0,box[0]-pad),max(0,box[1]-pad),min(crop.width,box[2]+pad),min(crop.height,box[3]+pad))
    crop=crop.crop(box)
    name=f'{year}-q{number:02d}-{len(paths)+1}.webp';crop.save(OUT/name,'WEBP',quality=88,method=6)
    paths.append('assets/annales/'+name);sourcepages.append(idx+1)
    texts.extend(l['text'] for l in lines[idx] if start<=l['bbox'][1]<end and not re.match(r'^\d+$',l['text']))
   clean=re.sub(r'^[QO]\s*UEST[ILT1I]O[NM]\s*(?:\d+)?[\s.:]*','',title,flags=re.I).strip()
   clean=clean.replace('QU ESTION:','').replace('Strudure','Structure').replace('Mlchaells','Michaelis')
   chapter=chapter_for(year,number,clean)
   q={'id':f'annale-{year}-q{number}','category':'annales','sourceId':'annale-'+year,'sourceLabel':'Annale '+year.replace('-','–'),'number':number,'chapter':chapter,'topic':topic_for(clean,chapter),'title':clean,'text':'\n'.join(texts),'images':paths,'choices':['A','B','C','D','E'],'itemNumbers':list(range((number-1)*5+1,number*5+1)),'answers':None,'explanation':'','correctionImages':[],'correctionStatus':'missing','sourcePages':sourcepages,'sourceFile':str(file.relative_to(ROOT))}
   if q['id'] in existing:
    for key in ['answers','explanation','courseReferences','externalReferences','correctionStatus','correctionImages']:
     if key in existing[q['id']]:q[key]=existing[q['id']][key]
   questions.append(q)
  report.append({'source':str(file.relative_to(ROOT)),'questions':len(heads),'assets':sum(len(q['images']) for q in questions if q['sourceId']=='annale-'+year)})
 (SITE/'public/data/annales.json').write_text(json.dumps(questions,ensure_ascii=False,indent=2))
 (SITE/'tmp/annales-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))
 print('Questions:',len(questions),'Assets:',sum(len(q['images']) for q in questions))
if __name__=='__main__':make()
