"""Build the deduplicated medicine bank, source crops and import audit.
Usage: python scripts/medicament_build.py DOWNLOADS WORK_DIR [--render]
"""
import json,re,collections,sys
from pathlib import Path
import medicament_extract as m
W=m.W;ROOT=m.ROOT
qs=json.loads((W/'unique.json').read_text());occ=json.loads((W/'prepared.json').read_text());by={q['id']:q for q in occ}
for q in json.loads((W/'supplemental.json').read_text())['questions']:by[q['id']]=q
old={q['id']:q for q in json.loads((m.OUT/'data/medicament.json').read_text())} if '--reuse-assets' in sys.argv else {}
curated=json.loads((ROOT/'scripts/data/medicament-corrections.json').read_text())
TOPICS={
'1':('cadre','Présentation du médicament',[103]),'2':('cadre','Définition juridique',[104]),'3':('cadre','Catégories de médicaments et produits de santé',[105]),
'4.1':('conception','Propriétés physico-chimiques des principes actifs',[106]),'4.2':('galenique','Excipients',[107]),'4.3':('galenique','Conditionnement',[108]),
'5':('conception','Sources naturelles de molécules actives',[109]),'6':('conception','Conception et synthèse de molécules actives',[110]),
'7':('pharmacologie','Pharmacodynamique',[111,112]),'9.1':('pharmacologie','Absorption et distribution',[113]),'9.2':('pharmacologie','Métabolisme, élimination et interactions',[114]),
'10':('pharmacologie','Pharmacocinétique quantitative',[93,94,95]),'11':('pharmacologie','Variabilité de la réponse aux médicaments',[96]),
'12-13':('galenique',"Voies d’administration et formes orales",[97,98]),'14':('galenique','Voies parentérales',[99]),'15':('galenique','Voies topiques',[100]),
'16':('cadre','Prescription et délivrance',[101,102]),'cycle':('conception','Cycle de vie du médicament',[116]),'bio':('conception','Médicaments biologiques',[105,109]),
'grossesse':('pharmacologie','Médicaments, grossesse et allaitement',[96]),'interactions':('pharmacologie','Interactions médicamenteuses',[96,114])}
DOC_TOPIC={76:'10',77:'2',78:'cycle',79:'3',80:'4.1',81:'3',82:'4.2',83:'5',84:'4.3',85:'9.2',86:'7',87:'grossesse',88:'interactions',89:'11',90:'12-13',91:'15',92:'bio',51:'16'}
for a,b in {50:77,47:79,49:81,44:80,42:82,53:83,38:85,39:86,40:76}.items():DOC_TOPIC[a]=DOC_TOPIC[b]
for label,sid,cid in m.PAIRS:
 if not label.startswith('eb'):DOC_TOPIC[sid]=label
ANNUAL_OVERRIDES={'med-d034-q004':'16','med-d034-q005':'16','med-d034-q006':'16','med-d034-q013':'12-13','med-d034-q018':'14','med-d035-q014':'12-13','med-d035-q016':'14','med-d035-q017':'14','med-d032-q016':'14','med-d032-q017':'14','med-d033-q017':'14','med-d037-q016':'14','med-d037-q017':'14','med-d035-q026':'10'}
def classification(q):
 if q['id'] in ANNUAL_OVERRIDES:return TOPICS[ANNUAL_OVERRIDES[q['id']]]
 ds=[x['document'] for x in q['occurrences'] if x['document'] in DOC_TOPIC]
 if ds:return TOPICS[DOC_TOPIC[ds[0]]]
 t=m.norm(q['title']+' '+' '.join(q['choices']))
 for key,pattern in [('16','prescri|dispens|stup[eé]fi|ordonnance'),('10','demivie|dose.dattaque|pousse.seringue|pharmacocinetiquequantitative'),('7','recepteur|ligand|cyclooxygenase|p[Dd]2'),('14','parenteral|sterilis|injectable|autoclav'),('12-13','comprime|gelule|voieorale|liberation'),('4.2','excipient|sorbitol|distillation|osmoseinverse'),('4.3','conditionnement|boitage'),('6','hemisynthese|pharmacophore|criblage|synthese'),('5','naturelle|alcaloide|extraction'),('11','variabilite|observance|age|creatinine'),('9.2','excretion|metabolis|interaction'),('3','generique|specialite|cosmetique'),('2','juridique|definition|upjohn')]:
  if re.search(pattern,t,re.I):return TOPICS[key]
 return TOPICS['1']
REFS={
'biologie':dict(label='EMA — Médicaments biologiques et biosimilaires',url='https://www.ema.europa.eu/en/human-regulatory-overview/biosimilar-medicines-overview'),
'pk':dict(label='EMA — Pharmacocinétique des protéines thérapeutiques',url='https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-clinical-investigation-pharmacokinetics-therapeutic-proteins_en.pdf'),
'genique':dict(label='Inserm — Thérapie génique',url='https://www.inserm.fr/dossier/therapie-genique/'),
'hybridome':dict(label='Köhler — Conférence Nobel : anticorps monoclonaux',url='https://www.nobelprize.org/uploads/2018/06/kohler-lecture.pdf'),
'insuline':dict(label='FDA — Évaluation de l’insuline humaine recombinante',url='https://www.accessdata.fda.gov/drugsatfda_docs/nda/2019/208157Orig1s000PharmR.pdf'),
'adn':dict(label='Biologie moléculaire — Clonage et ADN recombinant',url='https://www.ncbi.nlm.nih.gov/books/NBK26837/')}
def cours(ids):return [dict(file=m.META[i]['file'],label=Path(m.META[i]['file']).name.removesuffix('.pdf')) for i in ids]
# Crops for shared data preceding Q headers. Coordinates are PDF points, not page images.
shared={
 'med-d037-q018':(37,8,222,480),'med-d037-q019':(37,8,222,480),
 'med-d086-q038':(86,16,116,168),'med-d086-q039':(86,16,116,168),
 'med-d086-q042':(86,17,266,379),'med-d086-q043':(86,18,126,247),'med-d086-q044':(86,18,126,247)}
TITLES={'med-d037-q018':'Profils pharmacologiques des molécules S, A, C, L et Y','med-d037-q019':'Puissance, affinité et efficacité du ligand L',
'med-beb2-q013':'Sources de molécules actives : hit et lead','med-beb2-q021':'Hémisynthèse de molécules actives','med-d083-q036':'Hit, prodrogue et pharmacophore','med-d083-q037':'Méthodes de découverte des médicaments','med-d086-q041':'Transmission synaptique et récepteurs','med-d086-q046':'Réponses quantales et toxicité','med-d092-q026':'Définition et production des biomédicaments'}
cache={}
def doc(i):
 if i not in cache:cache[i]=m.Doc(i)
 return cache[i]
def region(fid,page,top,bottom,name):
 d=doc(fid);lines=[dict(p=page-1,x=22,x2=570,y=top,y2=bottom-10,text='Données communes')]
 return d.render(lines,name,dict(p=page-1,y=bottom+4)) if m.RENDER else []
def stem_lines(q):
 ls=q['layout']['qlines'];n=q['itemNumbers'][0];ix=next((i for i,l in enumerate(ls) if re.match(r'^'+str(n)+r'\s*[.)]',l['text'])),None)
 return ls[:ix] if ix else []
def ancestors(q,depth=0):
 if depth>=3 or not re.search(r'pr[ée]c[ée]dent|suite des|suite du|suite de la|même énoncé',q['title'],re.I):return []
 prev=by.get(q['id'].rsplit('q',1)[0]+'q'+str(q['number']-1).zfill(3))
 if not prev or prev['sourceDocument']!=q['sourceDocument']:return []
 return ancestors(prev,depth+1)+[prev]
for q in qs:
 q['chapter'],q['topic'],cids=classification(q)
 q['title']=TITLES.get(q['id'],q['title']) or 'Concernant '+q['topic'].lower()
 if q['id']=='med-beb2-q011':q['title']=by['med-b4.1-q019']['title']
 q['sources']=q.pop('occurrences')
 for s in q['sources']:
  s['sourceFile']=s.pop('file');s['sourcePages']=s.pop('pages')
 q['transcriptionVerified']=True
 # Remove subsequent standalone instructions and section headings from the last choice.
 q['choices']=[re.split(r'\s+(?:Les [Cc]omposants du [Mm]édicament|Pharmacologie|Cet énoncé est valable|Le tableau ci-dessous présente)',x)[0].strip() for x in q['choices']]
 if q['id']=='med-d086-q041':q['choices'][-1]='Les médicaments agissant comme antagonistes d’un récepteur des médiateurs ont pour effet de diminuer les effets de ce médiateur.'
 if q['id'] in curated:
  c=curated[q['id']];q['answers']=c['answers'];q['correctionStatus']='unofficial';q['courseReferences']=cours(c.get('courseDocuments',cids))
  if 'reasons' in c:q['explanation']='\n\n'.join(f'{chr(65+i)} — '+('Oui' if v is True else 'Non' if v is False else 'À vérifier')+' : '+c['reasons'][i] for i,v in enumerate(c['answers']))
  else:
   q['explanation']=re.sub(r'(?m)^\s*(?:Réponses?\s*:\s*)?[ONVF]{5}.*\n?','',q['explanation']).strip()
   q['explanation']='Réponses retenues : '+', '.join(f'{chr(65+i)} : '+('Oui' if x else 'Non') for i,x in enumerate(q['answers']))+'.\n\n'+q['explanation']
  q['provenanceNote']=c.get('reviewNote','Correction rédigée pour compléter les documents fournis. Chaque proposition est expliquée ; les items ambigus restent hors notation.')
  if c.get('biologicalSupplement'):
   n=q['number'];keys=['adn'] if n in [5,17,20,25] else ['hybridome'] if n in [7,27] else ['insuline'] if n in [4,13] else ['genique'] if n in [2,8,10,18,23] else ['pk'] if n in [1,3,6,11,12,14,19,22] else ['biologie']
   q['externalReferences']=[REFS[k] for k in keys];q['provenanceNote']+=' Les cours ne couvrent pas tous les détails de cette ancienne ACC ; les références institutionnelles indiquées complètent ces points.'
 elif q['correctionStatus']=='conflict':
  # Never allow an unresolved source contradiction to contribute to a score.
  q['answers']=None
 if not q['explanation'] and q['answers'] is not None:
  q['explanation']='Grille de réponses fournie, sans justification détaillée dans le document.\n\n'+'\n'.join(f'{chr(65+i)} — '+('Oui' if a else 'Non') for i,a in enumerate(q['answers']))
  q['gridOnly']=True
 q['contextImages']=[];q['context']=''
 parents=ancestors(by.get(q['id'],q))
 if parents:
  q['context']='\n\n'.join('Données du QCM '+str(p.get('originalNumber') or p['number'])+' : '+p['title'] for p in parents)
  if m.RENDER:
   for p in parents:
    sl=stem_lines(p)
    if sl:q['contextImages']+=doc(p['sourceDocument']).render(sl,q['id']+'-contexte-'+p['id'],next((l for l in p['layout']['qlines'] if l not in sl),None))
 if q['id']=='med-d086-q029':
  p=by['med-d086-q028'];q['context']='Étude de liaison spécifique du ligand radiomarqué L* sur le récepteur R.'
  q['contextImages']=region(86,13,116,395,q['id']+'-contexte')
 if q['id'] in shared:
  q['context']='Données communes nécessaires à cette question.';q['contextImages']+=region(*shared[q['id']],q['id']+'-contexte')
 if m.RENDER:
  b=q['layout'];ls=b['qlines'];stop=b['next']
  # The next question's shared table must not be attached to the preceding question.
  limits={'med-d037-q017':(8,198),'med-d086-q041':(17,262)}
  if q['id'] in limits:
   p,y=limits[q['id']];ls=[l for l in ls if l['p']<p-1 or (l['p']==p-1 and l['y']<y)];stop=dict(p=p-1,y=y)
  q['images']=doc(q['sourceDocument']).render(ls,q['id'],stop)
  c=q.get('correctionLayout');q['correctionImages']=[]
  if c and q.get('correctionDocument'):
   cl=c.get('clines',c.get('lines',[]));q['correctionImages']=doc(q['correctionDocument']).render(cl,q['id']+'-corr',c.get('next'))
  elif q.get('sourceGrid') and isinstance(q['sourceGrid'],dict) and q.get('correctionDocument'):
   g=q['sourceGrid'];x,y,x2,y2=g['bbox'];q['correctionImages']=region(q['correctionDocument'],g['page'],max(14,y-6),y2+22,q['id']+'-grille')
 if q['id'] in old and not m.RENDER:
  for key in ['images','correctionImages','contextImages']:q[key]=old[q['id']][key]
 q['text']=q['title']+'\n'+'\n'.join(f'{n}. {c}' for n,c in zip(q['itemNumbers'],q['choices']))
 for k in ['layout','correctionLayout','sourceGrid','detailedAnswers','matchSimilarity','verifiedDuplicate','transcriptionSource','correctionFromDuplicate','sourceDocument','correctionDocument']:
  q.pop(k,None)
 assert len(q['choices'])==5 and all(q['choices']),q['id']
 assert q['answers'] is not None or q['correctionStatus']=='conflict',q['id']
 assert q['explanation'],q['id']
 if m.RENDER:assert q['images'],q['id']
(m.OUT/'data/medicament.json').write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':'))+'\n')
report=json.loads((W/'dedupe-report.json').read_text());report['correctionCounts']=dict(collections.Counter(q['correctionStatus'] for q in qs));report['ungraded']=[q['id'] for q in qs if q['answers'] is None or None in q['answers']];report['gridOnly']=sum(bool(q.get('gridOnly')) for q in qs)
report['documents']=[dict(d,occurrences=sum(x['sourceDocument']==d['id'] for x in occ),correctionUses=sum(x.get('correctionDocument')==d['id'] for x in occ)) for d in m.MAN if d['id']<=92]
report['standaloneCorrections']=[58,74];report['independentVerification']={58:'Corrigé PASS 2024 comparé aux ACC 2024 ; contradiction Q7 arbitrée avec le carnet 6.',74:'Corrigé des voies parentérales réutilisé pour les annales LAS 2021–2025.'};report['generatedAt']='2026-11-23';report['sourceRoots']=['qcm medicament','ACC MED','ACC MEDS PASS','MEDICAMENT','MEDS']
(ROOT/'scripts/data/medicament-import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print({k:report[k] for k in ['totalOccurrences','unique','removed','correctionCounts','ungraded','gridOnly']})
