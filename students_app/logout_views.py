from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib import messages
from django.http import JsonResponse

def custom_logout(request):
    """Custom logout view with messages"""
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Successfully logged out, {username}!')
    else:
        messages.info(request, 'You were not logged in.')
    
    return redirect('students_app:simple_login')

def ajax_logout(request):
    """AJAX logout for better UX"""
    if request.user.is_authenticated:
        username = request.user.username
        
        # Clear all custom session keys
        keys_to_clear = [
            'parent_logged_in', 'parent_student_id',
            'teacher_logged_in', 'teacher_id',
            'student_logged_in', 'student_id',
            'librarian_logged_in', 'librarian_id'
        ]
        for key in keys_to_clear:
            if key in request.session:
                del request.session[key]
        
        logout(request)
        return JsonResponse({
            'success': True,
            'message': f'Successfully logged out, {username}!',
            'redirect_url': '/simple-login/'
        })
    else:
        return JsonResponse({
            'success': True,  # Treat as success if already logged out
            'message': 'You were already logged out.',
            'redirect_url': '/simple-login/'
        })

