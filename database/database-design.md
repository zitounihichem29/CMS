# Database Design

## 1. Overview

This document describes the relational database design of the Club Management System (CMS).

## 2. Tables and Keys


### 2.1 PEOPLE

**Primary Key**
- `person_id`

**Foreign Keys**
- None

---


### 2.2 USERS

**Primary Key**
- `user_id`

**Foreign Keys**
- `person_id` → `PEOPLE.person_id`

**Constraints**
- `UNIQUE (person_id)`

---


### 2.3 TERMS

**Primary Key**
- `term_id`

**Foreign Keys**
- None

---


### 2.4 ROLES

**Primary Key**
- `role_id`

**Foreign Keys**
- None

---


### 2.5 DEPARTMENTS


**Primary Key**
- `department_id`

**Foreign Keys**
- None

---


### 2.6 MEMBERSHIPS

**Primary Key**
- `membership_id`

**Foreign Keys**
- `person_id` → `PEOPLE.person_id`
- `term_id` → `TERMS.term_id`
- `role_id` → `ROLES.role_id`
- `department_id` → `DEPARTMENTS.department_id`

**Constraints**
- `UNIQUE (person_id, term_id, role_id, department_id)`

---


### 2.7 EVENTS

**Primary Key**
- `event_id`

**Foreign Keys**
- `term_id` → `TERMS.term_id`
- `event_leader_membership_id` → `MEMBERSHIPS.membership_id`

---


### 2.8 TRAININGS

**Primary Key**
- `training_id`

**Foreign Keys**
- `coach_person_id` → `PEOPLE.person_id`

---


### 2.9 TASKS

**Primary Key**
- `task_id`

**Foreign Keys**
- `assigned_by_membership_id` → `MEMBERSHIPS.membership_id`
- `reviewed_by_membership_id` → `MEMBERSHIPS.membership_id`

---


### 2.10 TASK_ASSIGNEES

**Primary Key**
- `task_assignee_id`

**Foreign Keys**
- `task_id` → `TASKS.task_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (task_id, membership_id)`

---


### 2.11 TASK_ATTACHMENTS

**Primary Key**
- `task_attachment_id`

**Foreign Keys**
- `task_id` → `TASKS.task_id`
- `uploaded_by_membership_id` → `MEMBERSHIPS.membership_id`

**Purpose**
- Stores the metadata of files attached to a task.
- The physical file is stored on the server; the database stores its path and metadata.

---


### 2.11 PROJECTS

**Primary Key**
- `project_id`

**Foreign Keys**
- `idea_owner_membership_id` → `MEMBERSHIPS.membership_id`

---


### 2.12 PROJECT_TERMS

**Primary Key**
- `project_term_id`

**Foreign Keys**
- `project_id` → `PROJECTS.project_id`
- `term_id` → `TERMS.term_id`

**Constraints**
- `UNIQUE (project_id, term_id)`

---


### 2.13 PROJECT_MEMBERS

**Primary Key**
- `project_member_id`

**Foreign Keys**
- `project_id` → `PROJECTS.project_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (project_id, membership_id)`

---



---

### 2.14 PROJECT_VOLUNTEERS

**Primary Key**
- `project_volunteer_id`

**Foreign Keys**
- `project_id` → `PROJECTS.project_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (project_id, membership_id)`


### 2.14 SCIENTIFIC_ARTICLES

**Primary Key**
- `scientific_article_id`

**Foreign Keys**
- `article_owner_membership_id` → `MEMBERSHIPS.membership_id`
- `uploaded_by_membership_id` → `MEMBERSHIPS.membership_id`

---


### 2.15 ARTICLE_TERMS

**Primary Key**
- `article_term_id`

**Foreign Keys**
- `scientific_article_id` → `SCIENTIFIC_ARTICLES.scientific_article_id`
- `term_id` → `TERMS.term_id`

**Constraints**
- `UNIQUE (scientific_article_id, term_id)`

---


### 2.16 ARTICLE_VOLUNTEERS

**Primary Key**
- `article_volunteer_id`

**Foreign Keys**
- `scientific_article_id` → `SCIENTIFIC_ARTICLES.scientific_article_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (scientific_article_id, membership_id)`

---


### 2.15 ARTICLE_AUTHORS

**Primary Key**
- `article_author_id`

**Foreign Keys**
- `scientific_article_id` → `SCIENTIFIC_ARTICLES.scientific_article_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (scientific_article_id, membership_id)`

---


### 2.16 SOURCE_REFERENCES

**Primary Key**
- `source_reference_id`

**Foreign Keys**
- None

---


### 2.17 ARTICLE_SOURCE_REFERENCES

**Primary Key**
- `article_source_reference_id`

**Foreign Keys**
- `scientific_article_id` → `SCIENTIFIC_ARTICLES.scientific_article_id`
- `source_reference_id` → `SOURCE_REFERENCES.source_reference_id`

**Constraints**
- `UNIQUE (scientific_article_id, source_reference_id)`

---


### 2.18 MEETINGS

**Primary Key**
- `meeting_id`

**Foreign Keys**
- `organizer_membership_id` → `MEMBERSHIPS.membership_id`

---


### 2.19 MEETING_ATTENDANCE

**Primary Key**
- `meeting_attendance_id`

**Foreign Keys**
- `meeting_id` → `MEETINGS.meeting_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (meeting_id, membership_id)`

---


### 2.20 EVENT_ATTENDANCE

**Primary Key**
- `event_attendance_id`

**Foreign Keys**
- `event_id` → `EVENTS.event_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (event_id, membership_id)`

---



### 2.38 EVENT_ORGANIZATIONS

**Primary Key**
- `event_organization_id`

**Foreign Keys**
- `event_id` → `EVENTS.event_id`
- `organization_id` → `ORGANIZATIONS.organization_id`

**Constraints**
- `UNIQUE (event_id, organization_id)`

---


### 2.21 EVENT_MEDIA

**Primary Key**
- `event_media_id`

**Foreign Keys**
- `event_id` → `EVENTS.event_id`

---


### 2.22 TRAINING_ATTENDANCE

**Primary Key**
- `training_attendance_id`

**Foreign Keys**
- `training_id` → `TRAININGS.training_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (training_id, membership_id)`

---


### 2.23 APPLICATION_PERIODS

**Primary Key**
- `application_period_id`

**Foreign Keys**
- `term_id` → `TERMS.term_id`

**Constraints**
- `onboarding_token` is unique when defined.

---


### 2.24 APPLICATIONS

**Primary Key**
- `application_id`

**Foreign Keys**
- `application_period_id` → `APPLICATION_PERIODS.application_period_id`
- `person_id` → `PEOPLE.person_id`

---


### 2.25 APPLICATION_MEETINGS

**Primary Key**
- `meeting_id`

**Foreign Keys**
- `application_id` → `APPLICATIONS.application_id`

**Constraints**
- `status` ∈ (`scheduled`, `completed`, `cancelled`)



### APPLICATION_MEETING_PARTICIPANTS

**Primary Key**
- `application_meeting_participant_id`

**Foreign Keys**
- `meeting_id` → `APPLICATION_MEETINGS.meeting_id`
- `membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (meeting_id, membership_id)`

---



### 2.26 PERSON_SKILLS

**Primary Key**
- `person_skill_id`

**Foreign Keys**
- `person_id` → `PEOPLE.person_id`

**Constraints**
- `UNIQUE (person_id, skill)`

---


### 2.26 ORGANIZATIONS

**Primary Key**
- `organization_id`

**Foreign Keys**
- `created_by_membership_id` → `MEMBERSHIPS.membership_id`


**Organization Types**
- `company`
- `startup`
- `university`
- `school`
- `association`
- `institution`
- `media`
- `club`
- `other`

---


### 2.27 ORGANIZATION_RELATIONS

**Primary Key**
- `organization_relation_id`

**Foreign Keys**
- `organization_id` → `ORGANIZATIONS.organization_id`
- `term_id` → `TERMS.term_id`

**Relation Types**
- `sponsor`
- `partner`
- `collaboration`
- `other`

**Constraints**
- `UNIQUE (organization_id, term_id)`

---


### 2.28 DOCUMENTS

**Primary Key**
- `document_id`

**Foreign Keys**
- `uploaded_by_membership_id` → `MEMBERSHIPS.membership_id`

**Storage**
- `storage_type = file`
  - Uses `file_path`
  - Uses `original_filename`
- `storage_type = link`
  - Uses `external_url`

**Document Types**
- `pdf`
- `word`
- `excel`
- `powerpoint`
- `canva`
- `figma`

---


### 2.30 EVENT_DOCUMENTS

**Primary Key**
- `event_document_id`

**Foreign Keys**
- `event_id` → `EVENTS.event_id`
- `created_by_membership_id` → `MEMBERSHIPS.membership_id`

---


### 2.32 ANNUAL_SCHEDULE

**Primary Key**
- `annual_schedule_id`

**Foreign Keys**
- `created_by_membership_id` → `MEMBERSHIPS.membership_id`
- `term_id` → `TERMS.term_id`

**Constraints**
- `UNIQUE (term_id)`

---


### 2.33 MEMBER_NOTES

**Primary Key**
- `member_note_id`

**Foreign Keys**
- `membership_id` → `MEMBERSHIPS.membership_id`
- `given_by_membership_id` → `MEMBERSHIPS.membership_id`

---


### 2.34 NOTIFICATIONS

**Primary Key**
- `notification_id`

**Foreign Keys**
- `recipient_user_id` → `USERS.user_id`

**Fields**
- `notification_type`
- `title`
- `message`
- `target_url`
- `is_read`
- `created_at`
- `read_at`

**Constraints**
- `notification_type` ∈ (`task`, `announcement`)
- `is_read` ∈ (`0`, `1`)


---


### 2.35 CERTIFICATES

**Primary Key**
- `certificate_id`

---


### 2.36 CERTIFICATE_RECIPIENTS

**Primary Key**
- `certificate_recipient_id`

**Foreign Keys**
- `certificate_id` → `CERTIFICATES.certificate_id`
- `person_id` → `PEOPLE.person_id`

**Constraints**
- `UNIQUE (certificate_id, person_id)`

---


### 2.37 TRAINING_TERMS

**Primary Key**
- `training_term_id`

**Foreign Keys**
- `training_id` → `TRAININGS.training_id`
- `term_id` → `TERMS.term_id`

**Constraints**
- `UNIQUE (training_id, term_id)`

---


### 37. ANNOUNCEMENTS

**Primary Key**
- `announcement_id`

**Foreign Keys**
- `created_by_membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `visibility` ∈ (`public`, `personalized`)
- `status` ∈ (`active`, `resolved`)

---


### 38. ANNOUNCEMENT_RECIPIENTS

**Primary Key**
- `announcement_recipient_id`

**Foreign Keys**
- `announcement_id` → `ANNOUNCEMENTS.announcement_id`
- `recipient_membership_id` → `MEMBERSHIPS.membership_id`

**Constraints**
- `UNIQUE (announcement_id)`

---


---

## 3. Relationships

### 3.1 One-to-One (1:1)

- `PEOPLE` 1:1 `USERS`
- `TERMS` 1:1 `ANNUAL_SCHEDULE`
- `ANNOUNCEMENTS` 1:1 `ANNOUNCEMENT_RECIPIENTS` — only for personalized announcements

### 3.2 One-to-Many (1:N)

- `PEOPLE` 1:N `MEMBERSHIPS`
- `TERMS` 1:N `MEMBERSHIPS`
- `ROLES` 1:N `MEMBERSHIPS`
- `DEPARTMENTS` 1:N `MEMBERSHIPS`
- `MEMBERSHIPS` 1:N `EVENTS` — as event leader
- `PEOPLE` 1:N `TRAININGS` — as coach
- `MEMBERSHIPS` 1:N `TASKS` — as task creator
- `TASKS` 1:N `TASK_ASSIGNEES`
- `MEMBERSHIPS` 1:N `TASK_ASSIGNEES`
- `MEMBERSHIPS` 1:N `PROJECTS` — as idea owner
- `PROJECTS` 1:N `PROJECT_TERMS`
- `TERMS` 1:N `PROJECT_TERMS`
- `PROJECTS` 1:N `PROJECT_MEMBERS`
- `MEMBERSHIPS` 1:N `PROJECT_MEMBERS`
- `SCIENTIFIC_ARTICLES` 1:N `ARTICLE_AUTHORS`
- `MEMBERSHIPS` 1:N `ARTICLE_AUTHORS`
- `SCIENTIFIC_ARTICLES` 1:N `ARTICLE_SOURCE_REFERENCES`
- `SOURCE_REFERENCES` 1:N `ARTICLE_SOURCE_REFERENCES`
- `MEMBERSHIPS` 1:N `MEETINGS` — as organizer
- `MEETINGS` 1:N `MEETING_ATTENDANCE`
- `MEMBERSHIPS` 1:N `MEETING_ATTENDANCE`
- `EVENTS` 1:N `EVENT_ATTENDANCE`
- `MEMBERSHIPS` 1:N `EVENT_ATTENDANCE`
- `EVENTS` 1:N `EVENT_MEDIA`
- `TRAININGS` 1:N `TRAINING_ATTENDANCE`
- `MEMBERSHIPS` 1:N `TRAINING_ATTENDANCE`
- `TERMS` 1:N `APPLICATION_PERIODS`
- `APPLICATION_PERIODS` 1:N `APPLICATIONS`
- `PEOPLE` 1:N `APPLICATIONS`
- `APPLICATIONS` 1:N `APPLICATION_MEETINGS`
- `APPLICATION_MEETINGS` 1:N `APPLICATION_MEETING_PARTICIPANTS`
- `MEMBERSHIPS` 1:N `APPLICATION_MEETING_PARTICIPANTS`
- `PEOPLE` 1:N `PERSON_SKILLS`
- `ORGANIZATIONS` 1:N `ORGANIZATION_RELATIONS`
- `TERMS` 1:N `ORGANIZATION_RELATIONS`
- `MEMBERSHIPS` 1:N `ORGANIZATIONS` — as organization creator
- `EVENTS` 1:N `EVENT_DOCUMENTS`
- `MEMBERSHIPS` 1:N `EVENT_DOCUMENTS` — as creator
- `MEMBERSHIPS` 1:N `DOCUMENTS` — as template uploader
- `MEMBERSHIPS` 1:N `ANNUAL_SCHEDULE` — as creator
- `MEMBERSHIPS` 1:N `MEMBER_NOTES` — as recipient
- `MEMBERSHIPS` 1:N `MEMBER_NOTES` — as issuer
- `USERS` 1:N `NOTIFICATIONS`
- `CERTIFICATES` 1:N `CERTIFICATE_RECIPIENTS`
- `PEOPLE` 1:N `CERTIFICATE_RECIPIENTS`
- `TRAININGS` 1:N `TRAINING_TERMS`
- `TERMS` 1:N `TRAINING_TERMS`
- `MEMBERSHIPS` 1:N `ANNOUNCEMENTS`
- `TASKS` 1:N `TASK_ATTACHMENTS`
- `MEMBERSHIPS` 1:N `TASK_ATTACHMENTS`
- `MEMBERSHIPS` 1:N `ANNOUNCEMENTS` — as announcement creator
- `MEMBERSHIPS` 1:N `ANNOUNCEMENT_RECIPIENTS` — as personalized announcement recipient
- `PROJECTS` 1:N `PROJECT_VOLUNTEERS`
- `MEMBERSHIPS` 1:N `PROJECT_VOLUNTEERS`
- `MEMBERSHIPS` 1:N `SCIENTIFIC_ARTICLES` — as article owner
- `MEMBERSHIPS` 1:N `SCIENTIFIC_ARTICLES` — as final PDF uploader
- `SCIENTIFIC_ARTICLES` 1:N `ARTICLE_TERMS`
- `TERMS` 1:N `ARTICLE_TERMS`
- `SCIENTIFIC_ARTICLES` 1:N `ARTICLE_VOLUNTEERS`
- `MEMBERSHIPS` 1:N `ARTICLE_VOLUNTEERS`
- `EVENTS` 1:N `EVENT_ORGANIZATIONS`
- `ORGANIZATIONS` 1:N `EVENT_ORGANIZATIONS`

### 3.3 Many-to-Many (N:N)

The following many-to-many relationships are implemented through junction tables:

- `PROJECTS` N:N `TERMS`
  - Junction table: `PROJECT_TERMS`

- `PROJECTS` N:N `MEMBERSHIPS`
  - Junction table: `PROJECT_MEMBERS`

- `PROJECTS` N:N `MEMBERSHIPS` — members who volunteer to participate
  - Junction table: `PROJECT_VOLUNTEERS`

- `SCIENTIFIC_ARTICLES` N:N `MEMBERSHIPS`
  - Junction table: `ARTICLE_AUTHORS`

- `SCIENTIFIC_ARTICLES` N:N `SOURCE_REFERENCES`
  - Junction table: `ARTICLE_SOURCE_REFERENCES`

- `MEETINGS` N:N `MEMBERSHIPS`
  - Junction table: `MEETING_ATTENDANCE`

- `EVENTS` N:N `MEMBERSHIPS`
  - Junction table: `EVENT_ATTENDANCE`

- `TRAININGS` N:N `MEMBERSHIPS`
  - Junction table: `TRAINING_ATTENDANCE`

- `CERTIFICATES` N:N `PEOPLE`
  - Junction table: `CERTIFICATE_RECIPIENTS`

- `TRAININGS` N:N `TERMS`
  - Junction table: `TRAINING_TERMS`
- `SCIENTIFIC_ARTICLES` N:N `TERMS`
  - Junction table: `ARTICLE_TERMS`

- `SCIENTIFIC_ARTICLES` N:N `MEMBERSHIPS`
  - Junction table: `ARTICLE_VOLUNTEERS`
  - Purpose: article volunteers
  
- `EVENTS` N:N `ORGANIZATIONS`
  - Junction table: `EVENT_ORGANIZATIONS`