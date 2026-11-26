import test from 'node:test';
import assert from 'node:assert/strict';
import {applyErratum, validateErratum, validateErrata, mergeErrata, evaluate, sessionStats} from '../public/core.js';
const source={id:'q1',answers:[true,false,true,false,true],explanation:'Corrigé du tutorat',correctionStatus:'source',images:['question.webp'],correctionImages:['original-correction.webp']};

test('a personal erratum changes grading and explanation while preserving the source and its images',()=>{
  const edit=validateErratum({answers:[false,false,true,false,true],explanation:'A : erratum du tutorat.'},123);
  const q=applyErratum(source,{q1:edit});
  assert.equal(evaluate(q,edit.answers).exact,true);
  assert.equal(evaluate(source,edit.answers).exact,false);
  assert.equal(q.explanation,edit.explanation);
  assert.equal(q.localErratum,true);
  assert.equal(q.correctionStatus,'personal');
  assert.equal(source.answers[0],true);
  assert.equal(source.explanation,'Corrigé du tutorat');
  assert.deepEqual(q.images,source.images);
  assert.deepEqual(q.correctionImages,source.correctionImages);
  q.answers[0]=true;
  assert.equal(edit.answers[0],false);
  assert.equal(applyErratum(source,{}),source);
});

test('current session scores reflect edits and return to the original score when reset',()=>{
  const answers=[false,false,true,false,true];
  const session={ids:['q1'],responses:{q1:answers}};
  const edit=validateErratum({answers,explanation:''},1);
  assert.equal(sessionStats(session,new Map([['q1',source]])).exact,0);
  assert.equal(sessionStats(session,new Map([['q1',applyErratum(source,{q1:edit})]])).exact,1);
  assert.equal(sessionStats(session,new Map([['q1',applyErratum(source,{})]])).exact,0);
});

test('an uncertain personal answer stays ungraded and can resolve a conflicting source key',()=>{
  const partial=validateErratum({answers:[null,false,true,false,true],explanation:''});
  assert.equal(evaluate(applyErratum(source,{q1:partial}),source.answers).graded,false);
  const confirmed=validateErratum({answers:source.answers,explanation:'Erratum confirmé.'});
  assert.equal(evaluate(applyErratum({...source,correctionStatus:'conflict'},{q1:confirmed}),source.answers).graded,true);
});

test('backup round trips retain errata and older backups cannot overwrite a newer correction',()=>{
  const older=validateErratum({answers:source.answers,explanation:'Ancienne',updatedAt:100});
  const newer=validateErratum({answers:[false,false,true,false,true],explanation:'Nouvelle\nAvec explication.',updatedAt:200});
  const exported=JSON.parse(JSON.stringify({version:1,errata:{q1:newer}}));
  assert.deepEqual(mergeErrata({q1:older},exported.errata),{q1:newer});
  assert.deepEqual(mergeErrata({q1:newer},{q1:older}),{q1:newer});
  assert.deepEqual(validateErrata(undefined),{});
});

test('invalid errata are rejected before they enter storage',()=>{
  for(const answers of [[],['true',false,true,false,true],[true,false,true,false,true,false]])assert.throws(()=>validateErratum({answers,explanation:''}));
  assert.throws(()=>validateErratum({answers:source.answers,explanation:5}));
  assert.throws(()=>validateErratum({answers:source.answers,explanation:'x'.repeat(12001)}));
  assert.throws(()=>validateErrata([]));
  assert.throws(()=>validateErrata(JSON.parse('{"__proto__":{}}')));
});
