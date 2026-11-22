import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {hasCorrection,readableQuestion,evaluate,filterQuestions} from '../public/core.js';
const qs=JSON.parse(fs.readFileSync(new URL('../public/data/anatomie.json',import.meta.url)));
const report=JSON.parse(fs.readFileSync(new URL('../scripts/data/anatomie-import-report.json',import.meta.url)));
const byId=new Map(qs.map(q=>[q.id,q]));
test('every supplied anatomy PDF and every source question is accounted for',()=>{
 assert.equal(qs.length,1261);assert.equal(byId.size,qs.length);assert.equal(report.documents.length,58);
 for(const d of report.documents){assert(d.questionIds.length+d.correctionIds.length>0,d.file);assert.match(d.sha256,/^[a-f0-9]{64}$/)}
 for(const year of ['2020-2021','2021-2022','2022-2023','2023-2024','2024-2025']){
  const exam=qs.filter(q=>q.sourceId==='anat-'+year);assert.equal(exam.length,35);
  assert.deepEqual(exam.flatMap(q=>q.itemNumbers),Array.from({length:175},(_,i)=>i+1));
 }
 assert.equal(qs.filter(q=>q.adaptedFromExercise).length,3);
 assert(qs.some(q=>q.id==='anat-5-q039'&&q.itemNumbers[0]===191));
});
test('all anatomy records have classified chapters, readable choices, corrections and real assets',()=>{
 for(const q of qs){
  assert.equal(q.subject,'anatomie');assert.notEqual(q.topic,'À classer');assert.notEqual(q.chapter,'transversal');
  assert.equal(q.choices.length,5);assert(q.choices.every(t=>t.trim()&&!t.includes('Voir la proposition')));assert(q.explanation,q.id);
  assert.deepEqual(readableQuestion(q).choices,q.choices,q.id);
  assert.equal(q.answers.length,5);assert(q.answers.every(v=>v===null||typeof v==='boolean'));
  assert(q.images.length,q.id);assert(q.sourcePages.length,q.id);
  for(const a of [...q.images,...q.correctionImages]){assert.match(a,/^assets\/anatomie\/[^/]+\.webp$/);assert(fs.statSync(new URL('../public/'+a,import.meta.url)).size>100,a)}
  if(q.correctionStatus==='unofficial'){
   assert(q.courseReferences.length,q.id);
   for(const l of 'ABCDE')assert(q.explanation.includes(l+' — '),q.id+' '+l);
  }
 }
});
test('partial corrections remain readable but never enter the score or corrected-only filter',()=>{
 const ambiguous=qs.filter(q=>q.answers.includes(null));assert.equal(ambiguous.length,report.ambiguous.length);assert(ambiguous.length>0);
 for(const q of ambiguous){assert.equal(hasCorrection(q),false);assert.equal(evaluate(q,[true,true,true,true,true]).graded,false);assert.match(q.explanation,/À confirmer/)}
 assert.equal(filterQuestions(qs,{correctedOnly:true}).length,qs.length-ambiguous.length-report.missingFigures.length);
});
test('reviewed conflicts and reversed instructions use the intended selection key',()=>{
 assert.deepEqual(byId.get('anat-eb1-q020').answers,[true,true,false,false,false]);
 assert.deepEqual(byId.get('anat-1-q028').answers,[false,false,false,true,false]);
 assert.deepEqual(byId.get('anat-12-q031').answers,[false,true,false,true,true]);
 assert.deepEqual(byId.get('anat-20-q015').answers,[true,true,false,false,false]);
 assert.equal(byId.get('anat-12-q031').answerInstruction,'inexactes');
 assert(byId.get('anat-eb1-q020').sourceExplanation);
});
test('five choices stay separate even when a PDF item marker is below the text',()=>{
 const q=byId.get('anat-2-q040');assert.equal(q.choices[3],'Est innervé par le système cérébro-spinal.');assert.equal(q.choices[4],'Est constitué de léiomyocytes.');
});

test('missing source diagrams exclude those questions from the score',()=>{assert.equal(report.missingFigures.length,4);for(const id of report.missingFigures){const q=byId.get(id);assert(q.missingFigure);assert(!hasCorrection(q));assert(q.explanation);}});
