from functools import wraps
from flask import abort
from flask_login import current_user, login_required

def roles_required(*role_names):
    """
    Protect a route so that only users with at least one of the roles can access it.
    Usage: @roles_required('Physician') or @roles_required('Physician', 'Admin')
    """
    def decorator(f):
        @wraps(f)
        @login_required  # ensures user is logged in first
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # unauthorized
            if not any(current_user.has_role(role) for role in role_names):
                abort(403)  # forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator
