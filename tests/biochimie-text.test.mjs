import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {readableQuestion,normalizeQuestion} from '../public/core.js';
const questions=['banques','annales'].flatMap(name=>JSON.parse(fs.readFileSync(new URL(`../public/data/${name}.json`,import.meta.url),'utf8'))).map(normalizeQuestion);

test('every biochimie QCM has five readable propositions, including architecture',()=>{
  assert.equal(questions.length,869);
  assert.equal(questions.filter(q=>q.topic==='Architecture des protéines').length,77);
  for(const q of questions){
    const text=readableQuestion(q);
    assert.ok(text,q.id);
    assert.equal(text.choices.length,5,q.id);
    assert.ok(text.choices.every(s=>s.trim()&&!/^(?:Proposition\s+)?[A-E]$/i.test(s.trim())),q.id);
  }
});

test('unnumbered OUI/NON rows keep wrapped statements together without inventing boundaries',()=>{
  const q={text:'Question 1 : Structure tertiaire\nOUI/NON Première proposition\nsur deux lignes.\nOUI/NON Deux.\nOUI/NON Trois.\nOUI/NON Quatre.\nOUI/NON Cinq.'};
  assert.deepEqual(readableQuestion(q).choices,['Première proposition sur deux lignes.','Deux.','Trois.','Quatre.','Cinq.']);
  assert.equal(readableQuestion({...q,text:q.text+'\nOUI/NON Six.'}),null);
  assert.equal(readableQuestion({text:'Titre\nUn\nDeux\nTrois\nQuatre\nCinq'}),null);
});

test('reviewed transcriptions preserve false statements, formulas and all shared given data',()=>{
  const byId=new Map(questions.map(q=>[q.id,q]));
  assert.equal(readableQuestion(byId.get('banques-architecture-33')).choices[1],'Elle confère un pic d’absorption à 280 nm.');
  assert.equal(readableQuestion(byId.get('banques-enzymologie-2-11')).choices[1],'V = d[S]/dt.');
  assert.equal(readableQuestion(byId.get('banques-architecture-45')).choices[4],'La proline.');
  const reviewed={transcriptionVerified:true,title:'Peptides',intro:'Peptide A : ABC ; peptide B : DEF.',choices:['un','deux','trois','quatre','cinq']};
  assert.equal(readableQuestion(reviewed).intro,reviewed.intro);
});
