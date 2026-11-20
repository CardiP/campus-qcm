"""Non-official, documented supplements to missing or contradictory tutorat keys.
Idempotent; run after extraction/finalization. It does not change source question images.
None marks an ambiguous proposition excluded from automatic scoring.
"""
from pathlib import Path
import json, collections
ROOT=Path(__file__).resolve().parents[1]
COURSES={
 'e1':('COURS/3 Enzymiologie/2525_biochimie_Carnet_Enzymo1_n°13.pdf','Enzymologie 1'),
 'e2':('COURS/3 Enzymiologie/2526_bch_las_carnet_n°14_Enzymologie2-1-1.pdf','Enzymologie 2'),
 'vue':('COURS/4 Métabolisme/carnet_n16_vue_densemble_du_metabolisme-1.pdf','Vue d’ensemble du métabolisme'),
 'krebs':('COURS/4 Métabolisme/2526-biochimie-carnet-n°17-cycle-de-Krebs-et-phosphorylation-oxydative-LAS.pdf','Cycle de Krebs'),
 'gly':('COURS/4 Métabolisme/2526-biochimie-carnet-n°18-digestion-des-glucides-et-glycolyse-LAS.pdf','Glycolyse'),
 'aa':('COURS/1 Biochimie structurale/Carnet20120-20Acide20AmineCC81s20-20LAS.pdf','Acides aminés'),
 'tbm':('COURS/2 Biomol/2526_bch_las_n°8_carnet_techniques-de-biologie-moleculaire.pdf','Techniques de biologie moléculaire')}
def refs(key,pages):
 f,label=COURSES[key];return [{'file':f,'page':p,'label':label} for p in pages]
def ext(label,url):return {'label':label,'url':url}
S={}
def add(id,key,notes,rr,external=()):
 assert len(key)==len(notes)==5,id
 S[id]={'answers':[{'V':True,'F':False,'?':None}[c] for c in key],
 'explanation':'Correction proposée, non officielle, établie à partir des cours fournis.\n\n'+'\n'.join(f'{chr(65+i)}. '+('Neutralisé : ' if key[i]=='?' else 'Vrai : ' if key[i]=='V' else 'Faux : ')+n for i,n in enumerate(notes)),
 'courseReferences':rr,'externalReferences':list(external),'correctionStatus':'unofficial'}
add('banques-enzymologie-2-35','FF?VV',[
 "L’ordre d’une réaction se définit par les exposants de sa loi de vitesse, pas par le nombre de réactifs.",
 "La somme des exposants vaut 1 + 1 = 2 : cette loi est d’ordre global 2.",
 "La vitesse dépend des concentrations, mais « difficile à déterminer » n’est pas une propriété générale définissant l’ordre 2. L’énoncé ne permet pas un jugement binaire fiable.",
 "Dans le cadre présenté page 6, le cours assimile la phase stationnaire linéaire à un ordre 0 par rapport au substrat durant la mesure. Cela ne signifie pas qu’une vitesse initiale serait indépendante de [S] entre toutes les expériences.",
 "Une loi d’ordre zéro par rapport aux réactants considérés ne dépend pas de leur concentration."],refs('e2',[5,6]),[ext('IUPAC · Définition de l’ordre de réaction','https://goldbook.iupac.org/terms/view/O04322')])
add('banques-enzymologie-2-36','VFFFF',[
 "La mesure doit être effectuée à pH et température standardisés ; ces facteurs modifient l’activité.",
 "Le cours distingue une très brève phase pré-stationnaire ; V0 est mesurée dans la phase stationnaire initiale, puis extrapolée vers t = 0.",
 "À [S] = Km, V0 = Vmax/2. La saturation nécessite [S] très supérieur à Km.",
 "La courbe d’une enzyme michaelienne est hyperbolique ; la sigmoïde est caractéristique d’une cinétique coopérative.",
 "V0 se mesure pendant l’état stationnaire initial, pas pendant l’installation pré-stationnaire."],refs('e2',[5,6,7,10,14,15]))
add('banques-enzymologie-2-37','VVFFV',[
 "E + S forme le complexe enzyme-substrat ES.",
 "k+1 caractérise l’association E + S vers ES.",
 "La formation de E + P à partir de ES correspond à k+2 ; k−2 décrit le sens retour.",
 "k+2 décrit précisément la formation de produit. C’est la réaction retour liée à k−2 qui est négligée en conditions de vitesse initiale.",
 "k−1 décrit la dissociation de ES en enzyme et substrat."],refs('e2',[5,9,10]))
add('banques-enzymologie-2-38','FVVVV',[
 "L’équation correcte est V0 = Vmax × [S] / (Km + [S]).",
 "Dans ce modèle simple, Km = (k−1 + k+2) / k+1.",
 "La représentation V0 = f([S]) a une allure d’hyperbole équilatérale.",
 "Pour [S] tendant vers l’infini, V0 tend vers Vmax.",
 "On peut estimer Vmax par l’asymptote, puis Km à Vmax/2 ; le cours précise que cette lecture est peu précise."],refs('e2',[7,10,12]))
add('banques-enzymologie-2-39','FFVFF',[
 "Km a la dimension d’une concentration : mol/L ou un multiple, et non la mole seule.",
 "Km correspond à la concentration donnant la demi-vitesse maximale, pas à la saturation.",
 "Dans l’approximation pédagogique du cours, Km caractérise le couple enzyme-substrat et s’interprète comme un indicateur inverse de l’affinité. Il ne se confond pas en général avec une constante de dissociation pure.",
 "L’égalité correcte est [S] = Km lorsque V0 = Vmax/2 ; Km et une vitesse n’ont pas les mêmes dimensions.",
 "Dans l’interprétation retenue par le cours, un Km plus élevé correspond à une affinité plus faible."],refs('e2',[10,11]))
add('banques-enzymologie-2-40','VVV??',[
 "Dans un mécanisme séquentiel aléatoire bi-bi, les deux substrats peuvent être présents simultanément dans un complexe ternaire.",
 "Le mécanisme séquentiel ordonné passe par un complexe enzyme-premier substrat puis un complexe ternaire.",
 "Dans le mécanisme ping-pong, le premier produit est libéré avant la fixation du second substrat : pas de complexe ternaire réunissant les deux substrats.",
 "L’enzyme précise n’est pas indiquée et les cours fournis ne documentent pas cette généralisation à toutes les déshydrogénases à NAD. La dépendance au NAD seule ne permet pas d’assigner un ordre de fixation.",
 "Un mécanisme ordonné est un exemple classique pour certaines déshydrogénases à NAD, mais l’enzyme n’est pas précisée. Cette affirmation générale est laissée hors score."],refs('e1',[9]),[ext('Mécanismes à plusieurs substrats · modèle enzymatique publié','https://academic.oup.com/bioinformatics/article/21/6/774/199454')])
add('banques-enzymologie-2-41','FVVFF',[
 "Les ions minéraux ne déstabilisent pas systématiquement les enzymes : certains servent de cofacteurs indispensables.",
 "Les cations de métaux lourds peuvent inhiber ou inactiver les enzymes, notamment par interaction avec des groupes fonctionnels essentiels ; cet effet dépend du métal et de l’enzyme.",
 "Pour l’amylase humaine visée ici, « neutre » désigne le pH optimal, voisin de 7, et non sa charge électrique.",
 "La pepsine a un optimum acide, voisin de pH 2.",
 "La trypsine a un optimum alcalin, voisin de pH 8."],refs('e1',[10])+refs('e2',[14]),[ext('Étude de l’alpha-amylase pancréatique humaine · pH et ions','https://pubmed.ncbi.nlm.nih.gov/20029/')])
add('banques-enzymologie-2-42','?F?F?',[
 "La phrase est incomplète : elle ne précise pas la valeur du Km. Le cours recommande un substrat spécifique avec un Km faible.",
 "On privilégie une concentration en substrat élevée, idéalement supérieure à 10 Km, pour approcher la saturation.",
 "« Grand volume » n’est pas défini et aucune règle de ce type n’est donnée dans le cours. La qualité dépend des conditions standardisées et de la mesure, pas d’un grand volume en soi.",
 "On mesure l’apparition du produit ou la disparition du substrat EN FONCTION du temps mesuré séparément ; la vitesse du produit ne remplace pas un chronomètre.",
 "Le dosage doit rester dans le domaine de vitesse initiale pendant sa fenêtre de mesure. « À la fin » peut désigner la fin du dosage ou l’achèvement de la réaction, deux situations différentes : formulation non notée."],refs('e2',[16,17]))
add('banques-enzymologie-2-43','VVV??',[
 "L’unité enzymatique U correspond à 1 µmol de substrat transformée par minute. Le cours signale que l’appellation UI est souvent employée abusivement.",
 "Un katal correspond à une activité de 1 mol de substrat transformée par seconde dans des conditions définies.",
 "À saturation, kcat exprime le nombre de cycles catalytiques par enzyme et par unité de temps ; en s−1, il s’agit du nombre par seconde.",
 "L’activité spécifique est une activité rapportée à une masse de protéines, souvent en U/mg = µmol/min/mg. mol/min/mg est dimensionnellement possible avec conversion ; on ne peut la déclarer fausse seulement parce que le préfixe µ manque.",
 "« Variation d’énergie » ne distingue pas énergie d’activation et variation d’énergie libre de réaction. Un effecteur accélère la réaction sans modifier son équilibre thermodynamique ; l’énoncé est trop imprécis."],refs('e2',[11,16,17]))
add('banques-enzymologie-2-44','VFFVV',[
 "Le cours décrit des liaisons covalentes ou quasi covalentes pour les inhibiteurs irréversibles.",
 "Le DIFP est lui-même un inhibiteur enzymatique, pas l’enzyme cible du méthotrexate ; celui-ci inhibe la dihydrofolate réductase.",
 "L’inhibition compétitive augmente le Km apparent mais laisse Vmax inchangée.",
 "Un inhibiteur incompétitif se fixe sur le complexe enzyme-substrat ES.",
 "L’inhibition non compétitive pure diminue Vmax, sans modifier Km."],refs('e2',[17,18,19,20,21,22]))
add('banques-vue-metabolisme-11','VVFVF',[
 "L’anabolisme consomme de l’énergie pour construire des molécules complexes.",
 "Les réactions cataboliques produisent notamment NADH et FADH2.",
 "Le cycle de Krebs est amphibolique : ses intermédiaires servent aussi à des biosynthèses.",
 "Une voie amphibolique participe à des fonctions cataboliques et anaboliques.",
 "La β-oxydation est une voie de dégradation des acides gras, donc catabolique."],refs('vue',[5,6,7])+refs('krebs',[11]))
add('banques-vue-metabolisme-12','V?V?F',[
 "La glycolyse produit directement de l’ATP par phosphorylation au niveau du substrat.",
 "Le cours détaillé fait produire du GTP au cycle de Krebs, convertible en ATP, tandis que le résumé parle d’énergie sous forme d’ATP. La question ne précise pas production directe ou équivalent énergétique ; elle n’est pas notée sur ce point.",
 "Le transfert d’électrons couplé à l’ATP synthase permet la phosphorylation oxydative.",
 "La β-oxydation ne synthétise pas directement d’ATP ; elle fournit des équivalents réducteurs et de l’acétyl-CoA permettant d’en produire ensuite. L’absence de « directement » rend l’item ambigu.",
 "La voie des pentoses phosphates fournit notamment NADPH et ribose-phosphate ; elle n’est pas une voie productrice d’ATP."],refs('vue',[5,6,7])+refs('krebs',[5,9,11]))
add('banques-vue-metabolisme-13','VV??F',[
 "Le foie est un réservoir majeur de glycogène selon le cours.",
 "Les muscles squelettiques constituent l’autre grand réservoir de glycogène présenté dans le cours.",
 "Le cours simplifie les réserves principales au foie et aux muscles, mais le cerveau contient du glycogène, notamment astrocytaire. La formulation « peut être stocké » est plus large : item hors score.",
 "Le tissu adipeux stocke principalement des triglycérides, mais du glycogène adipocytaire existe. La formulation absolue du QCM ne permet pas d’utiliser sans nuance le résumé du cours : item hors score.",
 "Les globules rouges matures ne constituent pas un tissu de réserve glycogénique dans le cadre de ce cours ; leur ATP provient du glucose via la glycolyse."],refs('vue',[6])+refs('gly',[7]),[ext('Étude primaire · Glycogène astrocytaire','https://pmc.ncbi.nlm.nih.gov/articles/PMC7530046/'),ext('Étude primaire · Glycogène dans les adipocytes humains','https://pmc.ncbi.nlm.nih.gov/articles/PMC4703799/')])
add('banques-vue-metabolisme-14','FVVVF',[
 "Dans le bilan classique des acides gras à nombre pair retenu ici, l’acétyl-CoA n’entraîne pas de production nette de glucose. Les acides gras impairs constituent une exception via le propionyl-CoA ; cette correction suit le cadre général du cours.",
 "Leur oxydation fournit de l’énergie permettant la synthèse d’ATP.",
 "L’acétyl-CoA issu des acides gras peut alimenter la cétogenèse hépatique.",
 "L’acétyl-CoA est un précurseur du cholestérol.",
 "La β-oxydation habituelle produit de l’acétyl-CoA, pas du pyruvate ; on raisonne ici sur les voies directes décrites dans le cours."],refs('vue',[7,8])+refs('gly',[11]))
add('banques-vue-metabolisme-17','FFFVV',[
 "Dans le vocabulaire large du tableau de cours page 9, « glycolyse aérobie » inclut la glycolyse cytosolique puis le devenir mitochondrial du pyruvate. Au sens biochimique strict, les réactions de glycolyse seules restent cytosoliques : c’est la convention du cours qui est retenue ici.",
 "L’uréogenèse comporte des étapes mitochondriales et cytosoliques.",
 "La phosphorylation oxydative se déroule au niveau de la membrane mitochondriale interne, pas dans le cytosol.",
 "La cétogenèse décrite dans le cours est mitochondriale et hépatique.",
 "La néoglucogenèse mobilise des étapes cytosoliques et mitochondriales ; sa dernière étape implique également le réticulum endoplasmique."],refs('vue',[9]))
add('banques-krebs-17','VVVVF',[
 "Selon la convention de rendement utilisée par ce cours, un NADH,H+ correspond à environ 3 ATP. D’autres conventions modernes utilisent des rendements inférieurs ; on applique ici celle du support d’examen.",
 "Le cours retient environ 2 ATP par FADH2.",
 "L’ATP synthase comporte une partie transmembranaire dans la membrane mitochondriale interne.",
 "Le dioxygène reçoit les électrons en fin de chaîne et est réduit en eau.",
 "La phosphorylation oxydative est associée à la membrane mitochondriale interne ; ce n’est pas une réaction libre dans la matrice."],refs('krebs',[9,10,11]))
add('banques-krebs-30','VFVFV',[
 "Le FADH2 alimente la chaîne respiratoire en électrons.",
 "Le FADH2 lié à la succinate déshydrogénase est réoxydé au complexe II, pas au complexe IV.",
 "La succinate déshydrogénase constitue le complexe II.",
 "Une réoxydation de FADH2 libère deux électrons, pas six.",
 "Le cours indique le pompage de 6 H+ et retient un rendement conventionnel de 2 ATP. Cette clé concorde aussi avec la grille du corrigé, page 2, malgré les espaces réservés laissés dans le corrigé détaillé."],refs('krebs',[11]))
add('banques-glycolyse-13','VVVFV',[
 "Certaines réactions de glycolyse produisent directement de l’ATP par phosphorylation au niveau du substrat.",
 "Le pyruvate est réduit en lactate dans le cytosol lors de la glycolyse anaérobie.",
 "Dans le vocabulaire du cours, le devenir aérobie du pyruvate conduit à l’acétyl-CoA par la pyruvate déshydrogénase mitochondriale. Cette étape suit la glycolyse stricte, dont le produit final est le pyruvate.",
 "La glycolyse elle-même est cytosolique.",
 "Les érythrocytes matures n’ont pas de mitochondries et dépendent de la glycolyse pour leur ATP."],refs('gly',[7,8,9,10,11]))
add('eb-eb-1-25','FVF?V',[
 "Les enzymes de restriction usuelles sont des endonucléases : elles clivent à l’intérieur de l’ADN.",
 "L’ADN est un polyanion et migre vers l’anode positive.",
 "Un doublement à chaque cycle donne une croissance exponentielle idéale, pas linéaire.",
 "Le support emploie « archébactérie », mais la Taq polymérase provient de Thermus aquaticus, classée parmi les bactéries. L’item mélange une origine taxonomique erronée et une thermostabilité correcte ; il est neutralisé à cause du conflit entre cours et connaissance établie.",
 "Les étapes sont dénaturation, hybridation des amorces puis extension. Les températures indiquées sont des valeurs usuelles, ajustables selon les amorces et l’enzyme."],refs('tbm',[7,10,11]),[ext('NCBI Taxonomy · Thermus aquaticus, domaine Bacteria','https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=271&mode=Info'),ext('NCBI MeSH · Taq Polymerase','https://www.ncbi.nlm.nih.gov/mesh?Cmd=DetailsSearch&Db=mesh&Term=%22Taq+Polymerase%22%5BMeSH+Terms%5D')])
add('td-td-1-3','FVVFF',[
 "L’interprétation attendue du schéma est la lysine, avec pK1 ≈ 2, pK2 ≈ 9 et pKr ≈ 10,8. Le corrigé détaillé nomme lui-même la lysine : la mention OUI devant « tyrosine » est incohérente.",
 "Le deuxième palier se trouve vers pH 9 et correspond à pK2.",
 "La lysine est un acide aminé basique, chargé positivement à pH physiologique.",
 "Le pI se situe entre les deux derniers pKa, au point 5, pas au point 4.",
 "pI = (9 + 10,8)/2 = 9,9 pour l’acide aminé visé, pas 5,5."],refs('aa',[16,19,20,21,22,23]))

p=ROOT/'public/data/banques.json';data=json.loads(p.read_text())
assert len(S)==20
for q in data:
 if q['id'] in S:
  q.setdefault('sourceExplanation',q.get('explanation',''))
  q.setdefault('sourceAnswers',q.get('answers'))
  q.setdefault('sourceCorrectionStatus',q.get('correctionStatus'))
  q.update(S[q['id']])
# Explicit topic review of cross-chapter EB and TD; no keyword-based false assignments.
TOPICS={
 'eb-eb-1':['Acides aminés']*5+['Architecture des protéines']*5+['Méthodes d’étude']*4+['Structure-fonction']*2+['Techniques de biologie moléculaire']+['Acides nucléiques']*5+['Techniques de biologie moléculaire']*3,
 'eb-eb-2':['Acides aminés']*3+['Architecture des protéines']*2+['Méthodes d’étude']*2+['Structure-fonction']+['Techniques de biologie moléculaire']*2+['Réplication']*2+['Transcription']*2+['Traduction']*2+['Régulation']*2+['Enzymologie 1']*2+['Enzymologie 2']*3+['Enzymologie 3']*2,
 'td-td-1':['Acides aminés']*3+['Architecture des protéines']*3+['Méthodes d’étude']*3+['Structure-fonction']*2+['Génome']+['Acides nucléiques']*2+['Techniques de biologie moléculaire']+['Génome']+['Techniques de biologie moléculaire']+['Réplication']*2+['Transcription']*2+['Traduction']*2+['Régulation']*2}
for source,topics in TOPICS.items():
 assert len(topics)==25,(source,len(topics))
 for q in data:
  if q['sourceId']==source:
   topic=topics[q['number']-1];q['topic']=topic
   q['chapter']='enzymologie' if topic.startswith('Enzymologie') else 'structurale' if topic in ['Acides aminés','Architecture des protéines','Méthodes d’étude','Structure-fonction'] else 'biomol'
for q in data:
 assert q['answers'] is not None and len(q['answers'])==5,q['id']
 assert all(v is None or isinstance(v,bool) for v in q['answers']),q['id']
 for r in q.get('courseReferences',[]):assert (ROOT.parent/r['file']).is_file(),r
p.write_text(json.dumps(data,ensure_ascii=False,indent=2))
report={'total':len(data),'statuses':dict(collections.Counter(q['correctionStatus'] for q in data)),'supplements':len(S),'neutralizedItems':sum(v is None for q in data for v in q['answers']),'neutralizedByQuestion':{q['id']:[chr(65+i) for i,v in enumerate(q['answers']) if v is None] for q in data if None in q['answers']}}
(ROOT/'tmp/banques-supplements-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
