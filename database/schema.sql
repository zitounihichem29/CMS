-- ============================================================
-- ORSC CMS - CANONICAL DATABASE SCHEMA
-- Automatically synchronized from rsclub.db
-- ============================================================

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

-- ============================================================
-- TABLE: people
-- ============================================================

CREATE TABLE people (
    person_id INTEGER PRIMARY KEY,

    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,

    date_of_birth DATE,

    phone TEXT,
    email TEXT,

    university TEXT,
    faculty TEXT,

    bio TEXT,

    linkedin TEXT,
    facebook TEXT,
    discord TEXT,
    github TEXT,

    cv TEXT,
    profession TEXT,

    profile_photo TEXT
);

-- ============================================================
-- TABLE: users
-- ============================================================

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,

    person_id INTEGER NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1, is_platform_admin INTEGER NOT NULL DEFAULT 0
CHECK (is_platform_admin IN (0, 1)),

    FOREIGN KEY (person_id) REFERENCES people(person_id)
);

-- ============================================================
-- TABLE: terms
-- ============================================================

CREATE TABLE terms (
    term_id INTEGER PRIMARY KEY,

    name TEXT NOT NULL UNIQUE,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL, status TEXT NOT NULL DEFAULT 'ARCHIVED'
CHECK (status IN ('DRAFT', 'ACTIVE', 'ARCHIVED')),

    CHECK (end_date > start_date)
);

-- ============================================================
-- TABLE: roles
-- ============================================================

CREATE TABLE roles (
    role_id INTEGER PRIMARY KEY,

    name TEXT NOT NULL UNIQUE,

    description TEXT
);

-- ============================================================
-- TABLE: departments
-- ============================================================

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,

    name TEXT NOT NULL UNIQUE,

    description TEXT
);

-- ============================================================
-- TABLE: events
-- ============================================================

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,

    term_id INTEGER NOT NULL,
    event_leader_membership_id INTEGER NOT NULL,

    title TEXT NOT NULL,
    description TEXT,

    event_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,

    location TEXT,

    cover_image_path TEXT,
    
     end_date DATE,

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    FOREIGN KEY (event_leader_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: event_media
-- ============================================================

CREATE TABLE event_media (
    event_media_id INTEGER PRIMARY KEY,

    event_id INTEGER NOT NULL,

    media_type TEXT NOT NULL,
    file_path TEXT NOT NULL,

    caption TEXT, is_public INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (event_id)
        REFERENCES events(event_id)
);

-- ============================================================
-- TABLE: event_attendance
-- ============================================================

CREATE TABLE event_attendance (
    event_attendance_id INTEGER PRIMARY KEY,

    event_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    attendance_status TEXT NOT NULL DEFAULT 'present',

    FOREIGN KEY (event_id)
        REFERENCES events(event_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (event_id, membership_id)
);

-- ============================================================
-- TABLE: trainings
-- ============================================================

CREATE TABLE trainings (
    training_id INTEGER PRIMARY KEY,

    coach_person_id INTEGER NOT NULL,

    title TEXT NOT NULL,
    description TEXT,

    training_date DATE,
    start_time TIME,
    end_time TIME,

    location TEXT,
    
    registration_link TEXT,

    cover_image_path TEXT,

    FOREIGN KEY (coach_person_id)
        REFERENCES people(person_id)
);

-- ============================================================
-- TABLE: training_terms
-- ============================================================

CREATE TABLE training_terms (
    training_term_id INTEGER PRIMARY KEY,

    training_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,

    FOREIGN KEY (training_id)
        REFERENCES trainings(training_id),

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    UNIQUE (training_id, term_id)
);

-- ============================================================
-- TABLE: training_attendance
-- ============================================================

CREATE TABLE training_attendance (
    training_attendance_id INTEGER PRIMARY KEY,

    training_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    attendance_status TEXT NOT NULL DEFAULT 'present',

    FOREIGN KEY (training_id)
        REFERENCES trainings(training_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (training_id, membership_id)
);

-- ============================================================
-- TABLE: projects
-- ============================================================

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,

    idea_owner_membership_id INTEGER NOT NULL,

    name TEXT NOT NULL,
    description TEXT,

    status TEXT NOT NULL DEFAULT 'active',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, project_link TEXT, is_public INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (idea_owner_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: project_terms
-- ============================================================

CREATE TABLE project_terms (
    project_term_id INTEGER PRIMARY KEY,

    project_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,

    FOREIGN KEY (project_id)
        REFERENCES projects(project_id),

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    UNIQUE (project_id, term_id)
);

-- ============================================================
-- TABLE: project_members
-- ============================================================

CREATE TABLE project_members (
    project_member_id INTEGER PRIMARY KEY,

    project_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    joined_at DATETIME,

    FOREIGN KEY (project_id)
        REFERENCES projects(project_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (project_id, membership_id)
);

-- ============================================================
-- TABLE: tasks
-- ============================================================

CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY,

    assigned_by_membership_id INTEGER NOT NULL,

    title TEXT NOT NULL,
    description TEXT,

    due_date DATE,

    status TEXT NOT NULL DEFAULT 'pending',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, review_status TEXT
        NOT NULL DEFAULT 'not_reviewed', reviewed_by_membership_id INTEGER
        REFERENCES memberships(membership_id), reviewed_at DATETIME,

    FOREIGN KEY (assigned_by_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: task_assignees
-- ============================================================

CREATE TABLE task_assignees (
    task_assignee_id INTEGER PRIMARY KEY,

    task_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (task_id, membership_id)
);

-- ============================================================
-- TABLE: meetings
-- ============================================================

CREATE TABLE meetings (
    meeting_id INTEGER PRIMARY KEY,

    organizer_membership_id INTEGER NOT NULL,

    title TEXT NOT NULL,
    description TEXT,

    meeting_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,

    location TEXT,

    application_id INTEGER, term_id
                INTEGER REFERENCES terms(term_id),

    FOREIGN KEY (organizer_membership_id)
        REFERENCES memberships(membership_id),

    FOREIGN KEY (application_id)
        REFERENCES applications(application_id)
);

-- ============================================================
-- TABLE: meeting_attendance
-- ============================================================

CREATE TABLE meeting_attendance (
    meeting_attendance_id INTEGER PRIMARY KEY,

    meeting_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    attendance_status TEXT NOT NULL DEFAULT 'present',

    FOREIGN KEY (meeting_id)
        REFERENCES meetings(meeting_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (meeting_id, membership_id)
);

-- ============================================================
-- TABLE: event_documents
-- ============================================================

CREATE TABLE event_documents (
    event_document_id INTEGER PRIMARY KEY,

    event_id INTEGER NOT NULL,
    created_by_membership_id INTEGER NOT NULL,

    document_name TEXT NOT NULL,
    file_path TEXT NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (event_id)
        REFERENCES events(event_id),

    FOREIGN KEY (created_by_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: source_references
-- ============================================================

CREATE TABLE source_references (
    source_reference_id INTEGER PRIMARY KEY,

    title TEXT NOT NULL,
    authors TEXT,

    source_type TEXT,

    publication_year INTEGER,

    url TEXT,
    doi TEXT
);

-- ============================================================
-- TABLE: article_authors
-- ============================================================

CREATE TABLE article_authors (
    article_author_id INTEGER PRIMARY KEY,

    scientific_article_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    FOREIGN KEY (scientific_article_id)
        REFERENCES scientific_articles(scientific_article_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (
        scientific_article_id,
        membership_id
    )
);

-- ============================================================
-- TABLE: article_source_references
-- ============================================================

CREATE TABLE article_source_references (
    article_source_reference_id INTEGER PRIMARY KEY,

    scientific_article_id INTEGER NOT NULL,
    source_reference_id INTEGER NOT NULL, source_title_snapshot
                TEXT, source_authors_snapshot
                TEXT, source_type_snapshot
                TEXT, source_publication_year_snapshot
                INTEGER, source_url_snapshot
                TEXT, source_doi_snapshot
                TEXT,

    FOREIGN KEY (scientific_article_id)
        REFERENCES scientific_articles(scientific_article_id),

    FOREIGN KEY (source_reference_id)
        REFERENCES source_references(source_reference_id),

    UNIQUE (
        scientific_article_id,
        source_reference_id
    )
);

-- ============================================================
-- TABLE: application_periods
-- ============================================================

CREATE TABLE application_periods (
    application_period_id INTEGER PRIMARY KEY,

    term_id INTEGER NOT NULL,

    name TEXT NOT NULL,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    CHECK (end_date > start_date)
);

-- ============================================================
-- TABLE: applications
-- ============================================================

CREATE TABLE applications (
    application_id INTEGER PRIMARY KEY,

    application_period_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,

    motivation TEXT,

    status TEXT NOT NULL DEFAULT 'pending',

    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, onboarding_token TEXT,

    FOREIGN KEY (application_period_id)
        REFERENCES application_periods(application_period_id),

    FOREIGN KEY (person_id)
        REFERENCES people(person_id)
);

-- ============================================================
-- TABLE: annual_schedule
-- ============================================================

CREATE TABLE annual_schedule (
    annual_schedule_id INTEGER PRIMARY KEY,

    term_id INTEGER NOT NULL UNIQUE,
    created_by_membership_id INTEGER NOT NULL,

    title TEXT NOT NULL,
    description TEXT,

    file_path TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, original_filename
                TEXT,

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    FOREIGN KEY (created_by_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: person_skills
-- ============================================================

CREATE TABLE person_skills (
    person_skill_id INTEGER PRIMARY KEY,

    person_id INTEGER NOT NULL,

    skill TEXT NOT NULL,

    FOREIGN KEY (person_id)
        REFERENCES people(person_id),

    UNIQUE (
        person_id,
        skill
    )
);

-- ============================================================
-- TABLE: member_notes
-- ============================================================

CREATE TABLE member_notes (
    member_note_id INTEGER PRIMARY KEY,

    membership_id INTEGER NOT NULL,
    given_by_membership_id INTEGER NOT NULL,

    note TEXT NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, note_type
                TEXT NOT NULL DEFAULT 'REMARK',

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    FOREIGN KEY (given_by_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: certificates
-- ============================================================

CREATE TABLE certificates (
    certificate_id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,

    description TEXT,

    certificate_type TEXT,

    issued_date DATE,

    file_path TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
, term_id
                INTEGER REFERENCES terms(term_id), created_by_membership_id
                INTEGER REFERENCES memberships(membership_id), original_filename
                TEXT);

-- ============================================================
-- TABLE: certificate_recipients
-- ============================================================

CREATE TABLE certificate_recipients (
    certificate_recipient_id INTEGER PRIMARY KEY,

    certificate_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL, recipient_name_snapshot
                TEXT,

    FOREIGN KEY (certificate_id)
        REFERENCES certificates(certificate_id),

    FOREIGN KEY (person_id)
        REFERENCES people(person_id),

    UNIQUE (
        certificate_id,
        person_id
    )
);

-- ============================================================
-- TABLE: announcements
-- ============================================================

CREATE TABLE announcements (
    announcement_id INTEGER PRIMARY KEY,
    created_by_membership_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, visibility TEXT
        NOT NULL DEFAULT 'public'
        CHECK (
            visibility IN (
                'public',
                'personalized'
            )
        ), status TEXT
        NOT NULL DEFAULT 'active'
        CHECK (
            status IN (
                'active',
                'resolved'
            )
        ), updated_at DATETIME,
    FOREIGN KEY (created_by_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: task_attachments
-- ============================================================

CREATE TABLE task_attachments (
    task_attachment_id INTEGER PRIMARY KEY,

    task_id INTEGER NOT NULL,
    uploaded_by_membership_id INTEGER NOT NULL,

    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER,

    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id),

    FOREIGN KEY (uploaded_by_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: announcement_recipients
-- ============================================================

CREATE TABLE announcement_recipients (
        announcement_recipient_id INTEGER PRIMARY KEY,

        announcement_id INTEGER NOT NULL UNIQUE,
        recipient_membership_id INTEGER NOT NULL,

        is_read BOOLEAN NOT NULL DEFAULT 0,
        read_at DATETIME,

        FOREIGN KEY (announcement_id)
            REFERENCES announcements(announcement_id),

        FOREIGN KEY (recipient_membership_id)
            REFERENCES memberships(membership_id)
    );

-- ============================================================
-- TABLE: project_volunteers
-- ============================================================

CREATE TABLE project_volunteers (
    project_volunteer_id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,
    volunteered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id)
        REFERENCES projects(project_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (project_id, membership_id)
);

-- ============================================================
-- TABLE: article_terms
-- ============================================================

CREATE TABLE article_terms (
    article_term_id INTEGER PRIMARY KEY,
    scientific_article_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,

    FOREIGN KEY (scientific_article_id)
        REFERENCES scientific_articles(scientific_article_id),

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    UNIQUE (scientific_article_id, term_id)
);

-- ============================================================
-- TABLE: article_volunteers
-- ============================================================

CREATE TABLE article_volunteers (
    article_volunteer_id INTEGER PRIMARY KEY,
    scientific_article_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,
    volunteered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (scientific_article_id)
        REFERENCES scientific_articles(scientific_article_id),

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id),

    UNIQUE (scientific_article_id, membership_id)
);

-- ============================================================
-- TABLE: scientific_articles
-- ============================================================

CREATE TABLE "scientific_articles" (
    scientific_article_id INTEGER PRIMARY KEY,

    article_owner_membership_id INTEGER NOT NULL,

    title TEXT NOT NULL,
    abstract TEXT,

    publication_date DATE,

    file_path TEXT,
    original_filename TEXT,
    uploaded_by_membership_id INTEGER,
    uploaded_at DATETIME,

    status TEXT NOT NULL DEFAULT 'active',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, is_public INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (article_owner_membership_id)
        REFERENCES memberships(membership_id),

    FOREIGN KEY (uploaded_by_membership_id)
        REFERENCES memberships(membership_id)
);

-- ============================================================
-- TABLE: documents
-- ============================================================

CREATE TABLE documents (
    document_id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,

    document_type TEXT NOT NULL,

    storage_type TEXT NOT NULL,

    file_path TEXT,
    original_filename TEXT,

    external_url TEXT,

    uploaded_by_membership_id INTEGER NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (uploaded_by_membership_id)
        REFERENCES memberships(membership_id),

    CHECK (
        storage_type IN ('file', 'link')
    ),

    CHECK (
        document_type IN (
            'pdf',
            'word',
            'excel',
            'powerpoint',
            'canva',
            'figma'
        )
    )
);

-- ============================================================
-- TABLE: organizations
-- ============================================================

CREATE TABLE organizations (
    organization_id INTEGER PRIMARY KEY,

    name TEXT NOT NULL UNIQUE,

    organization_type TEXT NOT NULL,

    description TEXT,

    address TEXT,

    website TEXT,
    email TEXT,
    phone TEXT,

    logo_path TEXT,
    original_logo_filename TEXT,

    created_by_membership_id INTEGER NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (created_by_membership_id)
        REFERENCES memberships(membership_id),

    CHECK (
        organization_type IN (
            'company',
            'startup',
            'university',
            'school',
            'association',
            'institution',
            'media',
            'club',
            'other'
        )
    )
);

-- ============================================================
-- TABLE: organization_relations
-- ============================================================

CREATE TABLE organization_relations (
    organization_relation_id INTEGER PRIMARY KEY,

    organization_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,

    relation_type TEXT NOT NULL,

    description TEXT,

    start_date DATE,
    end_date DATE,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, organization_name_snapshot
                    TEXT, organization_type_snapshot
                    TEXT, organization_description_snapshot
                    TEXT, organization_address_snapshot
                    TEXT, organization_website_snapshot
                    TEXT, organization_email_snapshot
                    TEXT, organization_phone_snapshot
                    TEXT, organization_logo_path_snapshot
                    TEXT, organization_original_logo_filename_snapshot
                    TEXT,

    FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id),

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    CHECK (
        relation_type IN (
            'sponsor',
            'partner',
            'collaboration',
            'other'
        )
    ),

    UNIQUE (
        organization_id,
        term_id
    )
);

-- ============================================================
-- TABLE: application_meetings
-- ============================================================

CREATE TABLE application_meetings (
    meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL,
    meeting_date TEXT NOT NULL,
    meeting_time TEXT NOT NULL,
    location TEXT,
    meeting_link TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id)
        REFERENCES applications(application_id)
        ON DELETE CASCADE
);

-- ============================================================
-- TABLE: application_meeting_participants
-- ============================================================

CREATE TABLE application_meeting_participants (
    application_meeting_participant_id INTEGER PRIMARY KEY AUTOINCREMENT,

    meeting_id INTEGER NOT NULL,
    membership_id INTEGER NOT NULL,

    FOREIGN KEY (meeting_id)
        REFERENCES application_meetings(meeting_id)
        ON DELETE CASCADE,

    FOREIGN KEY (membership_id)
        REFERENCES memberships(membership_id)
        ON DELETE CASCADE,

    UNIQUE (meeting_id, membership_id)
);

-- ============================================================
-- TABLE: notifications
-- ============================================================

CREATE TABLE notifications (
    notification_id INTEGER PRIMARY KEY,

    recipient_user_id INTEGER NOT NULL,

    notification_type TEXT NOT NULL,

    title TEXT NOT NULL,
    message TEXT NOT NULL,

    target_url TEXT,

    is_read BOOLEAN NOT NULL DEFAULT 0,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at DATETIME,

    FOREIGN KEY (recipient_user_id)
        REFERENCES users(user_id),

    CHECK (
        notification_type IN (
            'task',
            'announcement'
        )
    ),

    CHECK (
        is_read IN (
            0,
            1
        )
    )
);

-- ============================================================
-- TABLE: event_organizations
-- ============================================================

CREATE TABLE event_organizations (
    event_organization_id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,

    FOREIGN KEY (event_id)
        REFERENCES events(event_id),

    FOREIGN KEY (organization_id)
        REFERENCES organizations(organization_id),

    UNIQUE (event_id, organization_id)
);

-- ============================================================
-- TABLE: training_media
-- ============================================================

CREATE TABLE training_media (
    training_media_id INTEGER PRIMARY KEY,

    training_id INTEGER NOT NULL,
    uploaded_by_membership_id INTEGER NOT NULL,

    media_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,

    caption TEXT,

    is_public INTEGER NOT NULL DEFAULT 0,

    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (training_id)
        REFERENCES trainings(training_id),

    FOREIGN KEY (uploaded_by_membership_id)
        REFERENCES memberships(membership_id),

    CHECK (media_type IN ('image', 'video')),

    CHECK (is_public IN (0, 1))
);

-- ============================================================
-- TABLE: contact_messages
-- ============================================================

CREATE TABLE contact_messages (contact_message_id INTEGER PRIMARY KEY, sender_type TEXT NOT NULL DEFAULT 'guest', sender_email TEXT, message TEXT NOT NULL, is_read INTEGER NOT NULL DEFAULT 0, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, CHECK (sender_type IN ('guest')), CHECK (is_read IN (0, 1)));

-- ============================================================
-- TABLE: password_reset_codes
-- ============================================================

CREATE TABLE password_reset_codes (
    password_reset_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    code_hash TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,
    CHECK (is_used IN (0, 1))
);

-- ============================================================
-- TABLE: memberships
-- ============================================================

CREATE TABLE "memberships" (
    membership_id INTEGER PRIMARY KEY,

    person_id INTEGER NOT NULL,
    term_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,

    department_id INTEGER,

    FOREIGN KEY (person_id)
        REFERENCES people(person_id),

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    FOREIGN KEY (role_id)
        REFERENCES roles(role_id),

    FOREIGN KEY (department_id)
        REFERENCES departments(department_id),

    UNIQUE (
        person_id,
        term_id
    )
);

-- ============================================================
-- TABLE: mandate_elections
-- ============================================================

CREATE TABLE mandate_elections (

            election_id INTEGER PRIMARY KEY,

            term_id INTEGER NOT NULL UNIQUE,

            election_date DATE NOT NULL,

            report_path TEXT,

            notes TEXT,

            recorded_by_user_id INTEGER,

            recorded_at TEXT
                NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            updated_by_user_id INTEGER,

            updated_at TEXT,

            FOREIGN KEY (term_id)
                REFERENCES terms(term_id)
                ON DELETE CASCADE,

            FOREIGN KEY (recorded_by_user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL,

            FOREIGN KEY (updated_by_user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL
        );

-- ============================================================
-- TABLE: mandate_approvals
-- ============================================================

CREATE TABLE mandate_approvals (

            approval_id INTEGER PRIMARY KEY,

            term_id INTEGER NOT NULL,

            approval_type TEXT NOT NULL,

            approved_by_user_id INTEGER NOT NULL,

            approved_at TEXT
                NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (term_id)
                REFERENCES terms(term_id)
                ON DELETE CASCADE,

            FOREIGN KEY (approved_by_user_id)
                REFERENCES users(user_id),

            CHECK (
                approval_type IN (
                    'PRESIDENT',
                    'VICE_PRESIDENT'
                )
            ),

            UNIQUE (
                term_id,
                approval_type
            )
        );

-- ============================================================
-- TABLE: mandate_audit_log
-- ============================================================

CREATE TABLE mandate_audit_log (

            log_id INTEGER PRIMARY KEY,

            term_id INTEGER,

            term_name TEXT NOT NULL,

            actor_user_id INTEGER,

            action TEXT NOT NULL,

            details TEXT,

            emergency_reason TEXT,

            created_at TEXT
                NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (term_id)
                REFERENCES terms(term_id)
                ON DELETE SET NULL,

            FOREIGN KEY (actor_user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL
        );

-- ============================================================
-- TABLE: alumni_profiles
-- ============================================================

CREATE TABLE alumni_profiles (

                alumni_id INTEGER PRIMARY KEY,

                person_id INTEGER
                    NOT NULL
                    UNIQUE,

                slug TEXT UNIQUE,


                category TEXT
                    NOT NULL
                    DEFAULT 'OTHER'

                    CHECK (
                        category IN (
                            'ACADEMIA',
                            'STARTUP',
                            'INDUSTRY',
                            'OTHER'
                        )
                    ),


                headline TEXT,

                current_title TEXT,

                current_organization TEXT,


                graduation_year INTEGER

                    CHECK (
                        graduation_year IS NULL
                        OR graduation_year
                           BETWEEN 1900 AND 2200
                    ),


                short_bio TEXT,

                story TEXT,


                photo_path TEXT,

                linkedin_url TEXT,

                website_url TEXT,


                is_public INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        is_public IN (0, 1)
                    ),


                is_featured INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        is_featured IN (0, 1)
                    ),


                is_spotlight INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        is_spotlight IN (0, 1)
                    ),


                display_order INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        display_order >= 0
                    ),


                created_by_user_id INTEGER,

                updated_by_user_id INTEGER,


                created_at TEXT
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT,


                FOREIGN KEY (
                    person_id
                )

                    REFERENCES people(
                        person_id
                    )

                    ON DELETE CASCADE,


                FOREIGN KEY (
                    created_by_user_id
                )

                    REFERENCES users(
                        user_id
                    )

                    ON DELETE SET NULL,


                FOREIGN KEY (
                    updated_by_user_id
                )

                    REFERENCES users(
                        user_id
                    )

                    ON DELETE SET NULL
            );

-- ============================================================
-- INDEX: idx_applications_onboarding_token
-- ============================================================

CREATE UNIQUE INDEX idx_applications_onboarding_token
    ON applications(onboarding_token);

-- ============================================================
-- INDEX: idx_password_reset_user
-- ============================================================

CREATE INDEX idx_password_reset_user
ON password_reset_codes(user_id);

-- ============================================================
-- INDEX: idx_terms_single_active
-- ============================================================

CREATE UNIQUE INDEX idx_terms_single_active
ON terms(status)
WHERE status = 'ACTIVE';

-- ============================================================
-- INDEX: idx_terms_single_draft
-- ============================================================

CREATE UNIQUE INDEX idx_terms_single_draft

        ON terms(status)

        WHERE status = 'DRAFT';

-- ============================================================
-- INDEX: idx_mandate_approvals_term
-- ============================================================

CREATE INDEX idx_mandate_approvals_term

        ON mandate_approvals(term_id);

-- ============================================================
-- INDEX: idx_mandate_audit_log_term
-- ============================================================

CREATE INDEX idx_mandate_audit_log_term

        ON mandate_audit_log(term_id);

-- ============================================================
-- INDEX: idx_mandate_audit_log_created_at
-- ============================================================

CREATE INDEX idx_mandate_audit_log_created_at

        ON mandate_audit_log(created_at);

-- ============================================================
-- INDEX: idx_alumni_profiles_public
-- ============================================================

CREATE INDEX idx_alumni_profiles_public

            ON alumni_profiles(
                is_public,
                display_order,
                alumni_id
            );

-- ============================================================
-- INDEX: idx_alumni_profiles_category
-- ============================================================

CREATE INDEX idx_alumni_profiles_category

            ON alumni_profiles(
                category,
                is_public
            );

-- ============================================================
-- INDEX: idx_alumni_profiles_featured
-- ============================================================

CREATE INDEX idx_alumni_profiles_featured

            ON alumni_profiles(
                is_featured,
                is_public,
                display_order
            );

-- ============================================================
-- INDEX: idx_alumni_single_spotlight
-- ============================================================

CREATE UNIQUE INDEX idx_alumni_single_spotlight

            ON alumni_profiles(
                is_spotlight
            )

            WHERE is_spotlight = 1;

-- ============================================================
-- INDEX: idx_project_terms_single_term
-- ============================================================

CREATE UNIQUE INDEX idx_project_terms_single_term

            ON project_terms(
                project_id
            );

-- ============================================================
-- INDEX: idx_article_terms_single_term
-- ============================================================

CREATE UNIQUE INDEX idx_article_terms_single_term

            ON article_terms(
                scientific_article_id
            );

-- ============================================================
-- INDEX: idx_training_terms_single_term
-- ============================================================

CREATE UNIQUE INDEX idx_training_terms_single_term

            ON training_terms(
                training_id
            );

-- ============================================================
-- INDEX: idx_organization_relations_unique_term
-- ============================================================

CREATE UNIQUE INDEX idx_organization_relations_unique_term

            ON organization_relations(
                organization_id,
                term_id
            );

-- ============================================================
-- INDEX: idx_meetings_term_date
-- ============================================================

CREATE INDEX idx_meetings_term_date

            ON meetings(
                term_id,
                meeting_date,
                start_time
            );

-- ============================================================
-- INDEX: idx_member_notes_membership_created
-- ============================================================

CREATE INDEX idx_member_notes_membership_created

            ON member_notes(
                membership_id,
                created_at
            );

-- ============================================================
-- INDEX: idx_certificates_term_date
-- ============================================================

CREATE INDEX idx_certificates_term_date

            ON certificates(
                term_id,
                issued_date,
                certificate_id
            );

-- ============================================================
-- TRIGGER: trg_memberships_no_alumni_active_insert
-- ============================================================

CREATE TRIGGER trg_memberships_no_alumni_active_insert

            BEFORE INSERT
            ON memberships

            FOR EACH ROW

            WHEN

                EXISTS (

                    SELECT 1

                    FROM roles

                    WHERE role_id =
                          NEW.role_id

                      AND name =
                          'ALUMNI'
                )

                AND

                EXISTS (

                    SELECT 1

                    FROM terms

                    WHERE term_id =
                          NEW.term_id

                      AND status IN (
                          'ACTIVE',
                          'DRAFT'
                      )
                )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'ALUMNI role cannot be used in ACTIVE or DRAFT mandates'
                );

            END;

-- ============================================================
-- TRIGGER: trg_memberships_no_alumni_active_update
-- ============================================================

CREATE TRIGGER trg_memberships_no_alumni_active_update

            BEFORE UPDATE OF
                role_id,
                term_id

            ON memberships

            FOR EACH ROW

            WHEN

                EXISTS (

                    SELECT 1

                    FROM roles

                    WHERE role_id =
                          NEW.role_id

                      AND name =
                          'ALUMNI'
                )

                AND

                EXISTS (

                    SELECT 1

                    FROM terms

                    WHERE term_id =
                          NEW.term_id

                      AND status IN (
                          'ACTIVE',
                          'DRAFT'
                      )
                )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'ALUMNI role cannot be used in ACTIVE or DRAFT mandates'
                );

            END;

-- ============================================================
-- TRIGGER: trg_organization_relation_snapshot_insert
-- ============================================================

CREATE TRIGGER trg_organization_relation_snapshot_insert

        AFTER INSERT

        ON organization_relations

        FOR EACH ROW

        BEGIN

            UPDATE organization_relations

            SET

                organization_name_snapshot = (

                    SELECT name

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_type_snapshot = (

                    SELECT organization_type

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_description_snapshot = (

                    SELECT description

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_address_snapshot = (

                    SELECT address

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_website_snapshot = (

                    SELECT website

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_email_snapshot = (

                    SELECT email

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_phone_snapshot = (

                    SELECT phone

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_logo_path_snapshot = (

                    SELECT logo_path

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_original_logo_filename_snapshot = (

                    SELECT original_logo_filename

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                )


            WHERE
                organization_relation_id =
                NEW.organization_relation_id;

        END;

-- ============================================================
-- TRIGGER: trg_organization_current_snapshot_sync
-- ============================================================

CREATE TRIGGER trg_organization_current_snapshot_sync

        AFTER UPDATE OF

            name,

            organization_type,

            description,

            address,

            website,

            email,

            phone,

            logo_path,

            original_logo_filename

        ON organizations

        FOR EACH ROW

        BEGIN

            UPDATE organization_relations

            SET

                organization_name_snapshot =
                    NEW.name,

                organization_type_snapshot =
                    NEW.organization_type,

                organization_description_snapshot =
                    NEW.description,

                organization_address_snapshot =
                    NEW.address,

                organization_website_snapshot =
                    NEW.website,

                organization_email_snapshot =
                    NEW.email,

                organization_phone_snapshot =
                    NEW.phone,

                organization_logo_path_snapshot =
                    NEW.logo_path,

                organization_original_logo_filename_snapshot =
                    NEW.original_logo_filename


            WHERE
                organization_id =
                NEW.organization_id

              AND term_id IN (

                    SELECT term_id

                    FROM terms

                    WHERE status !=
                          'ARCHIVED'
              );

        END;

-- ============================================================
-- TRIGGER: trg_archived_terms_no_update
-- ============================================================

CREATE TRIGGER trg_archived_terms_no_update

        BEFORE UPDATE

        ON terms

        FOR EACH ROW

        WHEN OLD.status = 'ARCHIVED'

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_terms_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_terms_no_delete

        BEFORE DELETE

        ON terms

        FOR EACH ROW

        WHEN OLD.status = 'ARCHIVED'

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_memberships_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_memberships_no_insert

        BEFORE INSERT

        ON memberships

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived membership cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_memberships_no_update
-- ============================================================

CREATE TRIGGER trg_archived_memberships_no_update

        BEFORE UPDATE

        ON memberships

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived membership cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_memberships_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_memberships_no_delete

        BEFORE DELETE

        ON memberships

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived membership cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_annual_schedule_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_annual_schedule_no_insert

        BEFORE INSERT

        ON annual_schedule

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived annual_schedule data cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_annual_schedule_no_update
-- ============================================================

CREATE TRIGGER trg_archived_annual_schedule_no_update

        BEFORE UPDATE

        ON annual_schedule

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived annual_schedule data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_annual_schedule_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_annual_schedule_no_delete

        BEFORE DELETE

        ON annual_schedule

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived annual_schedule data cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_application_periods_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_application_periods_no_insert

        BEFORE INSERT

        ON application_periods

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived application_periods data cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_application_periods_no_update
-- ============================================================

CREATE TRIGGER trg_archived_application_periods_no_update

        BEFORE UPDATE

        ON application_periods

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived application_periods data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_application_periods_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_application_periods_no_delete

        BEFORE DELETE

        ON application_periods

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived application_periods data cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_mandate_elections_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_mandate_elections_no_insert

        BEFORE INSERT

        ON mandate_elections

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate_elections data cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_mandate_elections_no_update
-- ============================================================

CREATE TRIGGER trg_archived_mandate_elections_no_update

        BEFORE UPDATE

        ON mandate_elections

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate_elections data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_mandate_elections_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_mandate_elections_no_delete

        BEFORE DELETE

        ON mandate_elections

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate_elections data cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_mandate_approvals_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_mandate_approvals_no_insert

        BEFORE INSERT

        ON mandate_approvals

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate_approvals data cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_mandate_approvals_no_update
-- ============================================================

CREATE TRIGGER trg_archived_mandate_approvals_no_update

        BEFORE UPDATE

        ON mandate_approvals

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate_approvals data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_mandate_approvals_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_mandate_approvals_no_delete

        BEFORE DELETE

        ON mandate_approvals

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived mandate_approvals data cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_events_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_events_no_insert

        BEFORE INSERT

        ON events

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_events_no_update
-- ============================================================

CREATE TRIGGER trg_archived_events_no_update

        BEFORE UPDATE

        ON events

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_events_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_events_no_delete

        BEFORE DELETE

        ON events

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_media_insert
-- ============================================================

CREATE TRIGGER trg_archived_event_media_insert

        BEFORE INSERT

        ON event_media

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_media_update
-- ============================================================

CREATE TRIGGER trg_archived_event_media_update

        BEFORE UPDATE

        ON event_media

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_media_delete
-- ============================================================

CREATE TRIGGER trg_archived_event_media_delete

        BEFORE DELETE

        ON event_media

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = OLD.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_attendance_insert
-- ============================================================

CREATE TRIGGER trg_archived_event_attendance_insert

        BEFORE INSERT

        ON event_attendance

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_attendance_update
-- ============================================================

CREATE TRIGGER trg_archived_event_attendance_update

        BEFORE UPDATE

        ON event_attendance

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_attendance_delete
-- ============================================================

CREATE TRIGGER trg_archived_event_attendance_delete

        BEFORE DELETE

        ON event_attendance

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = OLD.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_documents_insert
-- ============================================================

CREATE TRIGGER trg_archived_event_documents_insert

        BEFORE INSERT

        ON event_documents

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_documents_update
-- ============================================================

CREATE TRIGGER trg_archived_event_documents_update

        BEFORE UPDATE

        ON event_documents

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_documents_delete
-- ============================================================

CREATE TRIGGER trg_archived_event_documents_delete

        BEFORE DELETE

        ON event_documents

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = OLD.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_organizations_insert
-- ============================================================

CREATE TRIGGER trg_archived_event_organizations_insert

        BEFORE INSERT

        ON event_organizations

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_organizations_update
-- ============================================================

CREATE TRIGGER trg_archived_event_organizations_update

        BEFORE UPDATE

        ON event_organizations

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = NEW.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_event_organizations_delete
-- ============================================================

CREATE TRIGGER trg_archived_event_organizations_delete

        BEFORE DELETE

        ON event_organizations

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM events JOIN terms ON events.term_id = terms.term_id WHERE events.event_id = OLD.event_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived event data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_terms_insert
-- ============================================================

CREATE TRIGGER trg_archived_project_terms_insert

        BEFORE INSERT

        ON project_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects term link cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_terms_update
-- ============================================================

CREATE TRIGGER trg_archived_project_terms_update

        BEFORE UPDATE

        ON project_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects term link cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_terms_delete
-- ============================================================

CREATE TRIGGER trg_archived_project_terms_delete

        BEFORE DELETE

        ON project_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects term link cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_projects_update
-- ============================================================

CREATE TRIGGER trg_archived_projects_update

        BEFORE UPDATE

        ON projects

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = OLD.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_projects_delete
-- ============================================================

CREATE TRIGGER trg_archived_projects_delete

        BEFORE DELETE

        ON projects

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = OLD.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_members_insert
-- ============================================================

CREATE TRIGGER trg_archived_project_members_insert

        BEFORE INSERT

        ON project_members

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = NEW.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_members_update
-- ============================================================

CREATE TRIGGER trg_archived_project_members_update

        BEFORE UPDATE

        ON project_members

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = NEW.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_members_delete
-- ============================================================

CREATE TRIGGER trg_archived_project_members_delete

        BEFORE DELETE

        ON project_members

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = OLD.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_volunteers_insert
-- ============================================================

CREATE TRIGGER trg_archived_project_volunteers_insert

        BEFORE INSERT

        ON project_volunteers

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = NEW.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_volunteers_update
-- ============================================================

CREATE TRIGGER trg_archived_project_volunteers_update

        BEFORE UPDATE

        ON project_volunteers

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = NEW.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_project_volunteers_delete
-- ============================================================

CREATE TRIGGER trg_archived_project_volunteers_delete

        BEFORE DELETE

        ON project_volunteers

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM project_terms JOIN terms ON project_terms.term_id = terms.term_id WHERE project_terms.project_id = OLD.project_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived projects data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_terms_insert
-- ============================================================

CREATE TRIGGER trg_archived_article_terms_insert

        BEFORE INSERT

        ON article_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles term link cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_terms_update
-- ============================================================

CREATE TRIGGER trg_archived_article_terms_update

        BEFORE UPDATE

        ON article_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles term link cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_terms_delete
-- ============================================================

CREATE TRIGGER trg_archived_article_terms_delete

        BEFORE DELETE

        ON article_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles term link cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_scientific_articles_update
-- ============================================================

CREATE TRIGGER trg_archived_scientific_articles_update

        BEFORE UPDATE

        ON scientific_articles

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = OLD.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_scientific_articles_delete
-- ============================================================

CREATE TRIGGER trg_archived_scientific_articles_delete

        BEFORE DELETE

        ON scientific_articles

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = OLD.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_authors_insert
-- ============================================================

CREATE TRIGGER trg_archived_article_authors_insert

        BEFORE INSERT

        ON article_authors

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = NEW.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_authors_update
-- ============================================================

CREATE TRIGGER trg_archived_article_authors_update

        BEFORE UPDATE

        ON article_authors

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = NEW.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_authors_delete
-- ============================================================

CREATE TRIGGER trg_archived_article_authors_delete

        BEFORE DELETE

        ON article_authors

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = OLD.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_volunteers_insert
-- ============================================================

CREATE TRIGGER trg_archived_article_volunteers_insert

        BEFORE INSERT

        ON article_volunteers

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = NEW.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_volunteers_update
-- ============================================================

CREATE TRIGGER trg_archived_article_volunteers_update

        BEFORE UPDATE

        ON article_volunteers

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = NEW.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_volunteers_delete
-- ============================================================

CREATE TRIGGER trg_archived_article_volunteers_delete

        BEFORE DELETE

        ON article_volunteers

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = OLD.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_source_references_insert
-- ============================================================

CREATE TRIGGER trg_archived_article_source_references_insert

        BEFORE INSERT

        ON article_source_references

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = NEW.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_source_references_update
-- ============================================================

CREATE TRIGGER trg_archived_article_source_references_update

        BEFORE UPDATE

        ON article_source_references

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = NEW.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_article_source_references_delete
-- ============================================================

CREATE TRIGGER trg_archived_article_source_references_delete

        BEFORE DELETE

        ON article_source_references

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM article_terms JOIN terms ON article_terms.term_id = terms.term_id WHERE article_terms.scientific_article_id = OLD.scientific_article_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived scientific_articles data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_terms_insert
-- ============================================================

CREATE TRIGGER trg_archived_training_terms_insert

        BEFORE INSERT

        ON training_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings term link cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_terms_update
-- ============================================================

CREATE TRIGGER trg_archived_training_terms_update

        BEFORE UPDATE

        ON training_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings term link cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_terms_delete
-- ============================================================

CREATE TRIGGER trg_archived_training_terms_delete

        BEFORE DELETE

        ON training_terms

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings term link cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_trainings_update
-- ============================================================

CREATE TRIGGER trg_archived_trainings_update

        BEFORE UPDATE

        ON trainings

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = OLD.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_trainings_delete
-- ============================================================

CREATE TRIGGER trg_archived_trainings_delete

        BEFORE DELETE

        ON trainings

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = OLD.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_attendance_insert
-- ============================================================

CREATE TRIGGER trg_archived_training_attendance_insert

        BEFORE INSERT

        ON training_attendance

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = NEW.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_attendance_update
-- ============================================================

CREATE TRIGGER trg_archived_training_attendance_update

        BEFORE UPDATE

        ON training_attendance

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = NEW.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_attendance_delete
-- ============================================================

CREATE TRIGGER trg_archived_training_attendance_delete

        BEFORE DELETE

        ON training_attendance

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = OLD.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_media_insert
-- ============================================================

CREATE TRIGGER trg_archived_training_media_insert

        BEFORE INSERT

        ON training_media

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = NEW.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_media_update
-- ============================================================

CREATE TRIGGER trg_archived_training_media_update

        BEFORE UPDATE

        ON training_media

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = NEW.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_training_media_delete
-- ============================================================

CREATE TRIGGER trg_archived_training_media_delete

        BEFORE DELETE

        ON training_media

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM training_terms JOIN terms ON training_terms.term_id = terms.term_id WHERE training_terms.training_id = OLD.training_id AND terms.status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived trainings data cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_organization_relations_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_organization_relations_no_insert

        BEFORE INSERT

        ON organization_relations

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived organization relation cannot be created'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_organization_relations_no_update
-- ============================================================

CREATE TRIGGER trg_archived_organization_relations_no_update

        BEFORE UPDATE

        ON organization_relations

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED') OR EXISTS (SELECT 1 FROM terms WHERE term_id = NEW.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived organization relation cannot be modified'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_organization_relations_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_organization_relations_no_delete

        BEFORE DELETE

        ON organization_relations

        FOR EACH ROW

        WHEN EXISTS (SELECT 1 FROM terms WHERE term_id = OLD.term_id AND status = 'ARCHIVED')

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: archived organization relation cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_archived_organizations_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_organizations_no_delete

        BEFORE DELETE

        ON organizations

        FOR EACH ROW

        WHEN 
        EXISTS (

            SELECT 1

            FROM organization_relations

            JOIN terms

                ON organization_relations.term_id =
                   terms.term_id

            WHERE
                organization_relations.organization_id =
                OLD.organization_id

              AND terms.status =
                  'ARCHIVED'
        )
        

        BEGIN

            SELECT RAISE(
                ABORT,
                'HISTORICAL_IMMUTABILITY: organization with archived history cannot be deleted'
            );

        END;

-- ============================================================
-- TRIGGER: trg_meetings_term_required_insert
-- ============================================================

CREATE TRIGGER trg_meetings_term_required_insert

            BEFORE INSERT
            ON meetings

            FOR EACH ROW

            WHEN NEW.term_id IS NULL

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting term is required'
                );

            END;

-- ============================================================
-- TRIGGER: trg_meetings_term_required_update
-- ============================================================

CREATE TRIGGER trg_meetings_term_required_update

            BEFORE UPDATE OF term_id
            ON meetings

            FOR EACH ROW

            WHEN NEW.term_id IS NULL

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting term is required'
                );

            END;

-- ============================================================
-- TRIGGER: trg_meetings_organizer_same_term_insert
-- ============================================================

CREATE TRIGGER trg_meetings_organizer_same_term_insert

            BEFORE INSERT
            ON meetings

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.organizer_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting organizer must belong to the same mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_meetings_organizer_same_term_update
-- ============================================================

CREATE TRIGGER trg_meetings_organizer_same_term_update

            BEFORE UPDATE OF
                organizer_membership_id,
                term_id

            ON meetings

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.organizer_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting organizer must belong to the same mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_archived_meetings_no_insert
-- ============================================================

CREATE TRIGGER trg_archived_meetings_no_insert

            BEFORE INSERT
            ON meetings

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id =
                    NEW.term_id

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting cannot be created'
                );

            END;

-- ============================================================
-- TRIGGER: trg_archived_meetings_no_update
-- ============================================================

CREATE TRIGGER trg_archived_meetings_no_update

            BEFORE UPDATE
            ON meetings

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id IN (
                        OLD.term_id,
                        NEW.term_id
                    )

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting cannot be modified'
                );

            END;

-- ============================================================
-- TRIGGER: trg_archived_meetings_no_delete
-- ============================================================

CREATE TRIGGER trg_archived_meetings_no_delete

            BEFORE DELETE
            ON meetings

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id =
                    OLD.term_id

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting cannot be deleted'
                );

            END;

-- ============================================================
-- TRIGGER: trg_meeting_attendance_status_insert
-- ============================================================

CREATE TRIGGER trg_meeting_attendance_status_insert

                BEFORE INSERT
                ON meeting_attendance

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_meeting_attendance_status_update
-- ============================================================

CREATE TRIGGER trg_meeting_attendance_status_update

                BEFORE UPDATE OF
                    attendance_status

                ON meeting_attendance

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_event_attendance_status_insert
-- ============================================================

CREATE TRIGGER trg_event_attendance_status_insert

                BEFORE INSERT
                ON event_attendance

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_event_attendance_status_update
-- ============================================================

CREATE TRIGGER trg_event_attendance_status_update

                BEFORE UPDATE OF
                    attendance_status

                ON event_attendance

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_training_attendance_status_insert
-- ============================================================

CREATE TRIGGER trg_training_attendance_status_insert

                BEFORE INSERT
                ON training_attendance

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_training_attendance_status_update
-- ============================================================

CREATE TRIGGER trg_training_attendance_status_update

                BEFORE UPDATE OF
                    attendance_status

                ON training_attendance

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_meeting_attendance_same_term_insert
-- ============================================================

CREATE TRIGGER trg_meeting_attendance_same_term_insert

            BEFORE INSERT
            ON meeting_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM meetings

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    meetings.meeting_id =
                    NEW.meeting_id

                  AND memberships.term_id =
                      meetings.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting attendance member must belong to the meeting mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_meeting_attendance_same_term_update
-- ============================================================

CREATE TRIGGER trg_meeting_attendance_same_term_update

            BEFORE UPDATE OF
                meeting_id,
                membership_id

            ON meeting_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM meetings

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    meetings.meeting_id =
                    NEW.meeting_id

                  AND memberships.term_id =
                      meetings.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting attendance member must belong to the meeting mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_archived_meeting_attendance_insert
-- ============================================================

CREATE TRIGGER trg_archived_meeting_attendance_insert

                BEFORE INSERT
                ON meeting_attendance

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM meetings

                    JOIN terms

                        ON terms.term_id =
                           meetings.term_id

                    WHERE
                        meetings.meeting_id =
                        NEW.meeting_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived meeting attendance cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_meeting_attendance_delete
-- ============================================================

CREATE TRIGGER trg_archived_meeting_attendance_delete

                BEFORE DELETE
                ON meeting_attendance

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM meetings

                    JOIN terms

                        ON terms.term_id =
                           meetings.term_id

                    WHERE
                        meetings.meeting_id =
                        OLD.meeting_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived meeting attendance cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_meeting_attendance_update
-- ============================================================

CREATE TRIGGER trg_archived_meeting_attendance_update

            BEFORE UPDATE
            ON meeting_attendance

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM meetings

                JOIN terms

                    ON terms.term_id =
                       meetings.term_id

                WHERE
                    meetings.meeting_id
                    IN (
                        OLD.meeting_id,
                        NEW.meeting_id
                    )

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting attendance cannot be modified'
                );

            END;

-- ============================================================
-- TRIGGER: trg_event_attendance_same_term_insert
-- ============================================================

CREATE TRIGGER trg_event_attendance_same_term_insert

            BEFORE INSERT
            ON event_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM events

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    events.event_id =
                    NEW.event_id

                  AND memberships.term_id =
                      events.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Event attendance member must belong to the event mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_event_attendance_same_term_update
-- ============================================================

CREATE TRIGGER trg_event_attendance_same_term_update

            BEFORE UPDATE OF
                event_id,
                membership_id

            ON event_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM events

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    events.event_id =
                    NEW.event_id

                  AND memberships.term_id =
                      events.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Event attendance member must belong to the event mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_training_attendance_same_term_insert
-- ============================================================

CREATE TRIGGER trg_training_attendance_same_term_insert

            BEFORE INSERT
            ON training_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM training_terms

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    training_terms.training_id =
                    NEW.training_id

                  AND memberships.term_id =
                      training_terms.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Training attendance member must belong to the training mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_training_attendance_same_term_update
-- ============================================================

CREATE TRIGGER trg_training_attendance_same_term_update

            BEFORE UPDATE OF
                training_id,
                membership_id

            ON training_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM training_terms

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    training_terms.training_id =
                    NEW.training_id

                  AND memberships.term_id =
                      training_terms.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Training attendance member must belong to the training mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_member_notes_type_insert
-- ============================================================

CREATE TRIGGER trg_member_notes_type_insert

                BEFORE INSERT
                ON member_notes

                FOR EACH ROW

                WHEN UPPER(
                    NEW.note_type
                )
                NOT IN (
                    'REMARK',
                    'WARNING',
                    'SANCTION',
                    'POSITIVE'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid member note type'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_member_notes_type_update
-- ============================================================

CREATE TRIGGER trg_member_notes_type_update

                BEFORE UPDATE
                ON member_notes

                FOR EACH ROW

                WHEN UPPER(
                    NEW.note_type
                )
                NOT IN (
                    'REMARK',
                    'WARNING',
                    'SANCTION',
                    'POSITIVE'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid member note type'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_member_notes_same_term_insert
-- ============================================================

CREATE TRIGGER trg_member_notes_same_term_insert

            BEFORE INSERT
            ON member_notes

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships
                    AS target

                JOIN memberships
                    AS giver

                    ON giver.membership_id =
                       NEW.given_by_membership_id

                WHERE
                    target.membership_id =
                    NEW.membership_id

                  AND target.term_id =
                      giver.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Member note author and target must belong to the same mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_member_notes_same_term_update
-- ============================================================

CREATE TRIGGER trg_member_notes_same_term_update

            BEFORE UPDATE OF
                membership_id,
                given_by_membership_id

            ON member_notes

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships
                    AS target

                JOIN memberships
                    AS giver

                    ON giver.membership_id =
                       NEW.given_by_membership_id

                WHERE
                    target.membership_id =
                    NEW.membership_id

                  AND target.term_id =
                      giver.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Member note author and target must belong to the same mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_archived_member_notes_insert
-- ============================================================

CREATE TRIGGER trg_archived_member_notes_insert

                BEFORE INSERT
                ON member_notes

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM memberships

                    JOIN terms

                        ON terms.term_id =
                           memberships.term_id

                    WHERE
                        memberships.membership_id =
                        NEW.membership_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived member note cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_member_notes_delete
-- ============================================================

CREATE TRIGGER trg_archived_member_notes_delete

                BEFORE DELETE
                ON member_notes

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM memberships

                    JOIN terms

                        ON terms.term_id =
                           memberships.term_id

                    WHERE
                        memberships.membership_id =
                        OLD.membership_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived member note cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_member_notes_update
-- ============================================================

CREATE TRIGGER trg_archived_member_notes_update

            BEFORE UPDATE
            ON member_notes

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM memberships

                JOIN terms

                    ON terms.term_id =
                       memberships.term_id

                WHERE
                    memberships.membership_id
                    IN (
                        OLD.membership_id,
                        NEW.membership_id
                    )

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived member note cannot be modified'
                );

            END;

-- ============================================================
-- TRIGGER: trg_certificates_term_required_insert
-- ============================================================

CREATE TRIGGER trg_certificates_term_required_insert

            BEFORE INSERT
            ON certificates

            FOR EACH ROW

            WHEN NEW.term_id IS NULL

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Certificate mandate is required'
                );

            END;

-- ============================================================
-- TRIGGER: trg_certificates_creator_same_term_insert
-- ============================================================

CREATE TRIGGER trg_certificates_creator_same_term_insert

            BEFORE INSERT
            ON certificates

            FOR EACH ROW

            WHEN
                NEW.created_by_membership_id
                IS NOT NULL

            AND NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.created_by_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Certificate creator must belong to the same mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_certificates_creator_same_term_update
-- ============================================================

CREATE TRIGGER trg_certificates_creator_same_term_update

            BEFORE UPDATE OF
                term_id,
                created_by_membership_id

            ON certificates

            FOR EACH ROW

            WHEN
                NEW.created_by_membership_id
                IS NOT NULL

            AND NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.created_by_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Certificate creator must belong to the same mandate'
                );

            END;

-- ============================================================
-- TRIGGER: trg_archived_certificates_insert
-- ============================================================

CREATE TRIGGER trg_archived_certificates_insert

                BEFORE INSERT
                ON certificates

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM terms

                    WHERE
                        term_id =
                        NEW.term_id

                      AND status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived certificate cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_certificates_delete
-- ============================================================

CREATE TRIGGER trg_archived_certificates_delete

                BEFORE DELETE
                ON certificates

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM terms

                    WHERE
                        term_id =
                        OLD.term_id

                      AND status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived certificate cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_certificates_update
-- ============================================================

CREATE TRIGGER trg_archived_certificates_update

            BEFORE UPDATE
            ON certificates

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id IN (
                        OLD.term_id,
                        NEW.term_id
                    )

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived certificate cannot be modified'
                );

            END;

-- ============================================================
-- TRIGGER: trg_certificate_recipient_snapshot_insert
-- ============================================================

CREATE TRIGGER trg_certificate_recipient_snapshot_insert

            AFTER INSERT
            ON certificate_recipients

            FOR EACH ROW

            BEGIN

                UPDATE certificate_recipients

                SET
                    recipient_name_snapshot = (

                        SELECT
                            TRIM(
                                first_name
                                || ' '
                                || last_name
                            )

                        FROM people

                        WHERE
                            person_id =
                            NEW.person_id
                    )

                WHERE
                    certificate_recipient_id =
                    NEW.certificate_recipient_id;

            END;

-- ============================================================
-- TRIGGER: trg_archived_certificate_recipients_insert
-- ============================================================

CREATE TRIGGER trg_archived_certificate_recipients_insert

                BEFORE INSERT
                ON certificate_recipients

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM certificates

                    JOIN terms

                        ON terms.term_id =
                           certificates.term_id

                    WHERE
                        certificates.certificate_id =
                        NEW.certificate_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived certificate recipients cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_certificate_recipients_delete
-- ============================================================

CREATE TRIGGER trg_archived_certificate_recipients_delete

                BEFORE DELETE
                ON certificate_recipients

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM certificates

                    JOIN terms

                        ON terms.term_id =
                           certificates.term_id

                    WHERE
                        certificates.certificate_id =
                        OLD.certificate_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived certificate recipients cannot be modified'
                    );

                END;

-- ============================================================
-- TRIGGER: trg_archived_certificate_recipients_update
-- ============================================================

CREATE TRIGGER trg_archived_certificate_recipients_update

            BEFORE UPDATE
            ON certificate_recipients

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM certificates

                JOIN terms

                    ON terms.term_id =
                       certificates.term_id

                WHERE
                    certificates.certificate_id
                    IN (
                        OLD.certificate_id,
                        NEW.certificate_id
                    )

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived certificate recipients cannot be modified'
                );

            END;

-- ============================================================
-- TRIGGER: trg_article_source_snapshot_insert
-- ============================================================

CREATE TRIGGER trg_article_source_snapshot_insert

            AFTER INSERT
            ON article_source_references

            FOR EACH ROW

            BEGIN

                UPDATE article_source_references

                SET

                    source_title_snapshot = (

                        SELECT title

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_authors_snapshot = (

                        SELECT authors

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_type_snapshot = (

                        SELECT source_type

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_publication_year_snapshot = (

                        SELECT publication_year

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_url_snapshot = (

                        SELECT url

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_doi_snapshot = (

                        SELECT doi

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    )


                WHERE
                    article_source_reference_id =
                    NEW.article_source_reference_id;

            END;

-- ============================================================
-- TRIGGER: trg_source_reference_snapshot_sync
-- ============================================================

CREATE TRIGGER trg_source_reference_snapshot_sync

            AFTER UPDATE OF
                title,
                authors,
                source_type,
                publication_year,
                url,
                doi

            ON source_references

            FOR EACH ROW

            BEGIN

                UPDATE article_source_references

                SET

                    source_title_snapshot =
                        NEW.title,

                    source_authors_snapshot =
                        NEW.authors,

                    source_type_snapshot =
                        NEW.source_type,

                    source_publication_year_snapshot =
                        NEW.publication_year,

                    source_url_snapshot =
                        NEW.url,

                    source_doi_snapshot =
                        NEW.doi


                WHERE
                    source_reference_id =
                    NEW.source_reference_id

                  AND scientific_article_id
                      IN (

                        SELECT
                            article_terms.scientific_article_id

                        FROM article_terms

                        JOIN terms

                            ON terms.term_id =
                               article_terms.term_id

                        WHERE
                            terms.status !=
                            'ARCHIVED'
                      );

            END;

-- ============================================================
-- TRIGGER: trg_source_reference_delete_archived_guard
-- ============================================================

CREATE TRIGGER trg_source_reference_delete_archived_guard

            BEFORE DELETE
            ON source_references

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM article_source_references

                JOIN article_terms

                    ON article_terms.scientific_article_id =
                       article_source_references.scientific_article_id

                JOIN terms

                    ON terms.term_id =
                       article_terms.term_id

                WHERE
                    article_source_references.source_reference_id =
                    OLD.source_reference_id

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: source used by archived article cannot be deleted'
                );

            END;

COMMIT;
