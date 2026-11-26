export function hasCorrection(q) { return !q.missingFigure && q.correctionStatus!=='conflict' && Array.isArray(q.answers) && q.answers.length===5 && q.answers.every(v=>typeof v==='boolean'); }
export function questionSources(q) { return q.sources?.length ? q.sources : [q]; }
export function matchesSource(q, filters) {
 return questionSources(q).some(s=>(!filters.category || filters.category==='all' || s.category===filters.category) && (!filters.source || s.sourceId===filters.source));
}
export const LETTERS = ['A','B','C','D','E'];
export function validateErratum(raw, now=Date.now()) {
 if(!raw || !Array.isArray(raw.answers) || raw.answers.length!==5 || raw.answers.some(value=>value!==true&&value!==false&&value!==null))throw Error('Indique Oui, Non ou À confirmer pour chacune des cinq propositions.');
 if(typeof raw.explanation!=='string'||raw.explanation.length>12000)throw Error('La correction doit contenir au maximum 12 000 caractères.');
 const updatedAt=raw.updatedAt??now;
 if(!Number.isFinite(updatedAt)||updatedAt<0)throw Error('La date de cette correction est invalide.');
 return {answers:[...raw.answers],explanation:raw.explanation.trim(),updatedAt};
}
export function validateErrata(raw={}) {
 if(!raw||typeof raw!=='object'||Array.isArray(raw)||Object.keys(raw).length>10000)throw Error('Le format des corrections personnelles est invalide.');
 const result={};
 for(const [id,entry] of Object.entries(raw)){
  if(!/^[a-z0-9][a-z0-9_-]{0,199}$/i.test(id)||['__proto__','constructor','prototype'].includes(id))throw Error('Une correction personnelle contient un identifiant invalide.');
  result[id]=validateErratum(entry);
 }
 return result;
}
export function mergeErrata(existing, incoming) {
 const result={...existing};
 for(const [id,entry] of Object.entries(validateErrata(incoming)))if(!Object.hasOwn(result,id)||entry.updatedAt>result[id].updatedAt)result[id]=entry;
 return result;
}
export function applyErratum(question, errata) {
 const edit=Object.hasOwn(errata,question.id)?errata[question.id]:null;
 return edit?{...question,answers:[...edit.answers],explanation:edit.explanation,correctionStatus:'personal',localErratum:true,erratumUpdatedAt:edit.updatedAt}:question;
}
export function shuffled(items, rng = Math.random) { const out=[...items]; for(let i=out.length-1;i>0;i--){const j=Math.floor(rng()*(i+1));[out[i],out[j]]=[out[j],out[i]];} return out; }
export function filterQuestions(questions, filters, progress = {}) {
 const result=questions.filter(q => matchesSource(q,filters)
 && (!filters.chapter || q.chapter===filters.chapter)
 && (!filters.topic || q.topic===filters.topic)
 && (!filters.correctedOnly || hasCorrection(q))
 && (!filters.onlyErrors || progress[q.id]?.lastCorrect===false)
 && (!filters.search || `${q.title} ${q.text} ${questionSources(q).map(s=>s.sourceLabel).join(' ')} ${q.topic}`.toLocaleLowerCase('fr').includes(filters.search.toLocaleLowerCase('fr'))));
 if(filters.source) result.sort((a,b)=>Math.min(...questionSources(a).filter(s=>s.sourceId===filters.source).map(s=>s.number))-Math.min(...questionSources(b).filter(s=>s.sourceId===filters.source).map(s=>s.number)));
 return result;
}
export function evaluate(question, responses = []) {
 const complete = responses.length===5 && responses.every(v=>typeof v==='boolean');
 if(!hasCorrection(question)) return {graded:false,complete,exact:false,items:0};
 const items = question.answers.reduce((n,v,i)=>n+(responses[i]===v?1:0),0);
 return {graded:true,complete,exact:complete && items===5,items};
}
export function sessionStats(session, byId) {
 const list=session.ids.map(id=>byId.get(id)).filter(Boolean);
 const rows=list.map(q=>({q,...evaluate(q,session.responses[q.id] || [])}));
 return {total:rows.length, answered:rows.filter(r=>r.complete).length, graded:rows.filter(r=>r.graded).length, exact:rows.filter(r=>r.graded&&r.exact).length, items:rows.reduce((n,r)=>n+(r.graded?r.items:0),0), missing:rows.filter(r=>!r.graded).length};
}
export function validateQuestion(raw, index, subject='anatomie') {
 if(!raw || typeof raw!=='object') throw new Error(`Question ${index+1} : format invalide.`);
 if(typeof raw.title!=='string' || !raw.title.trim()) throw new Error(`Question ${index+1} : un énoncé est nécessaire.`);
 if(!Array.isArray(raw.choices) || raw.choices.length!==5 || raw.choices.some(v=>typeof v!=='string'||!v.trim())) throw new Error(`Question ${index+1} : cinq propositions sont nécessaires.`);
 if(!Array.isArray(raw.answers) || raw.answers.length!==5 || raw.answers.some(v=>typeof v!=='boolean')) throw new Error(`Question ${index+1} : cinq réponses true/false sont nécessaires.`);
 return {id:`custom-${subject}-${Date.now()}-${index}`,subject,category:['acc','annales','eb','td','banques'].includes(raw.category)?raw.category:'banques',sourceId:`custom-${subject}-${String(raw.sourceLabel||'Mes QCM').toLowerCase().replace(/[^a-z0-9]+/g,'-')}`,sourceLabel:String(raw.sourceLabel||'Mes QCM').slice(0,120),number:index+1,chapter:String(raw.chapter||'personnel').slice(0,100),topic:String(raw.topic||'Mes questions').slice(0,120),title:raw.title.slice(0,6000),text:raw.choices.join(' '),choices:raw.choices.map(v=>v.slice(0,4000)),answers:raw.answers,explanation:String(raw.explanation||'').slice(0,12000),images:[],correctionImages:[],correctionStatus:'personal',sourcePages:[],sourceFile:'Import personnel'};
}
// Offer selectable text alongside the faithful original images only when all five item boundaries are unambiguous.
export function readableQuestion(q) {
 // Reviewed boundaries take precedence over the original PDF/OCR reading order.
 if(q.transcriptionVerified===true && Array.isArray(q.choices) && q.choices.length===5 && q.choices.every(t=>typeof t==='string'&&t.trim()))return {intro:q.intro||q.title||'',choices:q.choices};
 if(!q.text)return null;
 let matches;
 if(Array.isArray(q.itemNumbers)&&q.itemNumbers.length===5){
  matches=q.itemNumbers.map(n=>new RegExp('(?:^|\\n)\\s*'+Number(n)+'\\s*[.)]\\s*(?:(?:OUI\\s*[/]\\s*NON)\\s*:?\\s*)?','i').exec(q.text));
 }else{
  // Some banks use five unnumbered OUI/NON rows. Do not guess paragraph boundaries.
  matches=[...q.text.matchAll(/(?:^|\n)[ \t]*OUI[ \t]*\/[ \t]*NON[ \t]*:?[ \t]*/gi)];
  if(matches.length!==5)return null;
 }
 if(matches.some(m=>!m))return null;
 if(matches.some((m,i)=>i>0&&m.index<=matches[i-1].index))return null;
 const clean=t=>t.replace(/\s+/g,' ').trim();
 const choices=matches.map((m,i)=>clean(q.text.slice(m.index+m[0].length,i<4?matches[i+1].index:q.text.length)));
 if(choices.some(t=>!t || t.length>1800 || /(?:réponse\s*:|correction\s*:|ERRATA|FIN DU SUJET)/i.test(t)))return null;
 const intro=clean(q.text.slice(0,matches[0].index).replace(/^\s*qu[eé]stions?\s*(?:\d+)?\s*(?:\([^)]*\))?\s*[:.\-]?\s*/i,''));
 return {intro,choices};
}
const TOPIC_ALIASES={
 'Génome':'Introduction au génome','Structure des protéines':'Architecture des protéines',
 'Structure-fonction':'Relations structure-fonction','Méthodes d’étude':'Méthodes d’étude des protéines',
 'Réplication':'Réplication et réparation','Régulation':'Régulation de l’expression des gènes',
 'Cycle de Krebs':'Cycle de Krebs et phosphorylation oxydative','Métabolisme des lipides':'Métabolisme et transport des lipides',
 'Biosynthèse des acides gras':'Biosynthèse des acides gras et cétogenèse'
};
const CLASSIFICATION_FIXES={
 'eb-eb-1-21':['biomol','Acides nucléiques'],
 'eb-eb-1-23':['biomol','Techniques de biologie moléculaire'],
 'eb-eb-1-24':['biomol','Techniques de biologie moléculaire'],
 'eb-eb-2-1':['structurale','Acides aminés'],
 'eb-eb-2-9':['biomol','Techniques de biologie moléculaire'],
 'eb-eb-2-10':['biomol','Techniques de biologie moléculaire'],
 'eb-eb-2-12':['biomol','Réplication et réparation'],
 'eb-eb-2-14':['biomol','Transcription'],
 'eb-eb-2-17':['biomol','Régulation de l’expression des gènes'],
 'eb-eb-2-24':['enzymologie','Enzymologie 3'],
 'eb-eb-2-25':['enzymologie','Enzymologie 3'],
 'td-td-1-2':['structurale','Acides aminés'],
 'td-td-1-15':['biomol','Techniques de biologie moléculaire'],
 'td-td-1-16':['biomol','Introduction au génome'],
 'td-td-1-20':['biomol','Transcription'],
 'td-td-1-21':['biomol','Transcription'],
 'td-td-1-25':['biomol','Régulation de l’expression des gènes']
};
export function normalizeQuestion(q){const fixed=CLASSIFICATION_FIXES[q.id];return {...q,chapter:fixed?.[0]||q.chapter,topic:fixed?.[1]||TOPIC_ALIASES[q.topic]||q.topic};}
