from __future__ import annotations

from typing import Optional

from django.http import HttpRequest


def current_school(request: HttpRequest):
    school = None

    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        school_profile = getattr(user, 'school_profile', None)
        if school_profile is not None:
            school = getattr(school_profile, 'school', None)

        if school is None and getattr(user, 'is_superuser', False):
            try:
                from .models import School

                active_school_id = request.session.get('active_school_id')
                if active_school_id:
                    school = School.objects.filter(id=active_school_id).first()

                if school is None:
                    school = School.objects.order_by('id').first()
            except Exception:
                school = None

    return {
        'current_school': school,
        'school': school,
    }
