from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils import timezone
import json
import time
from .models import Student, IDCardTemplate, StudentIDCard, Class, Section


@login_required
def generate_id_cards_with_progress(request):
    """Generate ID cards with real-time progress tracking"""
    from .models import Class, Section, School
    
    classes = Class.objects.all()
    sections = Section.objects.all()
    templates = IDCardTemplate.objects.filter(is_active=True)
    
    context = {
        'classes': classes,
        'sections': sections,
        'templates': templates
    }
    
    return render(request, 'students/id_cards/generate_with_progress.html', context)


@login_required
@require_POST
def start_bulk_id_card_generation(request):
    """Start bulk ID card generation with progress tracking"""
    try:
        class_id = request.POST.get('class_id')
        section_id = request.POST.get('section_id')
        template_id = request.POST.get('template_id')
        
        # Get students to process
        students = Student.objects.all()
        if class_id:
            students = students.filter(current_class_id=class_id)
        if section_id:
            students = students.filter(section_id=section_id)
        
        total_students = students.count()
        
        if total_students == 0:
            return JsonResponse({
                'success': False,
                'message': 'No students found for the selected criteria.'
            })
        
        # Initialize progress tracking
        job_id = f"id_card_job_{int(time.time())}"
        cache.set(job_id, {
            'status': 'processing',
            'total': total_students,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'current_student': '',
            'start_time': timezone.now().isoformat(),
            'errors': []
        }, timeout=3600)  # 1 hour timeout
        
        # Start processing in background (for now, simulate)
        # In production, use Celery or similar
        import threading
        
        def process_id_cards():
            try:
                template = IDCardTemplate.objects.get(id=template_id)
                processed_count = 0
                success_count = 0
                failed_count = 0
                
                for student in students:
                    try:
                        # Update current progress
                        progress = cache.get(job_id)
                        if progress:
                            progress['processed'] = processed_count
                            progress['current_student'] = f"{student.first_name} {student.last_name}"
                            cache.set(job_id, progress, timeout=3600)
                        
                        # Generate ID card
                        from .id_card_generator import IDCardGenerator
                        generator = IDCardGenerator(student, template)
                        id_card = generator.save_card()
                        
                        if id_card:
                            success_count += 1
                        else:
                            failed_count += 1
                            
                    except Exception as e:
                        failed_count += 1
                        progress = cache.get(job_id)
                        if progress:
                            progress['errors'].append(f"{student.admission_number}: {str(e)}")
                            cache.set(job_id, progress, timeout=3600)
                    
                    processed_count += 1
                    
                    # Update progress
                    progress = cache.get(job_id)
                    if progress:
                        progress['processed'] = processed_count
                        progress['success'] = success_count
                        progress['failed'] = failed_count
                        progress['status'] = 'completed' if processed_count == total_students else 'processing'
                        cache.set(job_id, progress, timeout=3600)
                    
                    time.sleep(0.1)  # Simulate processing time
                
                # Final update
                final_progress = cache.get(job_id)
                if final_progress:
                    final_progress['status'] = 'completed'
                    final_progress['end_time'] = timezone.now().isoformat()
                    cache.set(job_id, final_progress, timeout=3600)
                    
            except Exception as e:
                progress = cache.get(job_id)
                if progress:
                    progress['status'] = 'failed'
                    progress['error'] = str(e)
                    cache.set(job_id, progress, timeout=3600)
        
        # Start processing thread
        thread = threading.Thread(target=process_id_cards)
        thread.daemon = True
        thread.start()
        
        return JsonResponse({
            'success': True,
            'job_id': job_id,
            'total_students': total_students,
            'message': 'ID card generation started successfully!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error starting ID card generation: {str(e)}'
        })


@login_required
def get_generation_progress(request, job_id):
    """Get real-time progress of ID card generation"""
    try:
        progress = cache.get(job_id)
        
        if not progress:
            return JsonResponse({
                'success': False,
                'message': 'Job not found or expired.'
            })
        
        # Calculate percentage
        percentage = 0
        if progress['total'] > 0:
            percentage = (progress['processed'] / progress['total']) * 100
        
        # Calculate estimated time remaining
        eta_seconds = 0
        if progress['status'] == 'processing' and progress['processed'] > 0:
            elapsed_time = (timezone.now() - timezone.datetime.fromisoformat(progress['start_time'])).total_seconds()
            avg_time_per_student = elapsed_time / progress['processed']
            remaining_students = progress['total'] - progress['processed']
            eta_seconds = avg_time_per_student * remaining_students
        
        return JsonResponse({
            'success': True,
            'progress': {
                'status': progress['status'],
                'total': progress['total'],
                'processed': progress['processed'],
                'success': progress['success'],
                'failed': progress['failed'],
                'percentage': round(percentage, 2),
                'current_student': progress['current_student'],
                'eta_seconds': round(eta_seconds),
                'errors': progress['errors'][-5:],  # Show last 5 errors
                'start_time': progress['start_time'],
                'end_time': progress.get('end_time')
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting progress: {str(e)}'
        })


@login_required
def id_card_generation_status(request):
    """Show ID card generation status dashboard"""
    return render(request, 'students/id_cards/generation_status.html')


@login_required
def list_generated_id_cards_with_status(request):
    """List generated ID cards with detailed status"""
    from .models import StudentIDCard
    
    cards = StudentIDCard.objects.select_related('student', 'template').order_by('-created_at')
    
    # Add status information
    card_data = []
    for card in cards:
        card_data.append({
            'id': card.id,
            'student_name': f"{card.student.first_name} {card.student.last_name}",
            'admission_number': card.student.admission_number,
            'class_name': card.student.current_class.name if card.student.current_class else 'N/A',
            'section_name': card.student.section.name if card.student.section else 'N/A',
            'template_name': card.template.name if card.template else 'Default',
            'created_at': card.created_at,
            'pdf_file': card.generated_image,
            'status': 'Generated' if card.generated_image else 'Processing',
            'download_url': card.generated_image.url if card.generated_image else None
        })
    
    context = {
        'cards': card_data,
        'total_cards': len(card_data),
        'generated_cards': len([c for c in card_data if c['status'] == 'Generated'])
    }
    
    return render(request, 'students/id_cards/list_with_status.html', context)
