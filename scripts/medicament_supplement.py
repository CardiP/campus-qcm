"""Use standalone corrections and full questions printed only in correction PDFs."""
import json
import medicament_extract as m
import medicament_acc_extract as a

qs=json.loads((m.W/'banks.json').read_text())+json.loads((m.W/'acc-exams.json').read_text())
patches={};extra=[]
for fid in [74,58]:
 d=m.Doc(fid);cs=d.blocks('acc-correction' if fid==74 else 'bank');gs=a.grid(d)
 for q in qs:
  yr,sec,num=q.get('year'),q.get('section'),q.get('originalNumber') or q['number']
  if fid==58 and (yr!='2024' or sec!='PASS'):continue
  c=next((c for c in cs if c['number']==num and (fid==58 or (c['year']==yr and c['section']==sec))),None)
  if not c:continue
  ans,det,conflict=m.key(c['lines'])
  if ans is None:continue
  if q['answers'] is None:
   patches[q['id']]=dict(answers=ans,explanation='\n'.join(l['text'] for l in c['lines']),correctionStatus='source',correctionDocument=fid,correctionSourceFile=d.meta['file'],correctionSourcePages=sorted({l['p']+1 for l in c['lines']}),correctionLayout=c)
  elif ans!=q['answers']:
   print('Independent correction differs',q['id'],fid,ans,q['answers'])
# The question is printed, but its correction question markers are inside a raster image.
d=m.Doc(3)
for c in [m.parse(b,True) for b in d.blocks('bank')]:
 if c['number']==25:
  ans,_,_=m.key(c['clines']);patches['med-b2-q025']=dict(answers=ans,explanation='\n'.join(l['text'] for l in c['clines']),correctionStatus='source',correctionDocument=3,correctionSourceFile=d.meta['file'],correctionSourcePages=sorted({l['p']+1 for l in c['clines']}),correctionLayout=c)
# Two additional complete QCM occur only in the correction PDF. The crop ends before answers.
d=m.Doc(27);cs=[m.parse(b,True) for b in d.blocks('bank')]
used=set()
for q in qs:
 if q['correctionDocument']==27 and q.get('correctionLayout'):
  c=q['correctionLayout'];used.add((c['qlines'][0]['p'],c['qlines'][0]['y']))
for ix,c in enumerate(cs,1):
 if (c['qlines'][0]['p'],c['qlines'][0]['y']) in used:continue
 if len(c['choices'])!=5:raise ValueError('Unparsed supplemental QCM')
 q=a.record(d,c,ix,'banques','Banque 5 · compléments du corrigé')
 q['id']=f'med-c027-q{ix:03}';q['sourceId']='med-5';q['sourceLabel']='Banque 5';q['number']=100+ix
 ans,_,conflict=m.key(c['clines']);q.update(answers=ans,explanation='\n'.join(l['text'] for l in c['clines']),correctionStatus='conflict' if conflict else 'source',correctionDocument=27,correctionSourceFile=d.meta['file'],correctionSourcePages=sorted({l['p']+1 for l in c['clines']}),correctionLayout=c)
 q['layout']=dict(c,next=c['clines'][0]);extra.append(q)
(m.W/'supplemental.json').write_text(json.dumps(dict(patches=patches,questions=extra),ensure_ascii=False))
print('Additional corrections',len(patches),'additional questions',len(extra))
