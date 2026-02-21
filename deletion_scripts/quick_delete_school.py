#!/usr/bin/env python
"""
QUICK DELETE EXISTING SCHOOL
Simple script to delete Army Asha School
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from students_app.models import School, SchoolUser, Student, Teacher

def quick_delete_school():
    print("=" * 80)
    print("🏫 QUICK DELETE ARMY ASHA SCHOOL")
    print("=" * 80)
    
    # Find the school
    school = School.objects.filter(name__icontains='army asha').first()
    if not school:
        print("❌ Army Asha School not found!")
        return
    
    print(f"\nFound school: {school.name} (ID: {school.id})")
    
    # Get data summary
    students = Student.objects.filter(school=school)
    teachers = Teacher.objects.filter(school=school)
    
    print(f"\nData to delete:")
    print(f"• Students: {students.count()}")
    print(f"• Teachers: {teachers.count()}")
    print(f"• School record: 1")
    
    total = students.count() + teachers.count() + 1
    print(f"\nTotal records: {total}")
    
    # Confirm
    confirm = input(f"\nDelete '{school.name}' and all its data? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("❌ Operation cancelled.")
        return
    
    try:
        with transaction.atomic():
            print("\n🔄 Deleting...")
            
            # Delete students first
            if students.exists():
                count = students.count()
                students.delete()
                print(f"  ✅ Deleted {count} students")
            
            # Delete teachers
            if teachers.exists():
                count = teachers.count()
                teachers.delete()
                print(f"  ✅ Deleted {count} teachers")
            
            # Delete school
            school.delete()
            print(f"  ✅ Deleted school: {school.name}")
            
            print(f"\n✅ School deletion complete!")
            
            # Show remaining state
            remaining_schools = School.objects.all()
            if remaining_schools.exists():
                print(f"\n📚 Remaining schools: {remaining_schools.count()}")
                for s in remaining_schools:
                    print(f"  • {s.name}")
            else:
                print(f"\n📭 No schools remaining!")
                print("You can now create new schools.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    quick_delete_school()
