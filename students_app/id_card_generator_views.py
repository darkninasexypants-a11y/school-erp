from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone
from .models import IDCardGenerator, IDCardData
from .id_card_generator_forms import IDCardGeneratorForm, IDCardDataForm
import json

@login_required
def id_card_generator_dashboard(request):
    """ID Card Generator Dashboard for Super User"""
    # Check if user is superuser
    if not request.user.is_superuser:
        messages.error(request, 'Only Super User can access this page.')
        return redirect('students_app:simple_login')
    
    generators = IDCardGenerator.objects.all().order_by('-created_at')
    recent_cards = IDCardData.objects.all().order_by('-created_at')[:10]
    
    context = {
        'generators': generators,
        'recent_cards': recent_cards,
        'total_generators': generators.count(),
        'total_cards': IDCardData.objects.count(),
        'generated_cards': IDCardData.objects.filter(is_generated=True).count(),
    }
    return render(request, 'id_card_generator/dashboard.html', context)

@login_required
def create_id_card_generator(request):
    """Create new ID Card Generator"""
    if not request.user.is_superuser:
        messages.error(request, 'Only Super User can access this page.')
        return redirect('students_app:simple_login')
    
    if request.method == 'POST':
        form = IDCardGeneratorForm(request.POST)
        if form.is_valid():
            generator = form.save()
            messages.success(request, f'ID Card Generator "{generator}" created successfully!')
            return redirect('students_app:id_card_generator_dashboard')
    else:
        form = IDCardGeneratorForm()
    
    context = {'form': form}
    return render(request, 'id_card_generator/create_generator.html', context)

@login_required
def edit_id_card_generator(request, generator_id):
    """Edit ID Card Generator"""
    if not request.user.is_superuser:
        messages.error(request, 'Only Super User can access this page.')
        return redirect('students_app:simple_login')
    
    generator = get_object_or_404(IDCardGenerator, id=generator_id)
    
    if request.method == 'POST':
        form = IDCardGeneratorForm(request.POST, instance=generator)
        if form.is_valid():
            form.save()
            messages.success(request, f'ID Card Generator "{generator}" updated successfully!')
            return redirect('students_app:id_card_generator_dashboard')
    else:
        form = IDCardGeneratorForm(instance=generator)
    
    context = {'form': form, 'generator': generator}
    return render(request, 'id_card_generator/edit_generator.html', context)

@login_required
def id_card_data_entry(request, generator_id):
    """ID Card Data Entry Form"""
    if not request.user.is_superuser:
        messages.error(request, 'Only Super User can access this page.')
        return redirect('students_app:simple_login')
    
    generator = get_object_or_404(IDCardGenerator, id=generator_id)
    card_data = IDCardData.objects.filter(generator=generator).order_by('-created_at')
    
    if request.method == 'POST':
        form = IDCardDataForm(request.POST, request.FILES)
        if form.is_valid():
            card = form.save(commit=False)
            card.generator = generator
            card.save()
            messages.success(request, f'ID Card data for "{card.name}" added successfully!')
            return redirect('students_app:id_card_data_entry', generator_id=generator_id)
    else:
        form = IDCardDataForm()
    
    context = {
        'generator': generator,
        'form': form,
        'card_data': card_data,
    }
    return render(request, 'id_card_generator/data_entry.html', context)

@login_required
def edit_id_card_data(request, card_id):
    """Edit ID Card Data"""
    if not request.user.is_superuser:
        messages.error(request, 'Only Super User can access this page.')
        return redirect('students_app:simple_login')
    
    card = get_object_or_404(IDCardData, id=card_id)
    
    if request.method == 'POST':
        form = IDCardDataForm(request.POST, request.FILES, instance=card)
        if form.is_valid():
            form.save()
            messages.success(request, f'ID Card data for "{card.name}" updated successfully!')
            return redirect('students_app:id_card_data_entry', generator_id=card.generator.id)
    else:
        form = IDCardDataForm(instance=card)
    
    context = {'form': form, 'card': card}
    return render(request, 'id_card_generator/edit_card_data.html', context)

@login_required
def generate_id_cards_pdf(request, generator_id):
    """Generate ID Cards PDF"""
    if not request.user.is_superuser:
        messages.error(request, 'Only Super User can access this page.')
        return redirect('students_app:simple_login')
    
    generator = get_object_or_404(IDCardGenerator, id=generator_id)
    card_data = IDCardData.objects.filter(generator=generator, is_generated=False)
    
    if not card_data.exists():
        messages.warning(request, 'No cards to generate. Please add card data first.')
        return redirect('students_app:id_card_data_entry', generator_id=generator_id)
    
    # Import PDF generation functions
    from .views import generate_id_cards_reportlab
    
    try:
        # Convert IDCardData to Student-like objects for PDF generation
        students_data = []
        for card in card_data:
            # Create a mock student object with required attributes
            class MockStudent:
                def __init__(self, card_data):
                    self.admission_number = card_data.admission_no
                    self.first_name = card_data.name.split()[0] if card_data.name.split() else card_data.name
                    self.last_name = ' '.join(card_data.name.split()[1:]) if len(card_data.name.split()) > 1 else ''
                    self.father_name = card_data.father_name
                    self.father_phone = card_data.mobile
                    self.date_of_birth = card_data.date_of_birth
                    self.photo = card_data.photo
                    self.current_class = type('obj', (object,), {'name': card_data.class_name})()
                    self.section = type('obj', (object,), {'name': card_data.section})()
                
                def get_full_name(self):
                    return f"{self.first_name} {self.last_name}".strip()
            
            students_data.append(MockStudent(card))
        
        # Generate PDF
        response = generate_id_cards_reportlab(students_data, request, single_card=(generator.card_type == 'single'))
        
        # Mark cards as generated
        with transaction.atomic():
            for card in card_data:
                card.is_generated = True
                card.generated_at = timezone.now()
                card.save()
        
        messages.success(request, f'Successfully generated {len(card_data)} ID cards!')
        return response
        
    except Exception as e:
        messages.error(request, f'Error generating ID cards: {str(e)}')
        return redirect('students_app:id_card_data_entry', generator_id=generator_id)

@login_required
def calculator(request):
    """Calculator for Super User"""
    if not request.user.is_superuser:
        messages.error(request, 'Only Super User can access this page.')
        return redirect('students_app:simple_login')
    
    return render(request, 'id_card_generator/calculator.html')

@login_required
@csrf_exempt
def calculator_calculate(request):
    """Calculator API endpoint"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            expression = data.get('expression', '')
            
            # Simple calculator - only allow safe operations
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                return JsonResponse({'error': 'Invalid characters'}, status=400)
            
            # Evaluate expression safely
            result = eval(expression)
            return JsonResponse({'result': result})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
