# ORSC — User Flows

## 1. Introduction

Ce document décrit les différents parcours des utilisateurs du **ORSC Club Management System**.

Le système comprend deux espaces principaux :

- le site public, accessible à tous les visiteurs ;
- le CMS interne, accessible uniquement aux utilisateurs possédant un compte.

Les principaux utilisateurs sont :

- Visiteur
- Candidat
- Member
- Sub-Head of Department
- Head of Department
- Head RH
- President
- Vice-President


## 2. Parcours du visiteur

Le visiteur peut accéder librement au site public sans authentification.

```text
Visiteur
   ↓
Page d'accueil
   ↓
Navigation sur le site
   ├── Découvrir le club
   ├── Départements
   ├── Événements
   ├── Projets
   ├── Articles
   ├── Organisations
   ├── Media
   └── Rejoindre le club




   Visiteur
   ↓
Clique sur « Découvrir le club »
   ↓
Page de présentation du club
   ↓
Consultation des informations
   ↓
Retour au site ou navigation vers une autre section


Visiteur
   ↓
Clique sur « Départements »
   ↓
Liste des départements
   ↓
Sélection d'un département
   ↓
Consultation de sa mission et de ses informations
   ↓
Retour à la liste ou navigation vers une autre section


Visiteur
   ↓
Clique sur « Événements »
   ↓
Liste des événements
   ├── Événements à venir
   └── Événements passés
   ↓
Sélection d'un événement
   ↓
Consultation des informations


Visiteur
   ↓
Clique sur « Projets »
   ↓
Liste des projets
   ↓
Sélection d'un projet
   ↓
Consultation des informations du projet


Visiteur
   ↓
Clique sur « Articles »
   ↓
Liste des articles
   ↓
Sélection d'un article
   ↓
Lecture de l'article


Visiteur
   ↓
Clique sur « Organisations »
   ↓
Liste des organisations et partenaires
   ↓
Sélection d'une organisation
   ↓
Consultation des informations


Visiteur
   ↓
Clique sur « Media »
   ↓
Galerie
   ├── Photos
   └── Vidéos
   ↓
Consultation du contenu


Visiteur
   ↓
Clique sur « Rejoindre le club »
   ↓
Le système vérifie la période d'inscription


                 Période d'inscription ?
                    /             \
                  NON             OUI
                   ↓               ↓
          Inscriptions fermées   Formulaire


                           Période d'inscription ?
                    /             \
                  NON             OUI
                   ↓               ↓
          Inscriptions fermées   Formulaire


          Visiteur
   ↓
« Rejoindre le club »
   ↓
Vérification de la période
   ↓
Aucune période ouverte
   ↓
Page « Inscriptions fermées »
   ↓
Message expliquant que les inscriptions sont actuellement fermées
   ↓
Retour au site public


Visiteur
   ↓
« Rejoindre le club »
   ↓
Vérification de la période
   ↓
Période ouverte
   ↓
Formulaire de candidature
   ↓
Remplissage du formulaire
   ↓
Envoi
   ↓
Candidature enregistrée


Candidat
   ↓
Envoie le formulaire
   ↓
Candidature enregistrée
   ↓
Head RH consulte la candidature
   ↓
Examen de la candidature
   ↓
Décision


                    Décision RH
                    /         \
              Acceptée       Rejetée
                 ↓               ↓
          Parcours accepté   Parcours rejeté


         
Candidature
   ↓
Acceptée par RH
   ↓
Génération d'un token d'intégration unique
   ↓
Email envoyé au candidat
   ↓
Invitation à rejoindre le club
   ↓
Lien sécurisé vers le deuxième formulaire
   ↓
Candidat ouvre le lien
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




Deuxième formulaire
   ↓
Validation
   ↓
Création du compte USER
   ↓
Création de la MEMBERSHIP
   ↓
Association à la personne
   ↓
Association au département choisi
   ↓
Association au terme courant
   ↓
Rôle initial = MEMBER
   ↓
Compte disponible
   ↓
Connexion au CMS


Candidature
   ↓
Examen par RH
   ↓
Rejet
   ↓
Email envoyé au candidat
   ↓
Invitation à une rencontre avec RH
   ↓
Date et heure communiquées
   ↓
Rencontre
   ↓
Nouvelle décision


                    Nouvelle décision
                     /            \
                Acceptée         Rejetée
                   ↓                ↓
             Intégration       Fin du processus
               au club


               Utilisateur
   ↓
Page Login
   ↓
Entre son username ou son email
   ↓
Entre son mot de passe
   ↓
Validation
   ↓
Vérification des informations


Informations correctes
   ↓
Authentification réussie
   ↓
Accès au CMS


Informations incorrectes
   ↓
Message d'erreur
   ↓
Retour à la page Login


Utilisateur
   ↓
Connexion réussie
   ↓
Identification du rôle
   ↓
Accès au CMS selon les permissions


Member
   ↓
Sub-Head of Department
   ↓
Head of Department
   ↓
Head RH
   ↓
President / Vice-President


Accueil
Tableau de bord
Membres
Départements
Projets
Articles
Événements
Tâches
Templates
Annonces
Formations
Organisations
Paramètres


Member
   ↓
Connexion
   ↓
CMS
   ↓
Accueil


Sub-Head
   ↓
Connexion
   ↓
CMS
   ↓
Accueil
   ↓
Dashboard de son département


Head of Department
   ↓
Connexion
   ↓
CMS
   ↓
Accueil
   ↓
Dashboard de son département


Member
   ↓
Connexion
   ↓
CMS
   ↓
Pas de Dashboard


Sub-Head
   ↓
Connexion
   ↓
Dashboard
   ↓
Informations de son département


Head
   ↓
Connexion
   ↓
Dashboard
   ↓
Informations de son département


Head RH
   ↓
Connexion
   ↓
Dashboard
   ↓
Informations globales du club


President / Vice-President
   ↓
Connexion
   ↓
Dashboard
   ↓
Informations globales du club


Sub-Head / Head
   ↓
Tâches
   ↓
Créer une tâche
   ↓
Ajouter les informations
   ↓
Choisir le ou les membres concernés
   ↓
Définir la date limite
   ↓
Créer la tâche
   ↓
Tâche enregistrée


Tâche créée
   ↓
Membre assigné
   ↓
Notification
   ↓
Membre consulte la notification
   ↓
Ouverture de la tâche


Utilisateur
   ↓
Tâches
   ↓
Liste des tâches accessibles
   ↓
Sélection d'une tâche
   ↓
Consultation des informations


Utilisateur
   ↓
Événements
   ↓
Liste des événements
   ├── À venir
   └── Passés
   ↓
Sélection d'un événement
   ↓
Consultation des informations
   ↓
Event Details
   ↓
Media
   ├── Photos
   └── Vidéos
   ↓
Médias rattachés à cet événement


Utilisateur autorisé
   ↓
Événements
   ↓
Ajouter un événement
   ↓
Remplir les informations
   ↓
Enregistrer
   ↓
Événement créé


Utilisateur
   ↓
Annonces
   ↓
Liste des annonces
   ↓
Sélection d'une annonce
   ↓
Consultation


Member
   ↓
Annonces
   ↓
Ajouter une annonce
   ↓
Écrire le contenu
   ↓
Publier
   ↓
Annonce enregistrée


Membre constate un problème dans le local
   ↓
Annonces
   ↓
Ajouter une annonce
   ↓
Décrire le problème
   ↓
Publier
   ↓
Annonce visible


Utilisateur
   ↓
Projets
   ↓
Liste des projets
   ↓
Sélection d'un projet
   ↓
Consultation des informations


Head Projects & Activities
   ↓
Projets
   ↓
Ajouter un projet
   ↓
Remplir les informations
   ↓
Enregistrer
   ↓
Projet créé


Utilisateur
   ↓
Articles
   ↓
Liste des articles
   ↓
Sélection d'un article
   ↓
Lecture


Head Innovation / Research
   ↓
Articles
   ↓
Ajouter un article
   ↓
Ajouter les informations
   ↓
Ajouter les auteurs
   ↓
Ajouter les sources
   ↓
Enregistrer
   ↓
Article créé


Utilisateur connecté
   ↓
Organizations
   ↓
Liste des organisations
   ↓
Logo + Nom + Type
   ↓
Identification du profil
   ├── External Relations Member
   │       ↓
   │   Sélection d'une organisation
   │       ↓
   │   Consultation des informations complètes
   │       ↓
   │   Consultation de l'historique des relations
   │
   ├── External Relations Head / Sub-Head
   │       ↓
   │   Sélection d'une organisation
   │       ↓
   │   Consultation des informations complètes
   │       ↓
   │   Ajouter / Modifier / Supprimer une organisation
   │       ↓
   │   Gérer l'historique des relations
   │       ├── Ajouter une relation
   │       ├── Modifier une relation
   │       └── Supprimer une relation
   │
   ├── Membre d'un autre département
   │       ↓
   │   Consultation de la liste uniquement
   │       ↓
   │   Pas d'accès aux détails
   │
   └── Alumni
           ↓
       Consultation de la liste uniquement
           ↓
       Pas d'accès aux détails


Head / Sub-Head External Relations
   ↓
Organizations
   ↓
Add Organization
   ↓
Informations de l'organisation
   ↓
Relation initiale avec ORSC
   ↓
Academic Year + Relation Type
   ↓
Enregistrer
   ↓
Organisation créée
   ↓
Historique des relations disponible


Organisation existante
   ↓
Relationship History
   ↓
Une relation par année académique
   ↓
Sponsor / Partner / Collaboration / Other
   ↓
Historique conservé d'une année à l'autre


Utilisateur
   ↓
Formations
   ↓
Liste des formations
   ├── Formations à venir
   └── Formations passées
   ↓
Sélection d'une formation
   ↓
Consultation des informations


Utilisateur autorisé
   ↓
Templates
   ↓
Liste des templates disponibles
   ↓
Choix d'un template
   ├── Fichier stocké dans le CMS
   │       ↓
   │   Télécharger
   │
   └── Canva / Figma
           ↓
       Ouvrir le lien externe


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
Template ajouté


RH Member / Sub-Head / Head
   ↓
Template existant
   ↓
Supprimer
   ↓
Template supprimé


Head RH
   ↓
Connexion
   ↓
CMS
   ↓
Dashboard global


Head RH
   ↓
Applications
   ↓
Liste des candidatures
   ↓
Sélection d'une candidature
   ↓
Consultation des informations
   ↓
Décision


                     Candidature
                          ↓
                    Décision RH
                     /       \
                Accepter    Rejeter
                    ↓          ↓
                  Email      Email
                    ↓          ↓
             2ème formulaire Rencontre


             Head RH
   ↓
Membres
   ↓
Sélection d'un membre
   ↓
Consultation des informations
   ↓
Actions disponibles selon les permissions


Head RH
   ↓
Membres
   ↓
Sélection d'un membre
   ↓
Consultation du rôle actuel
   ↓
Modifier le rôle
   ↓
Choisir le nouveau rôle
   ↓
Validation
   ↓
Rôle modifié


Head RH
   ↓
Membres
   ↓
Sélection d'un membre
   ↓
Désactiver le compte
   ↓
Confirmation
   ↓
Compte désactivé


Head RH
   ↓
Réunions
   ↓
Créer une réunion
   ↓
Sélectionner les participants
   ├── President
   ├── Vice-President
   └── Heads of Department
   ↓
Définir la date et l'heure
   ↓
Ajouter les informations
   ↓
Créer la réunion


President / Vice-President
   ↓
Connexion
   ↓
CMS
   ↓
Dashboard global


Utilisateur
   ↓
Sélecteur d'année
   ↓
Choix d'une année
   ↓
Le système charge les informations du terme sélectionné


Action dans le système
   ↓
Notification générée
   ↓
Utilisateur concerné
   ↓
Notification visible
   ↓
Utilisateur ouvre la notification
   ↓
Accès à l'information concernée


Head crée une tâche
   ↓
Membre assigné
   ↓
Notification générée
   ↓
Membre ouvre la notification
   ↓
Tâche affichée


Utilisateur
   ↓
Membres
   ↓
Liste des membres
   ↓
Sélection d'un membre
   ↓
Consultation du profil


Utilisateur
   ↓
Demande une action
   ↓
Vérification des permissions
        /             \
   Autorisé        Non autorisé
      ↓                ↓
Action exécutée    Accès refusé


                         VISITEUR
                            ↓
                       SITE PUBLIC
                            ↓
                  ┌─────────┴─────────┐
                  │                   │
             Navigation         Rejoindre le club
                                      ↓
                              Vérification période
                                /             \
                              NON             OUI
                               ↓               ↓
                       Inscriptions       Formulaire
                          fermées               ↓
                                          Candidature
                                               ↓
                                              RH
                                         /          \
                                    Acceptée       Rejetée
                                       ↓              ↓
                                     Email         Rencontre
                                       ↓              ↓
                               2ème formulaire    Décision
                                       ↓
                              USER + MEMBERSHIP
                                       ↓
                                Rôle = MEMBER
                                       ↓
                                     LOGIN
                                       ↓
                                      CMS
                                       ↓
                 ┌──────────┬──────────┬──────────┬──────────┐
                 ↓          ↓          ↓          ↓          ↓
              Member    Sub-Head     Head      Head RH   President/VP
                 ↓          ↓          ↓          ↓          ↓
              Accueil   Dashboard  Dashboard  Dashboard  Dashboard
                            département       global      global