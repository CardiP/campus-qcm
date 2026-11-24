# Campus QCM — Semestre 1

**Site en ligne : [cardip.github.io/campus-qcm](https://cardip.github.io/campus-qcm/)**

Site de révision adapté au téléphone et au PC, créé à partir des documents de biochimie, d’anatomie et de médicament fournis.

- Biochimie : 869 QCM — 130 annales (2020–2025), 50 examens blancs, 25 TD et 664 questions des banques.
- Filtrage par type, document, domaine et chapitre ; mélange et sélection de la longueur de session.
- Mode Révision : correction après validation des cinq propositions.
- Mode Annale : réponses modifiables, correction uniquement après remise de la session.
- Énoncés et schémas d’origine agrandissables, transcription de lecture lorsqu’elle est exploitable.
- Annales accompagnées de corrections **non officielles**, rédigées d’après les cours et accompagnées de leurs références.
- QCM dont une réponse reste ambiguë accessibles, avec explication, mais exclus du score.
- Progression, reprise de session, travail des erreurs et import/export des sauvegardes.
- Anatomie : 1 261 QCM — 988 questions de banques, 175 annales, 70 examens blancs et 28 TD. Les 58 PDF du dossier fourni sont inventoriés.
- Médicament : 1 007 QCM distincts issus des banques, des examens blancs, des annales et des ACC fournis ; 502 occurrences répétées sont regroupées. Le S2 reste à créer.

Les données personnelles sont conservées dans le navigateur (`localStorage`). La sauvegarde JSON permet de les transférer entre appareils. Il n’y a ni compte ni synchronisation automatique. Les imports personnels ne modifient pas le site partagé.

## Utilisation locale

```sh
npm start
```

Ouvrir `http://localhost:4173`. Python 3 suffit pour servir le site. Il n’y a pas de compilation ni de dépendance JavaScript nécessaire à l’exécution.

```sh
npm test
node scripts/validate-data.mjs
```

## Publication GitHub Pages

Le code source est dans `main`, et le contenu de `public/` est publié à la racine de `gh-pages`. Le fichier `.nojekyll` conserve le site statique tel quel.

Après une modification :

```sh
git add public scripts tests package.json README.md
git commit -m "Mettre à jour Campus QCM"
git push origin main
git subtree split --prefix public -b pages-update
git push origin pages-update:gh-pages
git branch -D pages-update
```

## Données et corrections

Les JSON sous `public/data/` référencent les images sous `public/assets/`. Chaque question porte sa source, ses pages, son chapitre, cinq réponses (ou une valeur `null` pour une ambiguïté), une explication et le statut de correction. Un QCM n’est noté que lorsque les cinq réponses sont établies et qu’aucun schéma nécessaire n’est signalé manquant. Le score d’entraînement attribue un point par QCM entièrement exact ; ce n’est pas un barème universitaire.

Les scripts Python d’extraction nécessitent les PDF originaux dans le dossier parent du projet, ainsi que PyMuPDF et Pillow. Les cours extraits sont attendus dans `../tmp/anki/extracted/`. Ils ne sont pas nécessaires pour utiliser ou publier le site déjà généré. Les ajustements des chapitres pour les EB/TD et l’unification des intitulés sont explicités dans `public/core.js`.

Les corrections non officielles restent distinctes de celles des documents. Les ambiguïtés et les différences entre une grille et son corrigé détaillé ne sont pas masquées.

## Import Anatomie

L’import conserve toutes les questions des 24 banques, des deux examens blancs, des cinq annales et du TD fournis. Les deux exercices non QCM du TD sont adaptés en trois QCM explicitement signalés. Les archives qui recommencent la numérotation gardent des identifiants distincts ; les répétitions présentes dans plusieurs documents sont conservées.

Les 266 corrections rédigées ou réexaminées avec les 37 carnets détaillent les cinq propositions. Les trois adaptations du TD sont également expliquées. Elles sont marquées **non officielles** et indiquent les carnets utilisés. Les corrections imprimées restent consultables après validation, y compris lorsqu’une incohérence a été corrigée. Les propositions à confirmer (24 QCM) et les quatre questions privées de leur schéma dans les documents fournis sont exclues du score. La question 40 factice du corrigé de la banque 18, constituée de « Item 196…200 / Justification » et absente du sujet, n’est pas proposée.

Le classement suit la numérotation des banques récentes, qui ajoutent l’innervation du membre pelvien en 16 : les chapitres suivants sont donc décalés d’un rang par rapport aux 37 carnets anciens. Les références de correction conservent les numéros réels des fichiers `anatomie_N.pdf`.

Les sources, empreintes SHA-256, pages, associations sujet-corrigé et cas particuliers sont consignés dans `scripts/data/anatomie-import-report.json`. Les corrections revues sont dans `scripts/data/anatomie-corrections.txt`. Les énoncés WebP ne contiennent pas les corrections : celles-ci sont chargées dans une section distincte après validation.

Pour reproduire l’import avec les mêmes PDF, installer PyMuPDF et Pillow dans un environnement Python, puis exécuter depuis la racine du dépôt :

```sh
python scripts/anatomie_extract.py "/chemin/qcm anat" /tmp/campus-anat --render
python scripts/anatomie_annales_extract.py "/chemin/qcm anat" /tmp/campus-anat --render
python scripts/anatomie_build.py /tmp/campus-anat "/chemin/aux/37-carnets"
npm test
node scripts/validate-data.mjs
```

Le PDF scanné de 2020–2021 utilise la transcription OCR locale et ses coordonnées conservées dans `scripts/data/anatomie-2021-ocr.json`. Les PDF originaux et les cours ne sont pas nécessaires pour utiliser le site déjà généré.

## Import Médicament

Les dossiers `qcm medicament`, `ACC MED` et `ACC MEDS PASS`, ainsi que leurs copies dans `MEDS`, sont inventoriés par empreinte SHA-256. Les 92 PDF uniques de QCM et corrigés sont pris en compte. Les 1 509 occurrences exploitables donnent 1 007 QCM distincts. Les 80 copies identiques de fichiers de l’ensemble QCM/cours ne sont pas réimportées. Les questions supplémentaires complètes trouvées uniquement dans un corrigé sont également récupérées.

Chaque question conserve toutes ses provenances. Un filtre de document retrouve la question dans l’ordre de ce document ; une session mélangée ne la répète pas. Les cinq annales contiennent chacune 28 questions. Des variantes qui changent un chiffre, une négation, un contexte ou la consigne exacte/inexacte restent distinctes. Les tableaux communs et les données des questions précédentes accompagnent les questions dépendantes.

83 corrections sont complétées ou arbitrées et marquées **non officielles**, avec références aux carnets. Les questions biologiques qui dépassent les cours fournis indiquent aussi leurs références institutionnelles complémentaires. Neuf questions comportent au moins un item ambigu : toutes leurs propositions sont discutées, mais elles sont exclues du score. Les 302 QCM disposant uniquement d’une grille fournie l’indiquent explicitement ; aucune justification détaillée n’est attribuée à tort au document.

Le rapport `scripts/data/medicament-import-report.json` conserve inventaire, groupes de doublons, différences entre corrections et provenance des occurrences. Les choix manuels de transcription, fusion et correction sont versionnés sous `scripts/data/medicament-*.json` ; le générateur lisible des corrections est `scripts/medicament_curate.py`. Les mises en page et transcriptions OCR sont archivées dans `medicament-layout-cache.json.gz`, sans nécessiter de service OCR externe pour reconstruire. Les PDF originaux ne sont pas inclus dans le dépôt.

Reconstruction avec les mêmes dossiers sous un répertoire commun (PyMuPDF et Pillow requis) :

```sh
python scripts/medicament_import.py "/chemin/Downloads" /tmp/campus-meds
npm test
node scripts/validate-data.mjs
```
