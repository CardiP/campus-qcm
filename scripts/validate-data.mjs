import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {hasCorrection,normalizeQuestion} from '../public/core.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const qs=['annales','banques','anatomie','medicament'].flatMap(f=>JSON.parse(fs.readFileSync(path.join(root,'public/data',f+'.json')))).map(normalizeQuestion);
const ids=new Set();const counts={};let assetCount=0;
for(const q of qs){
 assert(!ids.has(q.id),`Duplicate id ${q.id}`);ids.add(q.id);
 assert(['acc','annales','eb','td','banques'].includes(q.category),q.id);
 assert((q.subject==='medicament'?['cadre','conception','galenique','pharmacologie']:q.subject==='anatomie'?['generalites','membre-thoracique','membre-pelvien','tronc','cardiorespiratoire','abdomen-pelvis','neuroanatomie']:['structurale','biomol','enzymologie','metabolisme']).includes(q.chapter),q.id);
 assert(q.title&&q.sourceId&&q.sourceLabel&&q.topic,q.id);
 assert(Array.isArray(q.choices)&&q.choices.length===5,q.id);
 assert(q.answers===null||(Array.isArray(q.answers)&&q.answers.length===5&&q.answers.every(v=>typeof v==='boolean'||v===null)),q.id);
 assert(q.images?.length,q.id);
 if(q.correctionStatus==='unofficial'){assert(q.explanation,q.id);assert(q.courseReferences?.length,q.id)}
 for(const image of [...q.images,...(q.correctionImages||[]),...(q.contextImages||[])]){assert(image.startsWith('assets/')&&!image.includes('..'),image);assert(fs.existsSync(path.join(root,'public',image)),image);assetCount++}
 const subject=q.subject||'biochimie';counts[subject]||={};counts[subject][q.category]=(counts[subject][q.category]||0)+1;
}
assert.deepEqual(counts.biochimie,{annales:130,banques:664,eb:50,td:25});
assert.deepEqual(counts.anatomie,{banques:988,eb:70,td:28,annales:175});
for(const year of ['2020-2021','2021-2022','2022-2023','2023-2024','2024-2025'])assert.equal(qs.filter(q=>q.sourceId==='annale-'+year).length,year==='2020-2021'?30:25);
console.log(JSON.stringify({questions:qs.length,categories:counts,chapters:new Set(qs.map(q=>q.topic)).size,graded:qs.filter(hasCorrection).length,ungraded:qs.filter(q=>!hasCorrection(q)).length,verifiedImageReferences:assetCount},null,2));
