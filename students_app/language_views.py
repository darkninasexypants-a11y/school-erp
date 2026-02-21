from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils.translation import activate


@login_required
@require_POST
def switch_language(request):
    """
    Persist the chosen language in the user's session.
    Accepts 'language' = 'en' or 'hi'.
    """
    lang = request.POST.get('language', 'en')
    if lang not in ('en', 'hi'):
        lang = 'en'
    request.session['language'] = lang
    try:
        # If Django i18n is used elsewhere, activate for this request too
        activate('hi' if lang == 'hi' else 'en')
    except Exception:
        pass
    return JsonResponse({'success': True, 'language': lang})

from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse
from .language_utils import set_user_language, get_user_language

def switch_language(request):
    """Switch language between Hindi and English"""
    if request.method == 'POST':
        language = request.POST.get('language', 'en')
        
        if set_user_language(request, language):
            messages.success(request, f'Language switched to {language.upper()}')
        else:
            messages.error(request, 'Invalid language selection')
    
    # Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', '/'))

def get_language_text(request):
    """API endpoint to get language text for current user"""
    language = get_user_language(request)
    from .language_utils import get_sidebar_text
    text = get_sidebar_text(language)
    return JsonResponse(text)

