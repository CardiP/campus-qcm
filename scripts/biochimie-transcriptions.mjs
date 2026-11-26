// Apply image-checked proposition boundaries without modifying sources, figures or answer keys.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const directory=path.join(root,'scripts/data');
const overrides=new Map();
for(const name of fs.readdirSync(directory).filter(name=>/^biochimie-transcriptions-.*\.json$/.test(name)).sort()){
  const entries=JSON.parse(fs.readFileSync(path.join(directory,name),'utf8'));
  for(const [id,entry] of Object.entries(entries)){
    if(overrides.has(id))throw Error(`Duplicate transcription: ${id}`);
    if(typeof entry.intro!=='string'||!entry.intro.trim()||entry.choices?.length!==5||entry.choices.some(value=>typeof value!=='string'||!value.trim()))throw Error(`Invalid transcription: ${id}`);
    overrides.set(id,entry);
  }
}
const applied=new Set();
for(const name of ['banques','annales']){
  const target=path.join(root,`public/data/${name}.json`);
  const questions=JSON.parse(fs.readFileSync(target,'utf8'));
  for(const q of questions){
    const entry=overrides.get(q.id);
    if(!entry)continue;
    q.intro=entry.intro;
    q.choices=entry.choices;
    q.transcriptionVerified=true;
    q.text=[entry.intro,...entry.choices.map((text,i)=>`${q.itemNumbers?.[i]||'ABCDE'[i]}. ${text}`)].join('\n');
    applied.add(q.id);
  }
  fs.writeFileSync(target,JSON.stringify(questions,null,2)+'\n');
}
for(const id of overrides.keys())if(!applied.has(id))throw Error(`Unknown question: ${id}`);
console.log(`${applied.size} transcriptions appliquées ; énoncés, cinq propositions et ordre conservés.`);
