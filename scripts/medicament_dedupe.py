from pathlib import Path
import json,re,unicodedata,difflib,collections,sys
W=Path(sys.argv[1]);qs=json.loads((W/'prepared.json').read_text());by={q['id']:q for q in qs};parent={i:i for i in by}
def norm(s):return re.sub('[^a-z0-9]','',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower())
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
def union(a,b):parent[find(a)]=find(b)
def body(q):return '|'.join(norm(s) for s in q['choices'])
def title(q):return norm(re.sub(r'^(?:concernant|à propos de|a propos de|sur)\s*','',q['title'],flags=re.I))
merges=[]
for q in qs:
 if q.get('verifiedDuplicate') and len(q['choices'])==5:
  other=q['verifiedDuplicate'];union(q['id'],other);merges.append((q['id'],other,'matching archived question'))
seen={}
for q in qs:
 if len(q['choices'])!=5:continue
 key=body(q)
 for old in seen.get(key,[]):
  r=by[old];a=title(q);b=title(r);sim=difflib.SequenceMatcher(None,a,b,autojunk=False).ratio()
  generic=lambda t:bool(re.match(r'^(?:quelle|quelles|que peut|quels|qcm|quellesont)',t)) and len(t)<110
  if a==b or sim>.88 or (generic(a) and generic(b)):
   union(q['id'],old);merges.append((q['id'],old,'identical choices and matching context'));break
 seen.setdefault(key,[]).append(q['id'])
for pair in json.loads((Path(__file__).parent/'data/medicament-dedup-reviewed.json').read_text()):
 union(pair['a'],pair['b']);merges.append((pair['a'],pair['b'],pair['reason']))
groups=collections.defaultdict(list)
for q in qs:groups[find(q['id'])].append(q)
unique=[];groupsout={};conflicts=[]
def priority(q):return (0 if q['category']=='annales' else 1 if q['category']=='eb' else 2 if q['category']=='banques' else 3 if q['sourceDocument']>=76 else 4,q['sourceDocument'],q['number'])
for group in groups.values():
 group.sort(key=priority);q=dict(group[0]);groupsout[q['id']]=[x['id'] for x in group]
 candidates=[r for r in group if r['answers'] is not None];candidates.sort(key=lambda r:(r['correctionStatus']=='conflict',not bool(r['explanation']),r['sourceDocument']<59,priority(r)))
 if candidates:
  r=candidates[0]
  for k in ['answers','explanation','correctionStatus','correctionDocument','correctionSourceFile','correctionSourcePages','correctionLayout','sourceGrid','detailedAnswers']:q[k]=r.get(k)
  q['correctionFromOccurrence']=r['id']
  differing=[r['id'] for r in candidates if r['answers']!=q['answers']]
  if differing:conflicts.append(dict(id=q['id'],chosen=q['correctionFromOccurrence'],differing=differing))
 q['occurrences']=[dict(id=r['id'],category=r['category'],sourceId=r['sourceId'],sourceLabel=r['sourceLabel'],number=r['number'],originalNumber=r['originalNumber'],year=r.get('year'),section=r.get('section'),file=r['sourceFile'],pages=r['sourcePages'],document=r['sourceDocument']) for r in group]
 unique.append(q)
unique.sort(key=priority);(W/'unique.json').write_text(json.dumps(unique,ensure_ascii=False));(W/'dedupe-report.json').write_text(json.dumps(dict(totalOccurrences=len(qs),unique=len(unique),removed=len(qs)-len(unique),groups=groupsout,merges=merges,correctionConflicts=conflicts),ensure_ascii=False,indent=2))
print('Occurrences',len(qs),'Unique',len(unique),'Removed',len(qs)-len(unique),'Missing',sum(q['answers'] is None for q in unique),'Conflicts',len(conflicts));print('Bad choices',[(q['id'],len(q['choices'])) for q in unique if len(q['choices'])!=5]);print('Need explanations',sum(not q['explanation'] for q in unique))
(W/'unique-missing.txt').write_text('\n\n'.join(q['id']+' '+str(q.get('year',''))+' '+q['title']+'\n'+'\n'.join(chr(65+i)+'. '+s for i,s in enumerate(q['choices'])) for q in unique if q['answers'] is None))
(W/'unique-conflicts.txt').write_text('\n\n'.join(q['id']+' '+q['title']+'\n'+'\n'.join(chr(65+i)+'. '+s for i,s in enumerate(q['choices']))+'\n'+str(q['answers'])+'\n'+str(q.get('detailedAnswers'))+'\n'+q['explanation'] for q in unique if q['correctionStatus']=='conflict' or q['id'] in [c['id'] for c in conflicts]))
# Report close pairs for explicit review; never merge on similarity alone.
near=[]
for q in unique:q['_body']=body(q);q['_normalized']=[norm(s) for s in q['choices']]
for i,q in enumerate(unique):
 if len(q['choices'])!=5:continue
 for r in unique[i+1:]:
  if len(r['choices'])!=5 or abs(len(q['_body'])-len(r['_body']))>100:continue
  same=sum(a==b for a,b in zip(q['_normalized'],r['_normalized']))
  if same<3:continue
  sims=[difflib.SequenceMatcher(None,norm(a),norm(b),autojunk=False).ratio() for a,b in zip(q['choices'],r['choices'])]
  if sum(sims)/5>=.94:near.append(dict(a=q['id'],b=r['id'],same=same,score=round(sum(sims)/5,3),changes=[(a,b) for a,b in zip(q['choices'],r['choices']) if norm(a)!=norm(b)],titles=[q['title'],r['title']]))
(W/'near-duplicates.json').write_text(json.dumps(near,ensure_ascii=False,indent=2));print('Near pairs',len(near))
