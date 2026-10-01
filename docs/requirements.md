# ORSC — Club Management System

## 1. Présentation du projet

### 1.1 Nom du projet

**ORSC — Club Management System (CMS)**

### 1.2 Organisation

**Operations Research Society Club (ORSC)**  
Université des Sciences et Technologies Houari Boumediene (USTHB)

### 1.3 Description

Le ORSC Club Management System est une plateforme web destinée à centraliser la gestion du club et à fournir un espace public permettant aux visiteurs de découvrir le club.

Le système est composé de deux parties principales :

1. **Site web public**
2. **Système de gestion interne (CMS)**

Le site public est accessible aux visiteurs et aux candidats souhaitant rejoindre le club.

Le CMS est réservé aux personnes disposant d'un compte club actif et permet de gérer les membres, les départements, les événements et leurs médias, les projets, les tâches, les templates, les formations, les organisations, les articles et les autres activités du club.

---

# 2. Objectifs du projet

Le système doit permettre de :

- centraliser les informations du club ;
- présenter publiquement le club et ses activités ;
- gérer les membres et leurs appartenances au club ;
- gérer les différents départements ;
- gérer les différentes années/termes du club ;
- faciliter la gestion des tâches ;
- organiser les événements ;
- gérer les projets ;
- gérer les formations ;
- gérer les réunions ;
- gérer les templates internes du club ;
- gérer les annonces ;
- gérer les organisations et partenaires ;
- gérer les photos et vidéos associées aux événements ;
- gérer les articles scientifiques ;
- gérer les candidatures ;
- envoyer des notifications ;
- suivre les activités du club ;
- fournir des statistiques adaptées au rôle de chaque utilisateur ;
- conserver l'historique du club d'une année à l'autre.

---

# 3. Périmètre du système

Le projet comprend :

## 3.1 Site public

Le site public permet aux visiteurs de :

- découvrir le club ;
- consulter sa présentation ;
- découvrir les départements ;
- consulter les événements ;
- consulter les projets ;
- consulter les articles ;
- consulter les médias ;
- consulter les organisations et partenaires ;
- consulter les activités du club ;
- voir certaines statistiques générales ;
- consulter les informations relatives à l'équipe ;
- déposer une candidature lorsque les inscriptions sont ouvertes.

## 3.2 CMS interne

Le CMS permet aux membres autorisés de :

- consulter les informations internes du club ;
- consulter leur tableau de bord selon leur rôle ;
- consulter les membres ;
- consulter les départements ;
- consulter les événements ;
- gérer les tâches selon leurs permissions ;
- consulter et utiliser les templates disponibles ;
- publier des annonces ;
- consulter les formations ;
- consulter les organisations ;
- consulter les photos et vidéos associées aux événements ;
- consulter les projets ;
- consulter les articles ;
- gérer les candidatures selon les permissions ;
- gérer certains paramètres du club.

---

# 4. Utilisateurs du système

Le système distingue principalement les profils suivants :

1. **Member**
2. **Sub-Head of Department**
3. **Head of Department**
4. **Head of RH**
5. **President / Vice-President**

Les permissions sont déterminées par le rôle et, dans certains cas, par le département de l'utilisateur.

---

# 5. Gestion des personnes, comptes et adhésions

Le système distingue trois notions :

### 5.1 Personne

Une personne représente l'identité d'un individu ayant un lien avec le club.

Elle est enregistrée dans la table `PEOPLE`.

Une personne peut rester enregistrée dans le système même après avoir quitté le club.

### 5.2 Compte utilisateur

Un compte utilisateur permet à une personne d'accéder au CMS.

Il est enregistré dans la table `USERS`.

Un utilisateur peut se connecter avec :

- son username ;
- ou son adresse email.

### 5.3 Membership

Une membership représente l'appartenance d'une personne au club pour un terme/une année donnée.

Elle est enregistrée dans `MEMBERSHIPS`.

Une même personne peut donc avoir plusieurs memberships au cours de différentes années.

---

# 6. Gestion des années du club

Le club fonctionne avec plusieurs termes/années.

Le système doit conserver l'historique des années précédentes.

L'utilisateur peut sélectionner une année afin de consulter les informations correspondant à cette période.

Selon l'année sélectionnée, le système peut afficher notamment :

- les projets ;
- les formations ;
- les événements ;
- les membres ;
- les responsables ;
- le président ;
- le vice-président ;
- les chefs de départements ;
- les autres informations liées au terme sélectionné.

Par défaut, l'année courante est sélectionnée.

---

# 7. Site web public

## 7.1 Accès

Le site public est accessible sans authentification.

Les visiteurs peuvent naviguer librement dans les différentes sections disponibles.

## 7.2 Page d'accueil

La page d'accueil présente notamment :

- l'identité du club ;
- le logo ;
- la vision du club ;
- les statistiques principales ;
- les prochains événements ;
- les départements ;
- les activités du club ;
- la présentation vidéo ;
- les partenaires ;
- les éléments permettant de rejoindre le club.

Le contenu dynamique doit être récupéré depuis la base de données lorsque cela est nécessaire.

---

# 8. Statistiques publiques

Certaines statistiques sont affichées publiquement.

## 8.1 Nombre de membres

Le nombre affiché correspond au nombre de comptes présents dans `USERS`.

Ce nombre représente la communauté du club et peut inclure d'anciens membres qui continuent à être liés au club.

Le système ne doit donc pas limiter cette statistique aux memberships actives.

## 8.2 Nombre de départements

Le nombre de départements est obtenu à partir de la table `DEPARTMENTS`.

## 8.3 Événements

Les événements affichés comme prochains événements doivent être déterminés en fonction de la date actuelle.

Les événements passés et futurs doivent être différenciés.

---

# 9. Inscription au club

## 9.1 Périodes d'inscription

Les inscriptions ne sont pas ouvertes en permanence.

Les périodes d'inscription sont définies dans `APPLICATION_PERIODS`.

Lorsqu'aucune période d'inscription n'est ouverte, le visiteur doit voir une page indiquant que les inscriptions sont fermées.

Lorsqu'une période est ouverte, le bouton permettant de rejoindre le club donne accès au formulaire de candidature.

---

# 10. Formulaire de candidature

Le candidat doit fournir notamment :

- prénom ;
- nom ;
- date de naissance ;
- numéro de téléphone ;
- adresse email ;
- université (facultatif) ;
- faculté (facultatif) ;
- profession ;
- LinkedIn ;
- motivation ;
- compétences.

La candidature est enregistrée dans `APPLICATIONS`.

La personne correspondante est enregistrée dans `PEOPLE`.

---

# 11. Traitement des candidatures

Les candidatures sont traitées par le département RH.

Le Head RH peut :

- consulter les candidatures ;
- examiner les informations du candidat ;
- accepter une candidature ;
- rejeter une candidature.

## 11.1 Candidature acceptée

Lorsqu'une candidature est acceptée :

1. Le candidat reçoit un email.
2. L'email l'invite à rejoindre le club/local.
3. L'email contient un lien vers le deuxième formulaire.
Le lien vers le deuxième formulaire contient un token d'intégration unique et sécurisé.

Ce token :
- est associé à une seule candidature acceptée ;
- permet d'accéder au formulaire sans compte CMS ;
- devient inutilisable après la création du compte ;
- ne doit pas être réutilisable.
 
1. Le candidat complète la création de son compte.

Le deuxième formulaire contient :

- prénom ;
- nom ;
- username ;
- mot de passe ;
- département choisi.

Après validation :

- le compte `USER` est créé ;
- une `MEMBERSHIP` est créée ;
- le rôle initial est automatiquement `MEMBER` ;
- le département choisi est associé à la membership ;
- le terme courant est associé à la membership.

Le candidat ne choisit pas son rôle.

Le rôle peut ensuite être modifié par le Head RH.

## 11.2 Candidature rejetée

Lorsqu'une candidature est rejetée, le candidat reçoit un email l'invitant à venir au local pour une rencontre avec RH.

L'email contient :

- la date de la rencontre ;
- l'heure ;
- les informations nécessaires concernant la rencontre.

Après cette rencontre, RH peut décider de modifier la décision initiale et accepter finalement le candidat.

---

# 12. Authentification

Le CMS doit proposer une page de connexion.

L'utilisateur peut se connecter avec :

- username + mot de passe ;
- ou email + mot de passe.

Le système doit vérifier les informations d'identification avant d'autoriser l'accès au CMS.

Les mots de passe doivent être stockés sous forme sécurisée et ne doivent jamais être enregistrés en clair.

---

# 13. CMS — Navigation générale

Le CMS utilise une sidebar commune aux différents profils.

Les sections principales sont :

- Accueil
- Tableau de bord
- Membres
- Départements
- Projets
- Articles
- Événements
- Tâches
- Templates
- Annonces
- Formations
- Organisations
- Paramètres

La présence d'une section dans la sidebar ne signifie pas nécessairement que l'utilisateur possède le droit de modifier son contenu.

Les droits de création, modification et suppression sont contrôlés séparément selon le rôle et le département.

---

# 14. Profil Member

Le Member possède les droits suivants :

## Accueil

Le membre peut consulter :

- les informations du jour ;
- ses tâches ;
- les événements ;
- les activités récentes ;
- les templates disponibles ;
- les notifications ;
- les autres informations pertinentes du club.

## Dashboard

Le Member n'a pas accès au Dashboard.

## Membres

Le Member peut consulter les membres du club.

## Départements

Le Member peut consulter les départements.

## Projets

Le Member peut consulter les projets disponibles selon les règles définies par le système.

## Articles

Le Member peut consulter les articles publiés.

## Événements

Le Member peut :

- consulter les événements passés ;
- consulter les événements futurs ;
- consulter les informations relatives aux événements.

## Tâches

Le Member peut uniquement consulter ses propres tâches.

Il peut consulter notamment :

- la tâche ;
- sa description ;
- son état ;
- sa date limite.

Le Member ne peut pas créer de tâche.

## Templates

Le Member peut consulter les templates disponibles selon ses permissions.

Il peut :

- télécharger les templates stockés dans le CMS ;
- ouvrir les templates Canva ou Figma via leur lien externe.

Il ne peut pas ajouter, modifier ou supprimer un template sauf s'il appartient au département RH et possède les permissions prévues pour ce module.

## Annonces

Le Member peut :

- consulter les annonces ;
- créer une annonce.

Une annonce peut également être utilisée pour signaler une remarque concernant le club.

Exemple : un membre constate que le local est sale et peut publier une remarque via les annonces.

## Formations

Le Member peut consulter :

- les formations passées ;
- les formations à venir.

## Organisations

Le Member peut consulter les organisations et partenaires.

Il ne peut pas en ajouter.

## Paramètres

Le Member peut gérer ses propres paramètres personnels.

---

# 15. Profil Sub-Head of Department

Le Sub-Head possède les droits du Member avec des permissions supplémentaires.

## Dashboard

Le Sub-Head a accès au Dashboard.

Le Dashboard affiche les statistiques de son département.

Il peut notamment consulter :

- nombre de membres du département ;
- membres actifs/inactifs ;
- tâches terminées ;
- tâches en cours ;
- tâches non terminées ;
- taux de réalisation ;
- activités du département ;
- autres statistiques pertinentes.

## Tâches

Le Sub-Head peut créer des tâches.

Lors de la création d'une tâche, il peut définir :

- les destinataires ;
- la description ;
- la date limite ;
- les informations nécessaires à la tâche.

---

# 16. Profil Head of Department

Le Head possède les droits du Sub-Head avec des permissions supplémentaires.

## Dashboard

Le Dashboard présente les statistiques de son département.

## Membres

Le Head peut consulter les membres du club ainsi que notamment :

- leur département ;
- leur statut ;
- leur rating ;
- leur état actif/inactif.

## Tâches

Le Head peut consulter les tâches de tous les membres du club.

Il peut également créer des tâches.

## Templates

Le Head peut consulter et utiliser les templates disponibles.

Il peut :

- télécharger les fichiers stockés dans le CMS ;
- ouvrir les templates Canva ou Figma via leur lien externe.

Un Head ne peut ajouter ou supprimer des templates que s'il appartient au département RH.

Le Head RH peut donc gérer les templates selon les permissions définies pour ce module.

## Annonces

Le Head peut :

- consulter les annonces ;
- ajouter des annonces.

## Événements

Tous les Heads of Department peuvent ajouter des événements.

Ils peuvent également consulter les événements existants.

---

# 17. Permissions spécifiques aux départements

Certaines fonctionnalités de création dépendent du département du Head.

## 17.1 Projects

Seul le **Head of Projects & Activities** peut ajouter des projets.

Les autres utilisateurs peuvent consulter les projets.

## 17.2 Articles

Seul le **Head of Innovation/Research** peut ajouter des articles.

Les autres utilisateurs peuvent consulter les articles publiés.

## 17.3 Organizations

La gestion des organisations dépend du département et du rôle.

**Head of External Relations** et **Sub-Head of External Relations** peuvent :

- ajouter une organisation ;
- modifier une organisation ;
- supprimer une organisation ;
- ajouter, modifier et supprimer les relations avec ORSC.

Les **Members of External Relations** peuvent :

- consulter la liste des organisations ;
- ouvrir une organisation ;
- consulter ses informations complètes ;
- consulter l'historique de ses relations avec ORSC.

Les membres des autres départements peuvent uniquement consulter la liste des organisations.

Les Alumni peuvent également consulter uniquement la liste des organisations.

Les utilisateurs qui ne font pas partie du département External Relations ne peuvent pas accéder aux détails d'une organisation.

## 17.4 Events

Tous les Heads of Department peuvent ajouter des événements.

---

# 18. Profil Head RH

Le Head RH possède les droits du Head of Department avec des responsabilités supplémentaires au niveau du club.

## Dashboard

Le Head RH possède un Dashboard global.

Il peut consulter notamment :

- les statistiques générales du club ;
- l'état des départements ;
- les statistiques des membres ;
- les tâches ;
- les activités ;
- les autres indicateurs globaux.

## Membres

Le Head RH peut gérer les membres selon ses permissions.

Il peut notamment :

- consulter les membres ;
- consulter leur rôle ;
- consulter leur département ;
- désactiver un compte.

## Gestion des rôles

Le Head RH est responsable de la gestion des rôles.

Il peut :

- attribuer un rôle ;
- modifier un rôle ;
- gérer le rôle d'un utilisateur avant ou après sa connexion.

Lorsqu'un nouveau membre est accepté, son rôle initial est toujours :

`MEMBER`

Le Head RH peut ensuite modifier ce rôle.

## Candidatures

Le Head RH possède une section dédiée aux candidatures.

Il peut :

- consulter les candidatures ;
- examiner les candidats ;
- accepter une candidature ;
- rejeter une candidature ;
- gérer le processus de rencontre avec les candidats.

## Réunions

Le Head RH peut organiser des réunions confidentielles entre :

- President ;
- Vice-President ;
- Heads of Department.

---

# 19. Profil President / Vice-President

Le President et le Vice-President possèdent les droits généraux du Head RH.

Ils peuvent consulter et gérer les informations globales du club selon leurs permissions.

Cependant :

### Ils ne peuvent pas :

- désactiver les comptes des membres ;
- attribuer ou modifier les rôles des utilisateurs.

La gestion des rôles reste une responsabilité du Head RH.

---

# 20. Gestion des événements

Les événements peuvent être :

- à venir ;
- en cours ;
- terminés.

Les utilisateurs autorisés peuvent créer un événement.

Tous les Heads of Department peuvent créer des événements.

Un événement peut être associé à :

- un terme ;
- un responsable ;
- des participants ;
- des médias ;
- des documents.

Les membres peuvent consulter les événements et leurs informations.

---

# 21. Gestion des tâches

Les tâches permettent de suivre le travail des membres.

Une tâche peut contenir notamment :

- une description ;
- une date limite ;
- un créateur ;
- un ou plusieurs destinataires ;
- un état.

Les tâches peuvent être assignées à plusieurs membres.

### Permissions

**Member :**
- consulter ses propres tâches.

**Sub-Head :**
- consulter ses tâches ;
- créer des tâches.

**Head :**
- consulter toutes les tâches ;
- créer des tâches.

**Head RH :**
- consulter et gérer les tâches selon ses permissions.

**President / VP :**
- consulter et gérer les tâches selon leurs permissions.

---

# 22. Gestion des annonces

Les annonces sont accessibles aux utilisateurs autorisés.

Tous les membres peuvent :

- consulter les annonces ;
- créer une annonce.

Les Heads, RH et President/VP disposent également de ces droits.

Les annonces peuvent être utilisées pour :

- communiquer une information ;
- signaler un problème ;
- faire une remarque ;
- informer les membres d'un changement.

---

# 23. Gestion des templates

Le CMS met à disposition une bibliothèque de templates internes utilisés par ORSC.

Tous les utilisateurs autorisés peuvent consulter la liste des templates disponibles.

Un template peut être :

- un fichier PDF ;
- un document Word ;
- un fichier Excel ;
- une présentation PowerPoint ;
- un template Canva ;
- un template Figma.

Pour les fichiers stockés dans le CMS, l'utilisateur peut télécharger le template.

Pour Canva et Figma, le système conserve un lien externe permettant d'ouvrir directement le template.

# 23. Gestion des templates

La création et la suppression des templates sont réservées aux membres actuels du département RH ayant l'un des rôles suivants :

- Member ;
- Sub-Head ;
- Head.

Ces utilisateurs peuvent :

- ajouter un nouveau template ;
- sélectionner le type du template ;
- uploader un fichier ;
- enregistrer un lien Canva ou Figma ;
- supprimer un template existant.

Les autres utilisateurs peuvent consulter et utiliser les templates selon leurs permissions, mais ne peuvent pas les modifier.

Le module Templates ne possède pas de page de détail ni de fonction d'édition.

---

# 24. Gestion des formations

Le système permet de gérer les formations du club.

Les utilisateurs peuvent consulter :

- les formations à venir ;
- les formations passées.

Une formation peut être associée à :

- un coach ;
- des participants ;
- un terme/une année.

Les présences peuvent être enregistrées.

---

# 25. Gestion des projets

Les projets permettent de conserver les projets du club et leur historique.

Les utilisateurs peuvent consulter les projets selon leurs permissions.

La création d'un projet est réservée au :

**Head of Projects & Activities**

Un projet peut être associé à :

- un responsable de l'idée ;
- plusieurs membres ;
- plusieurs termes/années.

---

# 26. Gestion des articles

Le système permet de publier et consulter les articles scientifiques du club.

Les utilisateurs peuvent consulter les articles publiés.

La création d'un article est réservée au :

**Head of Innovation/Research**

Un article peut être associé à :

- plusieurs auteurs ;
- plusieurs références/sources.

---

# 27. Gestion des organisations

Le système permet de conserver les organisations liées à ORSC ainsi que l'historique de leurs relations avec le club.

Les organisations peuvent être de type :

- Company ;
- Startup ;
- University ;
- School ;
- Association ;
- Institution ;
- Media ;
- Club ;
- Other.

Chaque organisation peut contenir :

- un nom ;
- un type ;
- une description ;
- une adresse ;
- un site web ;
- un email ;
- un numéro de téléphone ;
- un logo.

## Consultation

Tous les utilisateurs connectés peuvent consulter la liste des organisations.

La liste affiche notamment :

- le logo ;
- le nom ;
- le type de l'organisation.

Les membres actuels du département **External Relations** peuvent ouvrir une organisation et consulter toutes ses informations.

Les membres des autres départements et les Alumni peuvent uniquement consulter la liste des organisations.

Ils ne peuvent pas accéder aux informations détaillées d'une organisation.

## Gestion

La création, la modification et la suppression des organisations sont réservées aux :

- **Head of External Relations** ;
- **Sub-Head of External Relations**.

Un Member du département External Relations peut consulter les informations détaillées mais ne peut pas modifier les organisations.

## Relations avec ORSC

Chaque organisation peut posséder un historique de relations avec ORSC.

Une relation est associée à une année académique et contient notamment :

- le type de relation ;
- l'année académique ;
- une description ;
- une date de début ;
- une date de fin.

Les types de relations disponibles sont :

- Sponsor ;
- Partner ;
- Collaboration ;
- Other.

Une organisation ne peut posséder qu'une seule relation pour une même année académique.

Les Head et Sub-Head External Relations peuvent :

- ajouter une nouvelle relation ;
- modifier une relation existante ;
- supprimer une relation.

Les anciennes relations sont conservées afin de maintenir l'historique des collaborations entre ORSC et l'organisation.

---

# 28. Notifications

Le système doit permettre d'envoyer des notifications aux utilisateurs.

Exemples :

- une nouvelle tâche lui est assignée ;
- une modification concernant une tâche ;
- une information importante ;
- une nouvelle activité ;
- une autre action nécessitant son attention.

Les notifications sont associées au compte utilisateur.

---

# 29. Activités récentes

Le CMS peut afficher les activités récentes du club.

Les activités doivent rester liées à la vie du club.

Exemples :

- réunion organisée ;
- événement réalisé ;
- projet lancé ;
- article publié ;
- formation réalisée ;
- autre activité importante du club.

---

# 30. Gestion des réunions

Le système permet de créer et gérer des réunions.

Une réunion peut avoir :

- un organisateur ;
- des participants ;
- une date ;
- des informations relatives à la réunion.

Les présences peuvent être enregistrées.

Certaines réunions peuvent être confidentielles et être organisées par RH entre les responsables du club.

---

# 31. Gestion des certificats

Le système permet de gérer les certificats délivrés par le club.

Un certificat peut être attribué à une ou plusieurs personnes.

Le système doit conserver l'historique des certificats et de leurs bénéficiaires.

---

# 32. Gestion des compétences

Le système permet d'associer des compétences aux personnes.

Les compétences peuvent notamment être utilisées lors :

- des candidatures ;
- de la gestion des membres ;
- de la constitution d'équipes ;
- des projets.

---

# 33. Système de permissions

Les permissions doivent être contrôlées côté backend.

Le fait de masquer un bouton dans l'interface ne suffit pas.

Le serveur doit vérifier que l'utilisateur possède réellement l'autorisation nécessaire avant :

- de créer ;
- modifier ;
- supprimer ;
- désactiver ;
- attribuer un rôle ;
- publier ;
- gérer une ressource.

---

# 34. Tableau général des permissions

| Fonctionnalité | Member | Sub-Head | Head | Head RH | President / VP |
|---|---|---|---|---|---|
| Accueil | Voir | Voir | Voir | Voir | Voir |
| Dashboard | ❌ | Département | Département | Global | Global |
| Membres | Voir | Voir | Voir | Gérer | Voir |
| Départements | Voir | Voir | Voir | Gérer | Voir |
| Projets | Voir | Voir | Voir / Ajouter selon département | Voir | Voir |
| Articles | Voir | Voir | Voir / Ajouter selon département | Voir | Voir |
| Événements | Voir | Voir | Voir / Ajouter | Voir / Ajouter | Voir / Ajouter |
| Tâches | Ses tâches | Ses tâches / Créer | Toutes / Créer | Gérer | Gérer |
| Templates | Voir / Utiliser | Voir / Utiliser | Gérer uniquement si RH | Gérer | Voir / Utiliser |
| Annonces | Voir / Ajouter | Voir / Ajouter | Voir / Ajouter | Voir / Ajouter | Voir / Ajouter |
| Formations | Voir | Voir | Voir | Voir | Voir |
| Organisations | Liste / Détails si External Relations | Gérer si External Relations / Liste sinon | Gérer si External Relations / Liste sinon | Liste uniquement | Liste uniquement |
| Paramètres | Personnel | Personnel | Personnel | Gestion | Gestion |
| Candidatures | ❌ | ❌ | ❌ | Gérer | Voir selon permissions |
| Gestion des rôles | ❌ | ❌ | ❌ | ✅ | ❌ |
| Désactivation de compte | ❌ | ❌ | ❌ | ✅ | ❌ |

---

# 35. Règles métier importantes

## Règle 1 — Nouveau membre

Tout candidat accepté devient initialement :

`MEMBER`

Il ne choisit pas son rôle.

## Règle 2 — Choix du département

Lors de la création de son compte après acceptation, le candidat choisit son département.

## Règle 3 — Gestion des rôles

Seul le Head RH peut modifier les rôles.

## Règle 4 — President / VP

Le President et le Vice-President ne peuvent pas :

- modifier les rôles ;
- désactiver les comptes.

## Règle 5 — Événements

Tous les Heads of Department peuvent créer des événements.

## Règle 6 — Annonces

Tous les membres peuvent créer des annonces.

## Règle 7 — Projets

Seul le Head du département Projects & Activities peut créer des projets.

## Règle 8 — Articles

Seul le Head du département Innovation/Research peut créer des articles.

## Règle 9 — Organisations

Seuls le Head et le Sub-Head du département External Relations peuvent ajouter, modifier et supprimer des organisations.

Les Members du département External Relations peuvent consulter les détails complets des organisations.

Les membres des autres départements et les Alumni peuvent uniquement consulter la liste des organisations.

## Règle 10 — Historique

Les informations des anciennes années doivent rester accessibles afin de conserver l'historique du club.

## Règle 11 — Année sélectionnée

Lorsqu'un utilisateur change l'année sélectionnée, les informations affichées doivent correspondre au terme choisi lorsque la donnée est liée à un terme.

---

# 36. Contraintes techniques générales

Le système doit :

- utiliser une architecture web séparant frontend et backend ;
- utiliser Flask pour le backend ;
- utiliser SQLite comme base de données initiale ;
- respecter le schéma de base de données défini dans `database/schema.sql` ;
- utiliser des contrôles d'autorisation côté serveur ;
- sécuriser les mots de passe ;
- gérer les sessions utilisateur ;
- permettre une interface responsive ;
- supporter les modes Light et Dark ;
- intégrer les animations prévues dans le design ;
- conserver une structure permettant une évolution future du système.

---

# 37. Technologies prévues

### Backend

- Python
- Flask

### Base de données

- SQLite

### Frontend

- HTML
- CSS
- JavaScript

### Outils de développement

- VS Code
- Git
- GitHub

---

# 38. Design et interface

L'interface du système doit respecter les maquettes et références visuelles déjà définies pour le projet.

Deux modes visuels sont prévus :

- Light Mode
- Dark Mode

Le design doit être responsive et adapté notamment :

- aux ordinateurs ;
- aux tablettes ;
- aux téléphones.

Les animations graphiques prévues dans l'identité visuelle du club seront intégrées lors de la phase d'implémentation frontend.

---

# 39. Documentation associée

Le projet est documenté à travers plusieurs fichiers :

```text
docs/
├── requirements.md
├── user-flows.md
├── public-website-ui-ux.md
└── cms-ui-ux.md


Flask-WTF==1.3.0


Flask-Limiter==4.1.1