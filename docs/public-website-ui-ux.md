# ORSC — Public Website UI/UX

## 1. Introduction

Ce document définit l'interface utilisateur (UI) et l'expérience utilisateur (UX) du site web public du **Operations Research Society Club (ORSC)**.

Le site public constitue la partie visible du projet par les visiteurs, étudiants, enseignants, partenaires, sponsors et personnes intéressées par le club.

Il doit présenter l'identité du club, ses activités, ses projets, ses événements, ses membres, ses partenaires et ses différentes ressources.

Le site doit également permettre à une personne intéressée de consulter les informations du club et, lorsque les inscriptions sont ouvertes, de déposer une candidature pour rejoindre le club.


## 2. Objectifs de l'interface

L'interface du site public doit :

- présenter clairement le club ;
- donner une image moderne et professionnelle de l'ORSC ;
- permettre une navigation simple ;
- mettre en valeur les activités du club ;
- présenter les départements ;
- présenter les projets ;
- présenter les événements ;
- présenter les articles ;
- présenter les organisations et partenaires ;
- présenter les photos et vidéos ;
- permettre aux visiteurs de rejoindre le club ;
- fonctionner correctement sur ordinateur et mobile ;
- proposer un mode Light et un mode Dark ;
- utiliser des animations modernes sans rendre l'interface difficile à utiliser.


## 3. Principes UX

L'expérience utilisateur doit respecter les principes suivants :

### 3.1 Simplicité

Les informations importantes doivent être facilement accessibles.

Le visiteur ne doit pas avoir besoin de parcourir plusieurs pages pour comprendre :

- ce qu'est l'ORSC ;
- ce que fait le club ;
- quelles sont ses activités ;
- comment rejoindre le club.

### 3.2 Hiérarchie visuelle

Les informations doivent être organisées selon leur importance.

Les éléments principaux doivent être immédiatement visibles :

- identité ORSC ;
- message principal ;
- actions principales ;
- événements ;
- activités ;
- projets.

### 3.3 Navigation claire

La navigation doit rester simple et cohérente sur toutes les pages.

### 3.4 Responsive

Le site doit être adapté aux :

- ordinateurs ;
- laptops ;
- tablettes ;
- smartphones.

### 3.5 Accessibilité

Les textes doivent rester lisibles.

Les boutons doivent être suffisamment grands pour être utilisés facilement sur mobile.

Les animations ne doivent pas empêcher la lecture du contenu.


## 4. Identité visuelle

L'identité visuelle du site doit être basée sur l'identité graphique officielle de l'ORSC.

Les éléments principaux sont :

- logo ORSC ;
- formes graphiques inspirées du logo ;
- éléments liés aux réseaux, connexions et recherche opérationnelle ;
- couleurs principales du club ;
- typographie moderne ;
- espaces suffisamment larges entre les éléments.

L'identité visuelle doit rester cohérente entre :

- le site public ;
- le CMS ;
- le mode Light ;
- le mode Dark.


## 5. Modes Light et Dark

Le site doit proposer deux thèmes :

- Light Mode ;
- Dark Mode.

### 5.1 Light Mode

Le Light Mode utilise une interface claire avec :

- arrière-plan clair ;
- cartes claires ;
- texte sombre ;
- couleurs principales de l'identité ORSC ;
- contrastes suffisants.

### 5.2 Dark Mode

Le Dark Mode utilise :

- arrière-plan sombre ;
- cartes légèrement plus claires que l'arrière-plan ;
- texte clair ;
- couleurs principales ORSC utilisées comme accents ;
- effets lumineux pour certaines animations.

### 5.3 Changement de thème

Un bouton permettant de changer le thème doit être accessible depuis la navigation.

Le changement doit être fluide.

Le choix de l'utilisateur doit être conservé pendant sa navigation.


## 6. Responsive Design

Le site doit être conçu selon une approche responsive.

### 6.1 Desktop

Sur ordinateur :

- navigation horizontale ;
- sections larges ;
- plusieurs cartes affichées côte à côte ;
- grandes images ;
- animations visibles ;
- espaces importants entre les sections.

### 6.2 Mobile

Sur smartphone :

- navigation compacte ;
- menu hamburger ou menu mobile ;
- contenu organisé verticalement ;
- cartes empilées ;
- boutons adaptés à l'écran tactile ;
- images redimensionnées ;
- textes adaptés à la largeur de l'écran.

Aucun élément important ne doit être coupé horizontalement.

### 6.3 Tablette

La mise en page doit s'adapter entre la version mobile et desktop.

Le nombre de colonnes peut être réduit automatiquement selon la largeur disponible.


## 7. Navigation principale

La navigation principale doit être présente sur toutes les pages importantes du site.

Elle contient :

- Logo ORSC ;
- Accueil ;
- Découvrir le club ;
- Départements ;
- Projets ;
- Événements ;
- Articles ;
- Organisations ;
- Media ;
- Rejoindre le club ;
- bouton Light / Dark.

La navigation doit rester cohérente entre les pages.

### 7.1 Desktop

La navigation est affichée horizontalement.

Le logo se trouve à gauche.

Les liens sont placés au centre ou à droite.

Le bouton « Rejoindre le club » doit être visuellement mis en valeur.

### 7.2 Mobile

La navigation devient compacte.

Le logo reste visible.

Les autres éléments sont accessibles depuis un menu mobile.


## 8. Page d'accueil

La page d'accueil est la page principale du site public.

Elle doit donner immédiatement une vision du club et permettre au visiteur de découvrir les principales sections.

Structure générale :

```text
Navigation
    ↓
Hero
    ↓
Statistiques
    ↓
Présentation du club
    ↓
Départements
    ↓
Prochains événements
    ↓
Projets
    ↓
Articles
    ↓
Organisations / Partenaires
    ↓
Media
    ↓
Sponsors
    ↓
Call To Action
    ↓
Footer



Réseau graphique
    ↓
Lumière se déplace sur les branches
    ↓
La lumière atteint certains points
    ↓
Petit effet lumineux / ombre
    ↓
La lumière continue son parcours



Période ouverte
    ↓
Formulaire de candidature

Période fermée
    ↓
Page « Inscriptions fermées »



Date actuelle
    ↓
Recherche des événements futurs
    ↓
Tri par date
    ↓
Affichage des prochains événements




Liste des événements
    ↓
Sélection d'un événement
    ↓
Page / section de détail



Liste des articles
    ↓
Sélection
    ↓
Page article
    ↓
Lecture



Media
├── Photos
└── Vidéos



Vous souhaitez rejoindre l'ORSC ?
        ↓
[ Rejoindre le club ]



Visiteur
    ↓
Rejoindre le club
    ↓
Vérification de la période




Rejoindre le club
    ↓
Inscriptions fermées




Rejoindre le club
    ↓
Présentation courte
    ↓
Formulaire de candidature




Candidat
    ↓
Remplit le formulaire
    ↓
Validation des champs



Erreur
    ↓
Message affiché près du champ concerné
    ↓
Correction



Formulaire valide
    ↓
Envoi
    ↓
Candidature enregistrée





Chargement
    ↓
Skeleton / Loading state
    ↓
Données disponibles
    ↓
Contenu affiché



Aucun contenu disponible




Erreur
    ↓
Message compréhensible
    ↓
Possibilité de réessayer





Titre principal
    ↓
Titre de section
    ↓
Sous-titre
    ↓
Texte courant
    ↓
Texte secondaire





Point de départ
      ↓
Lumière
      ↓
Déplacement sur une branche
      ↓
Intersection
      ↓
Effet lumineux
      ↓
Nouvelle branche
      ↓
Continuation




CMS
   ↓
Backend Flask
   ↓
SQLite
   ↓
Données
   ↓
Site public




Logo / Menu
    ↓
Hero
    ↓
Statistiques
    ↓
Présentation
    ↓
Départements
    ↓
Événements
    ↓
Projets
    ↓
Articles
    ↓
Organisations
    ↓
Media
    ↓
Sponsors
    ↓
Call To Action
    ↓
Footer





Navigation horizontale
    ↓
Hero large
    ↓
Statistiques en ligne
    ↓
Sections avec plusieurs colonnes
    ↓
Galeries et cartes
    ↓
Call To Action
    ↓
Footer





Tu peux maintenant **:contentReference[oaicite:1]{index=1}**. Ensuite, on passera au dernier gros document de conception : **`cms-ui-ux.md`**, qui sera beaucoup plus détaillé parce qu'il doit couvrir les interfaces et permissions des différents rôles du CMS. 