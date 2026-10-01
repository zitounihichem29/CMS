from functools import wraps
from flask import session, redirect

from context import get_current_user


# ========================================
# LOGIN REQUIRED
# ========================================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/login")

        user = get_current_user()

        if user is None:
            session.clear()
            return redirect("/login")

        if not user["is_active"]:
            session.clear()
            return redirect("/login")

        return view(*args, **kwargs)

    return wrapped_view


# ========================================
# CURRENT MEMBER REQUIRED
# Alumni are not allowed
# ========================================

def current_member_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/login")

        user = get_current_user()

        if user is None:
            session.clear()
            return redirect("/login")

        if not user["is_active"]:
            session.clear()
            return redirect("/login")

        if user["is_alumni"]:
            return "Access denied", 403

        return view(*args, **kwargs)

    return wrapped_view


# ========================================
# ROLE REQUIRED
# ========================================

def role_required(*allowed_roles):

    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            if "user_id" not in session:
                return redirect("/login")

            user = get_current_user()

            if user is None:
                session.clear()
                return redirect("/login")

            if not user["is_active"]:
                session.clear()
                return redirect("/login")

            # Alumni must never inherit
            # permissions from an old mandate.
            if user["is_alumni"]:
                return "Access denied", 403

            if user["role_name"] not in allowed_roles:
                return "Access denied", 403

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


# ========================================
# PLATFORM ADMIN REQUIRED
# Technical / emergency administration only
# ========================================

def platform_admin_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            return redirect("/login")

        user = get_current_user()

        if user is None:
            session.clear()
            return redirect("/login")

        if not user["is_active"]:
            session.clear()
            return redirect("/login")

        if not user["is_platform_admin"]:
            return "Access denied", 403

        return view(*args, **kwargs)

    return wrapped_view