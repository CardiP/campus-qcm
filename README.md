# Campus QCM — Semestre 1

Site de révision adapté au téléphone et au PC, créé à partir des documents de biochimie fournis.

- 869 QCM : 130 annales (2020–2025), 50 examens blancs, 25 TD et 664 questions des banques.
- Filtrage par type, document, domaine et chapitre ; mélange et sélection de la longueur de session.
- Mode Révision : correction après validation des cinq propositions.
- Mode Annale : réponses modifiables, correction uniquement après remise de la session.
- Énoncés et schémas d’origine agrandissables, transcription de lecture lorsqu’elle est exploitable.
- Annales accompagnées de corrections **non officielles**, rédigées d’après les cours et référencées par page.
- QCM dont une réponse reste ambiguë accessibles, avec explication, mais exclus du score.
- Progression, reprise de session, travail des erreurs et import/export des sauvegardes.
- Espaces Anatomie et Médicament prêts pour les imports JSON et la saisie de questions. Le S2 reste à créer.

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

Les JSON sous `public/data/` référencent les images sous `public/assets/`. Chaque question porte sa source, ses pages, son chapitre, cinq réponses (ou une valeur `null` pour une ambiguïté), une explication et le statut de correction. Un QCM n’est noté que lorsque les cinq réponses sont établies. Le score d’entraînement attribue un point par QCM entièrement exact ; ce n’est pas un barème universitaire.

Les scripts Python d’extraction nécessitent les PDF originaux dans le dossier parent du projet, ainsi que PyMuPDF et Pillow. Les cours extraits sont attendus dans `../tmp/anki/extracted/`. Ils ne sont pas nécessaires pour utiliser ou publier le site déjà généré. Les ajustements des chapitres pour les EB/TD et l’unification des intitulés sont explicités dans `public/core.js`.

Les corrections non officielles restent distinctes de celles des documents. Les ambiguïtés et les différences entre une grille et son corrigé détaillé ne sont pas masquées.
