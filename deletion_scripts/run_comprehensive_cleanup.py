#!/usr/bin/env python
"""
Auto-run comprehensive cleanup for trial data
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
from students_app.models import *

def auto_comprehensive_cleanup():
    print("=" * 80)
    print("🧹 AUTO COMPREHENSIVE TRIAL DATA CLEANUP")
    print("=" * 80)
    
    # Clean up test pattern users
    print("\n1. Cleaning test pattern users...")
    trial_indicators = ['test', 'demo', 'sample', 'temp', 'dummy', 'example']
    
    test_users = User.objects.none()
    for pattern in trial_indicators:
        pattern_users = User.objects.filter(
            models.Q(username__icontains=pattern) |
            models.Q(email__icontains=pattern) |
            models.Q(first_name__icontains=pattern) |
            models.Q(last_name__icontains=pattern),
            is_superuser=False
        )
        test_users = test_users | pattern_users
    
    test_users = test_users.distinct()
    print(f"Found {test_users.count()} test pattern users")
    
    if test_users.exists():
        # Get related SchoolUser profiles
        schooluser_ids = SchoolUser.objects.filter(
            user_id__in=test_users.values('id')
        ).values_list('id', flat=True)
        
        with transaction.atomic():
            SchoolUser.objects.filter(id__in=schooluser_ids).delete()
            deleted_count = test_users.count()
            test_users.delete()
            print(f"✅ Deleted {deleted_count} test pattern users")
    
    # Clean up duplicate emails
    print("\n2. Cleaning duplicate emails...")
    duplicate_emails = User.objects.values('email').annotate(
        count=models.Count('email')
    ).filter(count__gt=1).exclude(email='')
    
    total_duplicates_deleted = 0
    for dup in duplicate_emails:
        email = dup['email']
        if not email:  # Skip empty emails
            continue
            
        users_with_email = User.objects.filter(email=email).order_by('id')
        users_to_delete = users_with_email[1:]  # Keep first, delete rest
        
        if users_to_delete.exists():
            # Get SchoolUser profiles
            schooluser_ids = SchoolUser.objects.filter(
                user_id__in=users_to_delete.values('id')
            ).values_list('id', flat=True)
            
            with transaction.atomic():
                SchoolUser.objects.filter(id__in=schooluser_ids).delete()
                deleted_count = users_to_delete.count()
                users_to_delete.delete()
                total_duplicates_deleted += deleted_count
                print(f"✅ Deleted {deleted_count} duplicates for email: {email}")
    
    # Clean up empty emails
    print("\n3. Cleaning empty emails...")
    empty_email_users = User.objects.filter(
        models.Q(email='') | models.Q(email__isnull=True),
        is_superuser=False
    )
    
    if empty_email_users.exists():
        schooluser_ids = SchoolUser.objects.filter(
            user_id__in=empty_email_users.values('id')
        ).values_list('id', flat=True)
        
        with transaction.atomic():
            SchoolUser.objects.filter(id__in=schooluser_ids).delete()
            deleted_count = empty_email_users.count()
            empty_email_users.delete()
            print(f"✅ Deleted {deleted_count} users with empty emails")
    
    # Clean up orphaned records
    print("\n4. Cleaning orphaned records...")
    
    # Students without users
    students_without_users = Student.objects.filter(user__isnull=True)
    if students_without_users.exists():
        count = students_without_users.count()
        students_without_users.delete()
        print(f"✅ Deleted {count} students without users")
    
    # Teachers without users
    teachers_without_users = Teacher.objects.filter(user__isnull=True)
    if teachers_without_users.exists():
        count = teachers_without_users.count()
        teachers_without_users.delete()
        print(f"✅ Deleted {count} teachers without users")
    
    # SchoolUsers without users
    schoolusers_without_users = SchoolUser.objects.filter(user__isnull=True)
    if schoolusers_without_users.exists():
        count = schoolusers_without_users.count()
        schoolusers_without_users.delete()
        print(f"✅ Deleted {count} SchoolUsers without users")
    
    # SchoolUsers without schools
    schoolusers_without_schools = SchoolUser.objects.filter(school__isnull=True)
    if schoolusers_without_schools.exists():
        count = schoolusers_without_schools.count()
        schoolusers_without_schools.delete()
        print(f"✅ Deleted {count} SchoolUsers without schools")
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE CLEANUP COMPLETE")
    print("=" * 80)
    
    # Show final counts
    print(f"\nFinal database state:")
    print(f"Total Users: {User.objects.count()}")
    print(f"Superusers: {User.objects.filter(is_superuser=True).count()}")
    print(f"Regular Users: {User.objects.filter(is_superuser=False).count()}")
    print(f"SchoolUser profiles: {SchoolUser.objects.count()}")
    print(f"Students: {Student.objects.count()}")
    print(f"Teachers: {Teacher.objects.count()}")
    
    print(f"\n🎉 Trial data cleanup completed successfully!")

if __name__ == '__main__':
    auto_comprehensive_cleanup()
