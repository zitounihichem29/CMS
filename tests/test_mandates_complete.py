import io
import shutil
from pathlib import Path

import database

from app import app


BACKEND_DIR = (
    Path(__file__).resolve().parent
)

REAL_DB = (
    BACKEND_DIR.parent
    / "database"
    / "rsclub.db"
)

TEST_DB = (
    BACKEND_DIR.parent
    / "database"
    / "mandates_complete_test.db"
)


def require(
    condition,
    message,
):
    if not condition:
        raise RuntimeError(
            message
        )


def login(
    client,
    user_id,
):
    with client.session_transaction() as session:
        session["user_id"] = (
            user_id
        )


def redirect_ok(
    response,
):
    return response.status_code in {
        301,
        302,
        303,
        307,
        308,
    }


if TEST_DB.exists():
    TEST_DB.unlink()


shutil.copy2(
    REAL_DB,
    TEST_DB,
)


database.DATABASE_PATH = (
    TEST_DB
)


created_report_path = None


try:

    conn = (
        database.get_db_connection()
    )


    active_term = conn.execute(
        """
        SELECT
            term_id,
            name

        FROM terms

        WHERE status = 'ACTIVE'

        LIMIT 1
        """
    ).fetchone()


    draft_term = conn.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date

        FROM terms

        WHERE status = 'DRAFT'

        LIMIT 1
        """
    ).fetchone()


    require(
        active_term is not None,
        "No ACTIVE term found.",
    )


    require(
        draft_term is not None,
        "No DRAFT term found.",
    )


    president = conn.execute(
        """
        SELECT
            u.user_id,
            u.username,
            p.person_id

        FROM users u

        JOIN people p
            ON u.person_id =
               p.person_id

        JOIN memberships m
            ON p.person_id =
               m.person_id

        JOIN roles r
            ON m.role_id =
               r.role_id

        WHERE m.term_id = ?
          AND r.name = 'PRESIDENT'
          AND u.is_active = 1

        LIMIT 1
        """,
        (
            active_term[
                "term_id"
            ],
        ),
    ).fetchone()


    vice_president = conn.execute(
        """
        SELECT
            u.user_id,
            u.username,
            p.person_id

        FROM users u

        JOIN people p
            ON u.person_id =
               p.person_id

        JOIN memberships m
            ON p.person_id =
               m.person_id

        JOIN roles r
            ON m.role_id =
               r.role_id

        WHERE m.term_id = ?
          AND r.name = 'VICE_PRESIDENT'
          AND u.is_active = 1

        LIMIT 1
        """,
        (
            active_term[
                "term_id"
            ],
        ),
    ).fetchone()


    hr_head = conn.execute(
        """
        SELECT
            u.user_id,
            u.username,
            p.person_id

        FROM users u

        JOIN people p
            ON u.person_id =
               p.person_id

        JOIN memberships m
            ON p.person_id =
               m.person_id

        JOIN roles r
            ON m.role_id =
               r.role_id

        WHERE m.term_id = ?
          AND r.name = 'HEAD'
          AND m.department_id = 1
          AND u.is_active = 1

        LIMIT 1
        """,
        (
            active_term[
                "term_id"
            ],
        ),
    ).fetchone()


    platform_admin = conn.execute(
        """
        SELECT
            u.user_id,
            u.username,
            p.person_id

        FROM users u

        JOIN people p
            ON u.person_id =
               p.person_id

        WHERE u.is_platform_admin = 1
          AND u.is_active = 1

        ORDER BY
            u.user_id

        LIMIT 1
        """
    ).fetchone()


    require(
        president is not None,
        "Outgoing President missing.",
    )

    require(
        vice_president is not None,
        "Outgoing VP missing.",
    )

    require(
        hr_head is not None,
        "HR Head missing.",
    )

    require(
        platform_admin is not None,
        "Platform admin missing.",
    )


    secretary_candidate = conn.execute(
        """
        SELECT
            u.user_id,
            u.username,
            p.person_id

        FROM users u

        JOIN people p
            ON u.person_id =
               p.person_id

        WHERE u.is_active = 1

          AND p.person_id
              NOT IN (?, ?)

        ORDER BY
            CASE
                WHEN p.person_id = 1
                THEN 0
                ELSE 1
            END,

            p.person_id

        LIMIT 1
        """,
        (
            president[
                "person_id"
            ],
            vice_president[
                "person_id"
            ],
        ),
    ).fetchone()


    require(
        secretary_candidate
        is not None,
        "Secretary candidate missing.",
    )


    print(
        "ACTIVE:",
        active_term["name"]
    )

    print(
        "DRAFT:",
        draft_term["name"]
    )

    print(
        "President:",
        president["username"]
    )

    print(
        "Vice President:",
        vice_president["username"]
    )

    print(
        "HR Head:",
        hr_head["username"]
    )

    print(
        "Platform Admin:",
        platform_admin["username"]
    )


    conn.execute(
        """
        DELETE FROM mandate_approvals
        WHERE term_id = ?
        """,
        (
            draft_term[
                "term_id"
            ],
        ),
    )


    conn.execute(
        """
        DELETE FROM mandate_elections
        WHERE term_id = ?
        """,
        (
            draft_term[
                "term_id"
            ],
        ),
    )


    conn.commit()
    conn.close()


    with app.test_client() as client:

        login(
            client,
            president["user_id"],
        )

        response = client.get(
            f"/mandates/"
            f"{draft_term['term_id']}"
        )

        require(
            response.status_code
            == 200,
            "Mandate detail failed.",
        )

        body = response.get_data(
            as_text=True
        )

        require(
            "Basic Information"
            in body,
            "Step 1 missing.",
        )

        require(
            "Election Result"
            in body,
            "Step 2 missing.",
        )

        require(
            (
                "Board &amp; Members"
                in body
            )
            or (
                "Board & Members"
                in body
            ),
            "Step 3 missing.",
        )

        require(
            (
                "Review &amp; Activation"
                in body
            )
            or (
                "Review & Activation"
                in body
            ),
            "Step 4 missing.",
        )


    print(
        "Four-step mandate UI: OK"
    )


    with app.test_client() as client:

        login(
            client,
            platform_admin[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/basic/save",
            data={
                "name":
                    draft_term[
                        "name"
                    ],

                "start_date":
                    draft_term[
                        "start_date"
                    ],

                "end_date":
                    "2027-08-30",
            },
        )

        require(
            response.status_code
            == 400,
            (
                "Admin basic edit "
                "without reason was allowed."
            ),
        )


        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/basic/save",
            data={
                "name":
                    draft_term[
                        "name"
                    ],

                "start_date":
                    draft_term[
                        "start_date"
                    ],

                "end_date":
                    "2027-08-30",

                "emergency_reason":
                    (
                        "Automated "
                        "governance test."
                    ),
            },
            follow_redirects=False,
        )

        require(
            redirect_ok(
                response
            ),
            (
                "Admin basic edit "
                "with reason failed."
            ),
        )


    print(
        "Platform Admin emergency "
        "reason enforcement: OK"
    )


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/basic/save",
            data={
                "name":
                    draft_term[
                        "name"
                    ],

                "start_date":
                    draft_term[
                        "start_date"
                    ],

                "end_date":
                    draft_term[
                        "end_date"
                    ],
            },
            follow_redirects=False,
        )

        require(
            redirect_ok(
                response
            ),
            (
                "President basic "
                "edit failed."
            ),
        )


    print(
        "Basic information edit: OK"
    )


    election_data = {

        "election_date":
            "2026-09-15",

        "president_person_id":
            str(
                president[
                    "person_id"
                ]
            ),

        "vice_president_person_id":
            str(
                vice_president[
                    "person_id"
                ]
            ),

        "secretary_general_person_id":
            str(
                secretary_candidate[
                    "person_id"
                ]
            ),

        "notes":
            (
                "Automated complete "
                "mandate test."
            ),
    }


    with app.test_client() as client:

        login(
            client,
            hr_head[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/election/save",
            data=election_data,
        )

        require(
            response.status_code
            == 403,
            (
                "HR was allowed "
                "to edit election."
            ),
        )


    print(
        "Election permission "
        "separation: OK"
    )


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        payload = dict(
            election_data
        )

        payload[
            "report_file"
        ] = (
            io.BytesIO(
                b"%PDF-1.4 "
                b"test mandate PV"
            ),
            "election_test.pdf",
        )


        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/election/save",
            data=payload,
            content_type=(
                "multipart/form-data"
            ),
            follow_redirects=False,
        )

        require(
            redirect_ok(
                response
            ),
            "Election save failed.",
        )


    conn = (
        database.get_db_connection()
    )


    election = conn.execute(
        """
        SELECT *
        FROM mandate_elections
        WHERE term_id = ?
        """,
        (
            draft_term[
                "term_id"
            ],
        ),
    ).fetchone()


    require(
        election is not None,
        "Election record missing.",
    )


    require(
        election[
            "report_path"
        ],
        (
            "Election PV "
            "path missing."
        ),
    )


    created_report_path = (
        BACKEND_DIR
        / election[
            "report_path"
        ]
    )


    require(
        created_report_path.exists(),
        (
            "Election PV "
            "file missing."
        ),
    )


    conn.close()


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        response = client.get(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/election/report"
        )

        require(
            response.status_code
            == 200,
            (
                "Election PV "
                "route failed."
            ),
        )


    print(
        "Election result + "
        "PV upload/view: OK"
    )


    conn = (
        database.get_db_connection()
    )


    executive_role_id = (
        conn.execute(
            """
            SELECT role_id
            FROM roles
            WHERE name = 'PRESIDENT'
            """
        ).fetchone()[0]
    )


    member_role_id = (
        conn.execute(
            """
            SELECT role_id
            FROM roles
            WHERE name = 'MEMBER'
            """
        ).fetchone()[0]
    )


    conn.close()


    with app.test_client() as client:

        login(
            client,
            hr_head[
                "user_id"
            ],
        )


        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/memberships/save",
            data={
                "person_id":
                    str(
                        secretary_candidate[
                            "person_id"
                        ]
                    ),

                "role_id":
                    str(
                        executive_role_id
                    ),

                "department_id":
                    "2",
            },
        )


        require(
            response.status_code
            == 400,
            (
                "HR executive role "
                "edit was allowed."
            ),
        )


        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/memberships/save",
            data={
                "person_id":
                    str(
                        president[
                            "person_id"
                        ]
                    ),

                "role_id":
                    str(
                        member_role_id
                    ),

                "department_id":
                    "2",
            },
        )


        require(
            response.status_code
            == 400,
            (
                "HR changed elected "
                "President through "
                "board route."
            ),
        )


    print(
        "Executive role lock for HR: OK"
    )


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/approve/PRESIDENT",
            follow_redirects=False,
        )

        require(
            redirect_ok(
                response
            ),
            (
                "President "
                "approval failed."
            ),
        )


    with app.test_client() as client:

        login(
            client,
            vice_president[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/approve/VICE_PRESIDENT",
            follow_redirects=False,
        )

        require(
            redirect_ok(
                response
            ),
            (
                "VP approval failed."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    approval_count = (
        conn.execute(
            """
            SELECT COUNT(*)
            FROM mandate_approvals
            WHERE term_id = ?
            """,
            (
                draft_term[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        approval_count == 2,
        (
            "Both approvals "
            "were not recorded."
        ),
    )


    conn.close()


    print(
        "President + VP approvals: OK"
    )


    non_exec = None


    conn = (
        database.get_db_connection()
    )


    rows = conn.execute(
        """
        SELECT
            m.person_id,
            m.role_id,
            m.department_id,
            r.name AS role_name

        FROM memberships m

        JOIN roles r
            ON m.role_id =
               r.role_id

        WHERE m.term_id = ?

          AND r.name NOT IN (
              'PRESIDENT',
              'VICE_PRESIDENT',
              'SECRETARY_GENERAL'
          )

          AND m.person_id != ?

        ORDER BY
            m.membership_id
        """,
        (
            draft_term[
                "term_id"
            ],
            hr_head[
                "person_id"
            ],
        ),
    ).fetchall()


    for row in rows:

        if row[
            "department_id"
        ]:
            non_exec = row
            break


    conn.close()


    require(
        non_exec is not None,
        (
            "No non-executive "
            "draft member available "
            "for reset test."
        ),
    )


    conn = (
        database.get_db_connection()
    )


    sub_head_role_id = (
        conn.execute(
            """
            SELECT role_id
            FROM roles
            WHERE name = 'SUB_HEAD'
            """
        ).fetchone()[0]
    )


    member_role_id = (
        conn.execute(
            """
            SELECT role_id
            FROM roles
            WHERE name = 'MEMBER'
            """
        ).fetchone()[0]
    )


    conn.close()


    new_role_id = (
        member_role_id

        if non_exec[
            "role_id"
        ] != member_role_id

        else sub_head_role_id
    )


    with app.test_client() as client:

        login(
            client,
            hr_head[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/memberships/save",
            data={
                "person_id":
                    str(
                        non_exec[
                            "person_id"
                        ]
                    ),

                "role_id":
                    str(
                        new_role_id
                    ),

                "department_id":
                    str(
                        non_exec[
                            "department_id"
                        ]
                    ),
            },
            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),
            "HR board update failed.",
        )


    conn = (
        database.get_db_connection()
    )


    approval_count = (
        conn.execute(
            """
            SELECT COUNT(*)
            FROM mandate_approvals
            WHERE term_id = ?
            """,
            (
                draft_term[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        approval_count == 0,
        (
            "Board change did "
            "not reset approvals."
        ),
    )


    conn.close()


    print(
        "Approval reset after "
        "board change: OK"
    )


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/approve/PRESIDENT",
            follow_redirects=False,
        )

        require(
            redirect_ok(
                response
            ),
            (
                "President "
                "re-approval failed."
            ),
        )


    with app.test_client() as client:

        login(
            client,
            vice_president[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/approve/VICE_PRESIDENT",
            follow_redirects=False,
        )

        require(
            redirect_ok(
                response
            ),
            (
                "VP re-approval failed."
            ),
        )


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{draft_term['term_id']}"
            f"/activate",
            follow_redirects=False,
        )


        if not redirect_ok(
            response
        ):
            print(
                response.get_data(
                    as_text=True
                )
            )


        require(
            redirect_ok(
                response
            ),
            (
                "Normal President "
                "activation failed."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    new_status = (
        conn.execute(
            """
            SELECT status
            FROM terms
            WHERE term_id = ?
            """,
            (
                draft_term[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    old_status = (
        conn.execute(
            """
            SELECT status
            FROM terms
            WHERE term_id = ?
            """,
            (
                active_term[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        new_status == "ACTIVE",
        (
            "Draft was not "
            "activated."
        ),
    )


    require(
        old_status == "ARCHIVED",
        (
            "Old active term "
            "was not archived."
        ),
    )


    activation_log = (
        conn.execute(
            """
            SELECT action

            FROM mandate_audit_log

            WHERE term_id = ?
              AND action =
                  'MANDATE_ACTIVATED'

            ORDER BY
                log_id DESC

            LIMIT 1
            """,
            (
                draft_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        activation_log
        is not None,
        (
            "Activation audit "
            "log missing."
        ),
    )


    integrity = (
        conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
    )


    foreign_keys = (
        conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
    )


    conn.close()


    require(
        integrity == "ok",
        "Integrity check failed.",
    )


    require(
        not foreign_keys,
        "Foreign key check failed.",
    )


    print(
        "Atomic activation + audit: OK"
    )


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        response = client.post(
            "/mandates/new",
            data={
                "name":
                    "2099/2100",

                "start_date":
                    "2099-09-01",

                "end_date":
                    "2100-08-31",
            },
            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),
            (
                "Clean draft "
                "creation failed."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    clean_draft = (
        conn.execute(
            """
            SELECT
                term_id,
                name

            FROM terms

            WHERE status = 'DRAFT'

            LIMIT 1
            """
        ).fetchone()
    )


    require(
        clean_draft
        is not None,
        (
            "Clean DRAFT "
            "was not created."
        ),
    )


    clean_draft_id = (
        clean_draft[
            "term_id"
        ]
    )


    conn.close()


    with app.test_client() as client:

        login(
            client,
            president[
                "user_id"
            ],
        )

        response = client.post(
            f"/mandates/"
            f"{clean_draft_id}"
            f"/delete",
            data={
                "confirmation":
                    clean_draft[
                        "name"
                    ],
            },
            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),
            (
                "Clean DRAFT "
                "deletion failed."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    deleted = (
        conn.execute(
            """
            SELECT term_id
            FROM terms
            WHERE term_id = ?
            """,
            (
                clean_draft_id,
            ),
        ).fetchone()
    )


    delete_log = (
        conn.execute(
            """
            SELECT
                action,
                term_id

            FROM mandate_audit_log

            WHERE term_name =
                  '2099/2100'

              AND action =
                  'DRAFT_DELETED'

            ORDER BY
                log_id DESC

            LIMIT 1
            """
        ).fetchone()
    )


    require(
        deleted is None,
        "DRAFT was not deleted.",
    )


    require(
        delete_log is not None,
        (
            "DRAFT deletion "
            "audit log missing."
        ),
    )


    conn.close()


    print(
        "Draft create/delete "
        "+ preserved audit: OK"
    )


    print()

    print(
        "========================================"
    )

    print(
        "MANDATES COMPLETE TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )

    print(
        "Four-step UI: OK"
    )

    print(
        "Basic information editing: OK"
    )

    print(
        "Election permissions: OK"
    )

    print(
        "Election result + PV: OK"
    )

    print(
        "HR executive lock: OK"
    )

    print(
        "President / VP approvals: OK"
    )

    print(
        "Approval reset after changes: OK"
    )

    print(
        "Required account readiness: OK"
    )

    print(
        "Atomic activation: OK"
    )

    print(
        "Audit logging: OK"
    )

    print(
        "Emergency reason enforcement: OK"
    )

    print(
        "Draft create/delete: OK"
    )

    print(
        "Integrity check:",
        integrity
    )

    print(
        "Foreign key check:",
        foreign_keys
    )


finally:

    if (
        created_report_path
        and created_report_path.exists()
    ):
        try:
            created_report_path.unlink()

        except OSError:
            pass


    if TEST_DB.exists():
        TEST_DB.unlink()


    print(
        "Temporary database deleted."
    )