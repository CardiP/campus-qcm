from pathlib import Path
import json,re,unicodedata,difflib,collections,sys
W=Path(sys.argv[1])
qs=json.loads((W/'banks.json').read_text())+json.loads((W/'acc-exams.json').read_text());byid={q['id']:q for q in qs}
def norm(t):
 t=re.sub(r'\b(?:OUI\s*/\s*NON)\b','',t,flags=re.I);t=re.sub(r'(?m)^\s*\d{1,3}\s*[.)]?\s*(?=\s|$)','',t)
 return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',t).encode('ascii','ignore').decode().lower())
def content(q):return norm(q['title']+' '+' '.join(q['choices'])) if len(q['choices'])==5 else norm(q['text'])
COUNTER={50:77,47:79,49:81,44:80,42:82,53:83,38:85,39:86,40:76}
def qnum(q):return q.get('originalNumber') or q['number']
# Remove running headers and the next section heading from the readable choices.
for q in qs:
 q['choices']=[re.split(r'\s+(?:Les [Cc]omposants du [Mm]édicament|Sources de [Vv]ariabilité|Pharmacologie|Pharmacocinétique|MOLÉCULES ACTIVES)(?:\s|$)',c)[0] for c in q['choices']]
 q['choices']=[re.sub(r'\s+UE[N 7]*\s*M[ÉE]DICAMENT.*?Page \d+ sur \d+','',c).strip() for c in q['choices']]
 q['choices']=[re.sub(r'\s+(?:\d{1,2}\s*)?(?:PARIS SACLAY.*|2JJ0000SS)$','',c).strip() for c in q['choices']]
 q['choices']=[re.sub(r'(?<=[.!?])\s+\d{1,2}$','',c).strip() for c in q['choices']]
repaired=[];uncertain=[]
for q in qs:
 fid=q['sourceDocument']
 if fid not in COUNTER and fid not in [34,37]:continue
 candidates=[r for r in qs if r['sourceDocument']==COUNTER.get(fid) and r.get('year')==q.get('year') and r.get('section')==q.get('section') and qnum(r)==qnum(q) and len(r['choices'])==5] if fid in COUNTER else [r for r in qs if r['sourceDocument']>=76 and r['sourceDocument']<=92 and r.get('year')==q.get('year') and r.get('section')=='LAS' and qnum(r)==q['number'] and len(r['choices'])==5]
 rated=sorted([(difflib.SequenceMatcher(None,content(q),content(r),autojunk=False).ratio(),r['id']) for r in candidates],reverse=True)
 if rated:
  sim,rid=rated[0];r=byid[rid]
  if sim>.70 and (len(rated)==1 or sim-rated[1][0]>.08):
   q['transcriptionSource']=rid;q['title']=r['title'];q['choices']=r['choices'].copy();q['itemNumbers']=r['itemNumbers'].copy();q['verifiedDuplicate']=rid;repaired.append((q['id'],rid,round(sim,3)))
  else:uncertain.append((q['id'],rated))
# Correct a printed lowercase l standing in for the item 1 and a missing item label.
for q in qs:
 if q['id']=='med-d077-q008':
  t=q['text'].splitlines()[1:];marks=[i for i,l in enumerate(t) if re.match(r'^(?:l|[1-5])\.',l)];q['choices']=[re.sub(r'^(?:l|[1-5])\.\s*(?:OUI\s*/\s*NON\s*:\s*)?','', ' '.join(t[i:marks[n+1] if n<4 else len(t)])) for n,i in enumerate(marks)];q['itemNumbers']=[1,2,3,4,5]
# Manual transcription of verified printed markers.
for qid,patch in json.loads((Path(__file__).parent/'data/medicament-transcription-fixes.json').read_text()).items():byid[qid].update(patch)
for q in qs:
 q['choices']=[re.split(r'\s+Les [Cc]omposants du [Mm]édicament',c)[0].strip() for c in q['choices']]
extra=W/'supplemental.json'
if extra.exists():
 for qid,patch in json.loads(extra.read_text())['patches'].items():byid[qid].update(patch)
 qs.extend(json.loads(extra.read_text())['questions'])
# Make identical correction-bearing archives available to the annual exams.
for q in qs:
 if q['category']!='annales':continue
 candidates=[r for r in qs if r['category']=='acc' and r.get('year')==q.get('year') and r.get('section')=='LAS' and qnum(r)==q['number'] and len(r['choices'])==5]
 rated=sorted([(difflib.SequenceMatcher(None,content(q),content(r),autojunk=False).ratio(),r['id']) for r in candidates],reverse=True)
 if rated and rated[0][0]>.95:
  sim,rid=rated[0];r=byid[rid]
  if r['answers'] is not None:
   for k in ['answers','explanation','correctionStatus','correctionDocument','correctionSourceFile','correctionSourcePages','correctionLayout','sourceGrid']:q[k]=r.get(k)
   q['correctionFromDuplicate']=rid
(W/'prepared.json').write_text(json.dumps(qs,ensure_ascii=False));(W/'repaired.json').write_text(json.dumps(repaired,ensure_ascii=False,indent=2));(W/'repair-candidates.json').write_text(json.dumps(uncertain,ensure_ascii=False,indent=2))
print('restored from matching native PDF',len(repaired),'ambiguous matches',len(uncertain));print('bad choices',[(q['id'],q.get('year'),qnum(q)) for q in qs if len(q['choices'])!=5]);print('no key',len([q for q in qs if q['answers'] is None]))
(W/'missing-review.txt').write_text('\n\n'.join(q['id']+' '+q.get('year','')+' '+q['title']+'\n'+'\n'.join(chr(65+i)+'. '+s for i,s in enumerate(q['choices'])) for q in qs if q['answers'] is None))
