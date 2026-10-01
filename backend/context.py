from flask import session

from database import (
    get_db_connection,
)


# ============================================================
# ACTIVE TERM
# ============================================================

def get_active_term():

    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status

        FROM terms

        WHERE status = 'ACTIVE'

        LIMIT 1
        """
    )


    term = (
        cursor.fetchone()
    )


    conn.close()


    return term


def get_active_term_id():

    term = (
        get_active_term()
    )


    if term is None:

        return None


    return term[
        "term_id"
    ]


# ============================================================
# CURRENT USER
# ============================================================

def get_current_user():

    if "user_id" not in session:

        return None


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    cursor.execute(
        """
        SELECT

            users.user_id,

            users.username,

            users.is_active,

            users.is_platform_admin,


            people.person_id,

            people.first_name,

            people.last_name,

            people.profile_photo,

            people.email,


            memberships.membership_id,


            roles.role_id,

            roles.name
                AS role_name,


            departments.department_id,

            departments.name
                AS department_name,


            active_term.term_id
                AS term_id,

            active_term.name
                AS term_name,


            alumni_profiles.alumni_id,

            alumni_profiles.is_public
                AS alumni_is_public,

            alumni_profiles.is_featured
                AS alumni_is_featured,

            alumni_profiles.is_spotlight
                AS alumni_is_spotlight,


            CASE

                WHEN alumni_profiles.alumni_id
                     IS NULL

                    THEN 0

                ELSE 1

            END
                AS has_alumni_profile,


            CASE

                WHEN memberships.membership_id
                     IS NULL

                    THEN 1


                WHEN roles.name =
                     'ALUMNI'

                    THEN 1


                ELSE 0

            END
                AS is_alumni


        FROM users


        JOIN people

            ON users.person_id =
               people.person_id


        LEFT JOIN terms
            AS active_term

            ON active_term.status =
               'ACTIVE'


        LEFT JOIN memberships

            ON people.person_id =
               memberships.person_id

            AND memberships.term_id =
                active_term.term_id


        LEFT JOIN roles

            ON memberships.role_id =
               roles.role_id


        LEFT JOIN departments

            ON memberships.department_id =
               departments.department_id


        LEFT JOIN alumni_profiles

            ON people.person_id =
               alumni_profiles.person_id


        WHERE users.user_id = ?
        """,
        (
            session[
                "user_id"
            ],
        ),
    )


    user = (
        cursor.fetchone()
    )


    conn.close()


    return user