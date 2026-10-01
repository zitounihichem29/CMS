# ORSC — CMS UI/UX

## 1. Introduction

Ce document définit l'interface utilisateur (UI) et l'expérience utilisateur (UX) du **Club Management System (CMS)** de l'Operations Research Society Club (ORSC).

Le CMS constitue l'espace interne du club.

Il permet aux membres et responsables de :

- consulter les informations du club ;
- gérer les membres ;
- gérer les départements ;
- gérer les projets ;
- gérer les articles ;
- gérer les événements ;
- gérer les tâches ;
- consulter et gérer les templates selon leurs permissions ;
- gérer les annonces ;
- gérer les formations ;
- gérer les organisations ;
- gérer les candidatures ;
- gérer certaines réunions ;
- consulter les notifications ;
- gérer certaines informations selon leurs permissions.

L'interface doit adapter les fonctionnalités accessibles au rôle de l'utilisateur.


## 2. Objectifs de l'interface

Le CMS doit être :

- clair ;
- organisé ;
- professionnel ;
- moderne ;
- rapide à comprendre ;
- responsive ;
- cohérent avec l'identité ORSC ;
- utilisable sur ordinateur et mobile.

L'utilisateur doit pouvoir accéder rapidement aux informations importantes sans parcourir inutilement plusieurs pages.


## 3. Rôles du CMS

Le CMS possède cinq niveaux principaux de permissions :

1. Member
2. Sub-Head of Department
3. Head of Department
4. Head RH
5. President / Vice-President

Les permissions sont associées au rôle de l'utilisateur.

```text
Member
   ↓
Sub-Head
   ↓
Head of Department
   ↓
Head RH
   ↓
President / Vice-President










┌───────────────────────────────────────────────┐
│                    HEADER                     │
├───────────────┬───────────────────────────────┤
│               │                               │
│    SIDEBAR    │          CONTENT              │
│               │                               │
│               │                               │
│               │                               │
└───────────────┴───────────────────────────────┘














Accueil
Tableau de bord
Membres
Départements
Projets
Articles
Événements
Tâches
templates
Annonces
Formations
Organisations
Media
Paramètres











┌───────────────────────────────────────────────┐
│ Menu │ Page actuelle │ Année │ 🔔 │ Profil  │
└───────────────────────────────────────────────┘










Sarah BELHADJ
Head of Projects & Activities



Mon profil
Paramètres
Déconnexion










Année :
[ 2026 - 2027 ▼ ]










Logo ORSC

Bienvenue

Username ou Email
[________________]

Mot de passe
[________________]

[ Se connecter ]

Mot de passe oublié












[ Connexion... ]



Username/email ou mot de passe incorrect.



Login
   ↓
Authentification
   ↓
Identification du rôle
   ↓
CMS











Département : Projects & Activities

Membres        12
Tâches         25
Terminées      18
En cours        5
En retard       2
Projets         4










┌──────────────┐
│ Membres      │
│     42       │
└──────────────┘

┌──────────────┐
│ Projets      │
│     08       │
└──────────────┘

┌──────────────┐
│ Événements   │
│     15       │
└──────────────┘












Recherche [________________]

Département [Tous ▼]
Rôle        [Tous ▼]
Statut      [Tous ▼]

------------------------------------------------
Nom             Département       Rôle     Statut
------------------------------------------------
...






Membres
   ↓
Sélection d'un membre
   ↓
Profil membre






Nom du département

Mission
Description

Responsable

Membres

Tâches

Activités

Projets associés

Événements associés









Projets
   ↓
Ajouter un projet
   ↓
Formulaire






Formulaire
   ↓
Validation
   ↓
Projet enregistré
   ↓
Projet visible selon les permissions







Articles
   ↓
Ajouter un article
   ↓
Informations de l'article
   ↓
Auteurs
   ↓
Sources
   ↓
Enregistrement





Formulaire
   ↓
Validation
   ↓
Événement créé











À faire
En cours
Terminée
En retard









Tâches
   ↓
Ajouter une tâche
   ↓
Titre
Description
Membre(s) assigné(s)
Date limite
Priorité
   ↓
Créer









Tâche
   ↓
Task Assignees
   ↓
Membre(s)








Templates
   ↓
Liste des templates
   ↓
Consultation par les utilisateurs autorisés
   ↓
Télécharger un fichier
ou
Ouvrir un template Canva / Figma


External Relations non concerné
   ↓
Aucune action de gestion


RH Member / Sub-Head / Head
   ↓
Templates
   ↓
Ajouter un template
   ↓
Choisir le type
   ├── PDF / Word / Excel / PowerPoint
   │       ↓
   │   Sélectionner le fichier
   │
   └── Canva / Figma
           ↓
       Ajouter le lien externe
   ↓
Enregistrer
   ↓
Template disponible


RH Member / Sub-Head / Head
   ↓
Template existant
   ↓
Supprimer
   ↓
Template retiré










Annonces
   ↓
Ajouter une annonce
   ↓
Titre
Contenu
   ↓
Publier







Formation
   ↓
Participants
   ↓
Membre
   ↓
Présent / absent







Photos
Vidéos





Ajouter
   ↓
Sélectionner le fichier
   ↓
Ajouter les informations
   ↓
Enregistrer


Organizations
   ↓
Liste des organisations
   ↓
Cards
   ├── Logo
   ├── Nom
   └── Type


Accès selon le profil
   ↓
External Relations Member
   ├── Ouvrir une organisation
   ├── Voir les informations complètes
   └── Voir Relationship History

External Relations Head / Sub-Head
   ├── Ouvrir une organisation
   ├── Ajouter une organisation
   ├── Modifier une organisation
   ├── Supprimer une organisation
   └── Gérer Relationship History

Autres départements
   └── Liste uniquement

Alumni
   └── Liste uniquement


Organization Details
   ↓
Logo + Nom + Type
   ↓
Organization Information
   ├── Description
   ├── Address
   ├── Website
   ├── Email
   └── Phone
   ↓
Relationship History
   ├── Academic Year
   ├── Relation Type
   ├── Start Date
   ├── End Date
   └── Description


Head / Sub-Head External Relations
   ↓
Relationship History
   ├── Add Relationship
   ├── Edit Relationship
   └── Delete Relationship


Applications

Toutes
En attente
Acceptées
Rejetées










Applications

Toutes
En attente
Acceptées
Rejetées










Applications
   ↓
Candidature
   ↓
Détails







[ Accepter ]
[ Rejeter ]
[ Organiser une rencontre ]











Head RH
   ↓
Accepter
   ↓
Confirmation
   ↓
Génération d'un token sécurisé unique
   ↓
Email envoyé
   ↓
Candidat reçoit le lien sécurisé
   ↓
Vérification du token
   ↓
Deuxième formulaire
   ↓
Création USER + MEMBERSHIP
   ↓
Token supprimé
   ↓
Lien inutilisable après utilisation








Head RH
   ↓
Rejeter
   ↓
Confirmation
   ↓
Email envoyé
   ↓
Candidat informé













Candidature
   ↓
Organiser une rencontre
   ↓
Date
Heure
Participants
Informations
   ↓
Créer la réunion










Nouvelle tâche assignée
Nouvel événement
Nouvelle annonce
Modification importante
Invitation à une réunion









🔔 3



Profil
Sécurité
Notifications
Apparence





Département
Rôle
Année
Statut
Date
Type








Chargement...






Aucun résultat



Aucune tâche pour le moment.
Aucun événement trouvé.
Aucun projet disponible.
Aucune candidature.






Une erreur est survenue.
Veuillez réessayer.






[ Réessayer ]







Désactiver ce compte ?

Cette action empêchera l'utilisateur de se connecter.

[ Annuler ]    [ Confirmer ]









Member
    ↓
Voir projet
    ↓
Pas de bouton « Ajouter »







Head Projects & Activities
    ↓
Voir projets
    ↓
[ Ajouter un projet ]









MEMBER



Profil membre
   ↓
Actions
   ↓
Désactiver
   ↓
Confirmation
   ↓
Compte désactivé









Profil membre
   ↓
Rôle
   ↓
Modifier
   ↓
Sélection du rôle
   ↓
Confirmation
   ↓
Rôle modifié








Déconnexion




Utilisateur
   ↓
Déconnexion
   ↓
Session supprimée
   ↓
Retour à Login










┌───────────────────────────────┐
│ ☰   ORSC       🔔   Profil   │
├───────────────────────────────┤
│                               │
│          CONTENT              │
│                               │
└───────────────────────────────┘








Desktop
3 ou 4 colonnes

Tablet
2 colonnes

Mobile
1 colonne










Login
   ↓
CMS
   ├── Accueil
   ├── Dashboard
   ├── Membres
   ├── Départements
   ├── Projets
   ├── Articles
   ├── Événements
   ├── Tâches
   ├── templates
   ├── Annonces
   ├── Formations
   ├── Organisations
   ├── Media
   ├── Applications
   ├── Réunions
   ├── Notifications
   └── Paramètres











   Accueil
Membres
Départements
Projets
Articles
Événements
Tâches
templates
Annonces
Formations
Organisations
Media
Paramètres















Accueil
Dashboard
Membres
Départements
Projets
Articles
Événements
Tâches
templates
Annonces
Formations
Organisations
Paramètres











Applications
Réunions









Frontend CMS
      ↓
Flask Backend
      ↓
Business Logic
      ↓
Permission Check
      ↓
Database
      ↓
SQLite










Membres
   ↓
PEOPLE
USERS
MEMBERSHIPS

Tâches
   ↓
TASKS
TASK_ASSIGNEES

Événements
   ↓
EVENTS
EVENT_ATTENDANCE
EVENT_MEDIA
EVENT_DOCUMENTS

Projets
   ↓
PROJECTS
PROJECT_MEMBERS
PROJECT_TERMS

Articles
   ↓
SCIENTIFIC_ARTICLES
ARTICLE_AUTHORS
ARTICLE_SOURCE_REFERENCES
SOURCE_REFERENCES

Formations
   ↓
TRAININGS
TRAINING_ATTENDANCE
TRAINING_TERMS

Organisations
   ↓
ORGANIZATIONS
ORGANIZATION_RELATIONS



Applications
   ↓
APPLICATIONS
APPLICATION_PERIODS



Templates
   ↓
DOCUMENTS









Head ajoute un événement
        ↓
Flask Backend
        ↓
SQLite
        ↓
Site public récupère l'événement
        ↓
Événement affiché









Utilisateur
   ↓
POST /projects/create
   ↓
Backend
   ↓
Vérification du rôle
   ↓
Permission ?
   /       \
 OUI       NON
  ↓         ↓
Créer     Refuser
projet    l'action










Dashboard
   ↓
Tâches en retard
   ↓
Sélection
   ↓
Profil de la tâche










Ajouter
Modifier
Supprimer / Désactiver
Voir
Retour
Enregistrer
Annuler










Après avoir recopié ce fichier, **la phase de documentation UI/UX sera terminée**. 