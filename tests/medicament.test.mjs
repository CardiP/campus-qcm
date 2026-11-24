import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {hasCorrection,filterQuestions,evaluate,questionSources} from '../public/core.js';
const qs=JSON.parse(fs.readFileSync(new URL('../public/data/medicament.json',import.meta.url)));
const report=JSON.parse(fs.readFileSync(new URL('../scripts/data/medicament-import-report.json',import.meta.url)));
const by=new Map(qs.map(q=>[q.id,q]));
test('medicine import accounts for all occurrences and all 92 source PDFs',()=>{
 assert.equal(qs.length,1007);assert.equal(report.totalOccurrences,1509);assert.equal(report.removed,502);
 assert.equal(qs.reduce((n,q)=>n+q.sources.length,0),1509);
 assert.equal(new Set(qs.flatMap(q=>q.sources.map(s=>s.id))).size,1509);
 assert.equal(report.documents.length,92);
 for(const d of report.documents)assert(d.occurrences || d.correctionUses || report.standaloneCorrections.includes(d.id),d.file);
});
test('all medicine choices, corrections, references and assets are usable',()=>{
 for(const q of qs){
  assert(q.title&&q.topic&&q.chapter,q.id);assert(q.choices.length===5&&q.choices.every(x=>typeof x==='string'&&x.trim()),q.id);
  assert(q.images.length&&q.explanation,q.id);assert(q.answers.length===5,q.id);
  for(const p of [...q.images,...q.correctionImages,...q.contextImages])assert(fs.existsSync(new URL('../public/'+p,import.meta.url)),p);
  if(q.correctionStatus==='unofficial')assert(q.courseReferences.length,q.id);
 }
 assert.equal(qs.filter(q=>q.correctionStatus==='unofficial').length,83);
 assert.equal(qs.filter(q=>!hasCorrection(q)).length,9);
});
test('each medicine annual exam keeps all 28 questions in original order without duplicate IDs',()=>{
 for(const id of [32,33,34,35,37]){
  const source='med-d'+String(id).padStart(3,'0'),found=filterQuestions(qs,{category:'annales',source});
  assert.equal(found.length,28,source);assert.equal(new Set(found.map(q=>q.id)).size,28);
  assert.deepEqual(found.map(q=>q.sources.find(s=>s.sourceId===source).number),Array.from({length:28},(_,i)=>i+1));
 }
});
test('source and category match the same occurrence, while mixing returns each QCM once',()=>{
 const q=qs.find(q=>q.sources.some(s=>s.category==='acc')&&q.sources.some(s=>s.category==='annales'));
 const acc=q.sources.find(s=>s.category==='acc');
 assert.deepEqual(filterQuestions([q],{category:'acc',source:acc.sourceId}),[q]);
 assert.deepEqual(filterQuestions([q],{category:'annales',source:acc.sourceId}),[]);
 const mixed=filterQuestions(qs,{category:'all'});assert.equal(new Set(mixed.map(q=>q.id)).size,mixed.length);
});
test('shared data survive shuffled study and significant variants remain separate',()=>{
 for(const id of ['med-d035-q026','med-d034-q026','med-d037-q018','med-d037-q019','med-d086-q044','med-d086-q029'])assert(by.get(id).contextImages.length,id);
 for(const id of ['med-d087-q003','med-d087-q004','med-d032-q019','med-b7-q028','med-d085-q001','med-d085-q002'])assert(by.has(id),id);
});
test('reviewed correction conflicts and arithmetic have explicit keys; ambiguities never score',()=>{
 assert.deepEqual(by.get('med-b11-q011').answers,[true,false,true,false,false]);
 assert.deepEqual(by.get('med-d035-q026').answers,[true,true,false,false,true]);
 assert.deepEqual(by.get('med-d086-q044').answers,[true,false,true,false,true]);
 assert.deepEqual(by.get('med-b4.2-q025').answers,[true,false,true,false,true]);
 for(const q of qs.filter(q=>!hasCorrection(q)))assert.equal(evaluate(q,[true,true,true,true,true]).graded,false,q.id);
 assert.equal(hasCorrection({answers:[true,true,true,true,true],correctionStatus:'conflict'}),false);
});
