"""Assemble extracted anatomy QCM, reviewed course corrections and provenance.
Usage: python scripts/anatomie_build.py WORK_DIR COURSES_DIR
The JSON/WebP files committed under public/ work without Python or the source PDFs.
"""
from pathlib import Path
import json,sys,copy,collections,re,hashlib
ROOT=Path(__file__).resolve().parents[1];WORK=Path(sys.argv[1]);COURSES=Path(sys.argv[2]);OUT=ROOT/'public'
qs=json.loads((WORK/'banks.json').read_text())+json.loads((WORK/'exams.json').read_text());byid={q['id']:q for q in qs}
# The final item marker in banque 2 sits below its text baseline in the PDF.
q=byid['anat-2-q040'];q['choices'][3]='Est innervé par le système cérébro-spinal.';q['choices'][4]='Est constitué de léiomyocytes.'
byid['anat-24-q033']['choices'][0]='Les structures 4 et 5 sont respectivement les bronches principales droite et gauche.'
missing_figures=['anat-4-q021','anat-4-q025','anat-10-q034','anat-18-q039']
for qid in missing_figures:byid[qid]['missingFigure']=True
titles=['Généralités et orientations','Système osseux, articulaire et musculaire','Os de la ceinture scapulaire et du bras','Os de l’avant-bras et de la main','Épaule et bras','Coude et avant-bras','Poignet et main','Vaisseaux du membre thoracique','Innervation du membre thoracique','Os de la ceinture pelvienne et de la cuisse','Os de la jambe et du pied','Hanche et cuisse','Genou et jambe','Cheville et pied','Vaisseaux du membre pelvien','Innervation du membre pelvien','Colonne vertébrale','Paroi thoracique et médiastin','Glande mammaire','Appareil circulatoire','Parois, cavités et valves cardiaques','Vaisseaux et nerfs cardiaques','Diaphragme','Voies aériennes','Poumons et plèvre','Rétropéritoine','Appareil urinaire','Parois pelviennes','Appareil génital masculin','Appareil génital féminin','Crâne','Moelle, tronc cérébral et cervelet','Cerveau','Méninges et liquide cérébrospinal','Vascularisation cérébrale','Voies de la douleur','Système nerveux végétatif','Appareil optique']
def domain(n):return 'generalites' if n<=2 else 'membre-thoracique' if n<=9 else 'membre-pelvien' if n<=16 else 'tronc' if n<=19 else 'cardiorespiratoire' if n<=25 else 'abdomen-pelvis' if n<=30 else 'neuroanatomie'
def classify(q,n):q.update(topic=f'{n:02} · {titles[n-1]}',chapter=domain(n),topicOrder=n)
# Explicit document order for the supplied EB1 and TD; anatomy course references
# use the original 37-course numbering (the banks add pelvic innervation at 16).
eb=[1,1,2,2,3,3,3,3,4,4,4,4,5,5,5,5,6,6,9,6,7,6,6,7,8,8,8,9,9,9,9,10,10,11,11]
td=[3,3,4,4,5,5,7,7,8,8,9,9,1,10,12,12,11,13,11,13,13,13,15,15,15,16,16]
for q in qs:
 if q['category']=='banques':classify(q,int(q['sourceId'].split('-')[1]))
 elif q['sourceId']=='anat-eb1':classify(q,eb[q['number']-1])
 elif q['sourceId']=='anat-td1':classify(q,td[q['number']-1])
 q['choices']=[re.sub(r'ARCHIVES DES ANNÉES PRÉCÉDENTES','',s).strip() for s in q['choices']]
 q['choices']=[re.sub(r'^OUI\s*/\s*NON\s*','',s).strip() for s in q['choices']]
 if q['itemNumbers']:q['transcriptionVerified']=True
# Supplied exercises are explicitly adapted to the site's five-proposition model.
# The source exercises and their original correction images remain accessible.
adaptations=[('anat-td1-q024','Repères du réseau artériel pelvien et fémoral (1/2)',[
 'Le repère 1 désigne l’aorte.','Le repère 2 désigne la bifurcation aortique.','Le repère 3 désigne l’artère iliaque externe.','Le repère 4 désigne l’artère iliaque interne.','Le repère 5 désigne l’artère fémorale commune.'], 'OONNO',[
 'Le corrigé du schéma identifie l’aorte en 1.','Le repère 2 est la division de l’aorte en iliaques communes.','Le repère 3 désigne l’iliaque interne.','Le repère 4 désigne l’iliaque externe.','L’iliaque externe devient fémorale commune après le ligament inguinal.']),
 ('anat-td1-q024b','Repères du réseau artériel pelvien et fémoral (2/2)',[
 'Le repère 6 désigne l’artère fémorale superficielle.','Le repère 7 désigne l’artère profonde de la cuisse.','Le repère 8 désigne le ligament inguinal.','Le repère 9 désigne le hiatus du grand adducteur.','Après le repère 9, l’artère porte le nom d’artère tibiale antérieure.'],'OOOON',[
 'Le corrigé nomme en 6 l’axe fémoral superficiel.','Le repère 7 est la fémorale profonde.','Le ligament inguinal est repéré en 8.','Le repère 9 est le hiatus du grand adducteur.','Après le hiatus, l’artère devient poplitée ; les axes tibiaux sont plus distaux.']),
 ('anat-td1-q025','Continuité des artères du membre pelvien',[
 'La fémorale devient poplitée au hiatus du grand adducteur.','L’axe poplité donne une artère tibiale antérieure.','L’axe poplité donne une artère tibiale postérieure.','L’iliaque commune se divise en iliaques interne et externe.','L’iliaque externe se poursuit directement par l’artère poplitée.'],'OOOON',[
 'C’est le changement de nom indiqué dans l’exercice corrigé.','La tibiale antérieure est une branche terminale du réseau poplité.','La tibiale postérieure constitue l’autre grand axe terminal.','L’interne gagne le pelvis ; l’externe se poursuit vers le membre.','L’iliaque externe devient d’abord fémorale au passage du ligament inguinal.'])]
for qid,title,choices,bits,why in adaptations:
 if qid.endswith('b'):
  q=copy.deepcopy(byid[qid[:-1]]);q['id']=qid;q['number']=24.5;qs.insert(qs.index(byid[qid[:-1]])+1,q);byid[qid]=q
 else:q=byid[qid]
 q.update(title=title,choices=choices,answers=[c=='O' for c in bits],explanation='Adaptation en cinq propositions de l’exercice corrigé du TD.\n\n'+'\n\n'.join(f'{c} — {"Vrai" if b=="O" else "Faux"}. {w}' for c,b,w in zip('ABCDE',bits,why)),correctionStatus='unofficial',adaptedFromExercise=True,transcriptionVerified=True,itemNumbers=None,courseReferences=[{'file':'anatomie_15.pdf','label':'Carnet 15 · Vaisseaux du membre pelvien'}],provenanceNote='Exercice du TD adapté en QCM ; les propositions ont été rédigées à partir de son corrigé et du carnet 15.')
# Every authored verdict is reviewed independently; unknown remains null and ungraded.
reviewed=[]
for line in (ROOT/'scripts/data/anatomie-corrections.txt').read_text().splitlines():
 if not line or line.startswith('#'):continue
 parts=line.split('|');assert len(parts)==8,line
 qid,bits,refs,*why=parts;assert len(bits)==5 and set(bits)<=set('ON?'),qid;assert qid not in reviewed,qid
 q=byid[qid];old=q['correctionStatus'];q['originalCorrectionStatus']=old
 if q.get('explanation'):q['sourceExplanation']=q['explanation']
 q['answers']=[None if c=='?' else c=='O' for c in bits];q['correctionStatus']='unofficial'
 inexact=bool(re.search(r'inexact|incorrect|fausse',q['title'],re.I))
 q['explanation']='\n\n'.join(f'{c} — {"À confirmer" if b=="?" else ("Oui, à sélectionner" if b=="O" else "Non, à écarter") if inexact else "Vrai" if b=="O" else "Faux"}. {w}' for c,b,w in zip('ABCDE',bits,why))
 nums=[int(x) for x in refs.split(',')];q['courseReferences']=[{'file':f'anatomie_{n}.pdf','label':f'Carnet {n} · {titles[n-1 if n<16 else n]}'} for n in nums]
 if q.get('chapter')=='transversal':classify(q,nums[0] if nums[0]<16 else nums[0]+1)
 if old=='conflict' or qid in ['anat-1-q028','anat-20-q035','anat-7-q010','anat-14-q005','anat-16-q011']:
  q['provenanceNote']='La grille et/ou les justifications du document comportent une incohérence. La réponse proposée ici a été réexaminée avec les cours ; le corrigé d’origine reste consultable.'
 reviewed.append(qid)
# Compact records, preserve match evidence in the audit rather than app payload.
match_audit=[]
for q in qs:
 assert q['topic']!='À classer',q['id']
 assert len(q['choices'])==5 and all(q['choices']),q['id']
 assert q['answers'] is not None and len(q['answers'])==5,q['id']
 assert q['explanation'],q['id']
 if 'matchSimilarity' in q:match_audit.append({k:q[k] for k in ['id','originalNumber','sourceFile','sourcePages','correctionSourceFile','correctionSourcePages','matchSimilarity']})
 for k in ['matchSimilarity','detailedAnswers','sourceAnswers']:q.pop(k,None)
 q['answerInstruction']='inexactes' if re.search(r'inexact|incorrect|fausse',q['title'],re.I) else 'exactes'
(OUT/'data/anatomie.json').write_text(json.dumps(qs,ensure_ascii=False,separators=(',',':'))+'\n')
manifest=json.loads((WORK/'manifest.json').read_text());courses=[]
for n in range(1,38):
 p=COURSES/f'anatomie_{n}.pdf';courses.append({'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
coverage=[]
for m in manifest:
 source=[q for q in qs if q['sourceFile']==m['file']];corr=[q for q in qs if q.get('correctionSourceFile')==m['file']]
 coverage.append({**m,'questionIds':[q['id'] for q in source],'correctionIds':[q['id'] for q in corr]})
 assert source or corr,m['file']
report={'documents':coverage,'missingFigures':missing_figures,'courses':courses,'counts':dict(collections.Counter(q['category'] for q in qs)),'total':len(qs),'authoredCorrections':len(reviewed),'adaptedExercises':3,'ambiguous':[q['id'] for q in qs if None in q['answers']],'bankMatching':match_audit,'bankCoverage':json.loads((WORK/'bank-audit.json').read_text()),'notes':['La banque 5 omet le titre de la question 39 dans les deux PDF ; les items 191 à 195 sont récupérés.','La banque 18 correction contient une question 40 factice (Item 196…200 / Justification), absente du sujet : elle est exclue.','La numérotation recommence dans certaines archives : les identifiants reposent sur l’ordre réel des questions.','Les deux exercices 24 et 25 du TD sont adaptés en trois QCM, explicitement signalés.','Annale 2020–2021 : transcription OCR locale Apple Vision, vérifiée pour les 175 propositions.']}
(ROOT/'scripts/data/anatomie-import-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['counts','total','authoredCorrections','adaptedExercises','ambiguous']},ensure_ascii=False,indent=2))
