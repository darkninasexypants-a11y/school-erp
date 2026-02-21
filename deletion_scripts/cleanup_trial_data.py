#!/usr/bin/env python
"""
CLEANUP TRIAL DATA
Identify and remove any leftover data from previous trials/tests
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
from django.utils import timezone
from datetime import timedelta

def cleanup_trial_data():
    print("=" * 80)
    print("🧹 CLEANUP TRIAL DATA - Remove Leftover Test Data")
    print("=" * 80)
    
    print("\nScanning for potential trial/test data...")
    
    # Check for common test patterns
    trial_indicators = [
        'test', 'demo', 'sample', 'trial', 'temp', 'dummy',
        'example', 'mock', 'fake', 'placeholder', 'xyz',
        'abc', '123', 'testuser', 'demouser', 'sampleuser'
    ]
    
    cleanup_options = {
        '1': ('Users with test patterns', cleanup_test_users),
        '2': ('Users with generic emails', cleanup_generic_emails),
        '3': ('Empty/Incomplete records', cleanup_incomplete_records),
        '4': ('Duplicate records', cleanup_duplicates),
        '5': ('Orphaned records', cleanup_orphaned_records),
        '6': ('Very recent test data', cleanup_recent_test_data),
        '7': ('All trial data (comprehensive)', comprehensive_cleanup),
        '8': ('Show current data analysis', show_data_analysis)
    }
    
    print("\nCleanup options:")
    for key, (desc, _) in cleanup_options.items():
        print(f"{key}. {desc}")
    
    choice = input(f"\nSelect cleanup option (1-8): ").strip()
    
    if choice in cleanup_options:
        desc, func = cleanup_options[choice]
        print(f"\n--- {desc} ---")
        func(trial_indicators)
    else:
        print("Invalid choice!")

def cleanup_test_users(trial_indicators):
    """Clean up users with test patterns"""
    print("\n🔍 Checking for users with test patterns...")
    
    test_users = User.objects.none()
    for pattern in trial_indicators:
        pattern_users = User.objects.filter(
            models.Q(username__icontains=pattern) |
            models.Q(email__icontains=pattern) |
            models.Q(first_name__icontains=pattern) |
            models.Q(last_name__icontains=pattern)
        )
        test_users = test_users | pattern_users
    
    # Exclude superusers
    test_users = test_users.filter(is_superuser=False).distinct()
    
    print(f"Found {test_users.count()} users with test patterns:")
    
    if test_users.exists():
        for user in test_users[:10]:
            print(f"  • {user.username} ({user.email})")
        if test_users.count() > 10:
            print(f"  ... and {test_users.count() - 10} more")
        
        confirm = input(f"\nDelete {test_users.count()} test users? (yes/no): ").strip().lower()
        if confirm == 'yes':
            with transaction.atomic():
                # Get related SchoolUser profiles
                schooluser_ids = SchoolUser.objects.filter(
                    user_id__in=test_users.values('id')
                ).values_list('id', flat=True)
                
                # Delete SchoolUser profiles first
                SchoolUser.objects.filter(id__in=schooluser_ids).delete()
                
                # Delete users
                deleted_count = test_users.count()
                test_users.delete()
                
                print(f"✅ Deleted {deleted_count} test users and their profiles")
    else:
        print("No test pattern users found!")

def cleanup_generic_emails(trial_indicators):
    """Clean up users with generic/test emails"""
    print("\n🔍 Checking for generic/test emails...")
    
    generic_patterns = [
        'test@', 'demo@', 'sample@', 'temp@', 'dummy@',
        'example@', 'test.com', 'example.com', 'sample.com',
        '@test.', '@demo.', '@sample.', '@temp.'
    ]
    
    generic_users = User.objects.none()
    for pattern in generic_patterns:
        pattern_users = User.objects.filter(email__icontains=pattern)
        generic_users = generic_users | pattern_users
    
    generic_users = generic_users.filter(is_superuser=False).distinct()
    
    print(f"Found {generic_users.count()} users with generic emails:")
    
    if generic_users.exists():
        for user in generic_users[:10]:
            print(f"  • {user.username} ({user.email})")
        if generic_users.count() > 10:
            print(f"  ... and {generic_users.count() - 10} more")
        
        confirm = input(f"\nDelete {generic_users.count()} users with generic emails? (yes/no): ").strip().lower()
        if confirm == 'yes':
            with transaction.atomic():
                schooluser_ids = SchoolUser.objects.filter(
                    user_id__in=generic_users.values('id')
                ).values_list('id', flat=True)
                
                SchoolUser.objects.filter(id__in=schooluser_ids).delete()
                
                deleted_count = generic_users.count()
                generic_users.delete()
                
                print(f"✅ Deleted {deleted_count} users with generic emails")
    else:
        print("No generic email users found!")

def cleanup_incomplete_records(trial_indicators):
    """Clean up incomplete records"""
    print("\n🔍 Checking for incomplete records...")
    
    incomplete_counts = {}
    
    # Check students with missing data
    incomplete_students = Student.objects.filter(
        models.Q(first_name='') | models.Q(first_name__isnull=True) |
        models.Q(email='') | models.Q(email__isnull=True) |
        models.Q(user__isnull=True)
    )
    incomplete_counts['Students with missing data'] = incomplete_students.count()
    
    # Check teachers with missing data
    incomplete_teachers = Teacher.objects.filter(
        models.Q(first_name='') | models.Q(first_name__isnull=True) |
        models.Q(employee_id='') | models.Q(employee_id__isnull=True) |
        models.Q(user__isnull=True)
    )
    incomplete_counts['Teachers with missing data'] = incomplete_teachers.count()
    
    # Check SchoolUser without proper user
    orphaned_schoolusers = SchoolUser.objects.filter(user__isnull=True)
    incomplete_counts['Orphaned SchoolUser profiles'] = orphaned_schoolusers.count()
    
    total_incomplete = sum(incomplete_counts.values())
    print(f"Found {total_incomplete} incomplete records:")
    
    for category, count in incomplete_counts.items():
        if count > 0:
            print(f"  • {category}: {count}")
    
    if total_incomplete > 0:
        confirm = input(f"\nDelete {total_incomplete} incomplete records? (yes/no): ").strip().lower()
        if confirm == 'yes':
            with transaction.atomic():
                deleted_count = 0
                
                if incomplete_students.exists():
                    count = incomplete_students.count()
                    incomplete_students.delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} incomplete students")
                
                if incomplete_teachers.exists():
                    count = incomplete_teachers.count()
                    incomplete_teachers.delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} incomplete teachers")
                
                if orphaned_schoolusers.exists():
                    count = orphaned_schoolusers.count()
                    orphaned_schoolusers.delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} orphaned SchoolUser profiles")
                
                print(f"✅ Total incomplete records deleted: {deleted_count}")
    else:
        print("No incomplete records found!")

def cleanup_duplicates(trial_indicators):
    """Clean up duplicate records"""
    print("\n🔍 Checking for duplicate records...")
    
    duplicate_counts = {}
    
    # Check duplicate emails
    duplicate_emails = User.objects.values('email').annotate(
        count=models.Count('email')
    ).filter(count__gt=1)
    duplicate_counts['Duplicate emails'] = duplicate_emails.count()
    
    # Check duplicate usernames
    duplicate_usernames = User.objects.values('username').annotate(
        count=models.Count('username')
    ).filter(count__gt=1)
    duplicate_counts['Duplicate usernames'] = duplicate_usernames.count()
    
    # Check duplicate employee IDs
    try:
        duplicate_employee_ids = Teacher.objects.values('employee_id').annotate(
            count=models.Count('employee_id')
        ).filter(count__gt=1).exclude(employee_id='')
        duplicate_counts['Duplicate employee IDs'] = duplicate_employee_ids.count()
    except:
        duplicate_counts['Duplicate employee IDs'] = 0
    
    total_duplicates = sum(duplicate_counts.values())
    print(f"Found {total_duplicates} duplicate patterns:")
    
    for category, count in duplicate_counts.items():
        if count > 0:
            print(f"  • {category}: {count}")
    
    if total_duplicates > 0:
        print("\nDuplicate details:")
        
        # Show duplicate emails
        if duplicate_emails.exists():
            print("  Duplicate emails:")
            for dup in duplicate_emails[:5]:
                users_with_email = User.objects.filter(email=dup['email'])
                print(f"    - {dup['email']}: {users_with_email.count()} users")
        
        # Show duplicate usernames
        if duplicate_usernames.exists():
            print("  Duplicate usernames:")
            for dup in duplicate_usernames[:5]:
                users_with_username = User.objects.filter(username=dup['username'])
                print(f"    - {dup['username']}: {users_with_username.count()} users")
        
        confirm = input(f"\nProceed with duplicate cleanup? (yes/no): ").strip().lower()
        if confirm == 'yes':
            print("Manual cleanup required for duplicates.")
            print("Please review duplicates above and clean up manually.")
    else:
        print("No duplicates found!")

def cleanup_orphaned_records(trial_indicators):
    """Clean up orphaned records"""
    print("\n🔍 Checking for orphaned records...")
    
    orphan_counts = {}
    
    # Students without users
    students_without_users = Student.objects.filter(user__isnull=True)
    orphan_counts['Students without users'] = students_without_users.count()
    
    # Teachers without users
    teachers_without_users = Teacher.objects.filter(user__isnull=True)
    orphan_counts['Teachers without users'] = teachers_without_users.count()
    
    # SchoolUsers without users
    schoolusers_without_users = SchoolUser.objects.filter(user__isnull=True)
    orphan_counts['SchoolUsers without users'] = schoolusers_without_users.count()
    
    # SchoolUsers without schools
    schoolusers_without_schools = SchoolUser.objects.filter(school__isnull=True)
    orphan_counts['SchoolUsers without schools'] = schoolusers_without_schools.count()
    
    total_orphans = sum(orphan_counts.values())
    print(f"Found {total_orphans} orphaned records:")
    
    for category, count in orphan_counts.items():
        if count > 0:
            print(f"  • {category}: {count}")
    
    if total_orphans > 0:
        confirm = input(f"\nDelete {total_orphans} orphaned records? (yes/no): ").strip().lower()
        if confirm == 'yes':
            with transaction.atomic():
                deleted_count = 0
                
                if students_without_users.exists():
                    count = students_without_users.count()
                    students_without_users.delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} students without users")
                
                if teachers_without_users.exists():
                    count = teachers_without_users.count()
                    teachers_without_users.delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} teachers without users")
                
                if schoolusers_without_users.exists():
                    count = schoolusers_without_users.count()
                    schoolusers_without_users.delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} SchoolUsers without users")
                
                if schoolusers_without_schools.exists():
                    count = schoolusers_without_schools.count()
                    schoolusers_without_schools.delete()
                    deleted_count += count
                    print(f"  ✅ Deleted {count} SchoolUsers without schools")
                
                print(f"✅ Total orphaned records deleted: {deleted_count}")
    else:
        print("No orphaned records found!")

def cleanup_recent_test_data(trial_indicators):
    """Clean up very recent test data"""
    print("\n🔍 Checking for recent test data...")
    
    # Check users created in last 24 hours
    yesterday = timezone.now() - timedelta(days=1)
    recent_users = User.objects.filter(
        date_joined__gte=yesterday,
        is_superuser=False
    )
    
    print(f"Found {recent_users.count()} users created in last 24 hours:")
    
    if recent_users.exists():
        for user in recent_users:
            print(f"  • {user.username} ({user.email}) - Joined: {user.date_joined}")
        
        confirm = input(f"\nDelete {recent_users.count()} recent test users? (yes/no): ").strip().lower()
        if confirm == 'yes':
            with transaction.atomic():
                schooluser_ids = SchoolUser.objects.filter(
                    user_id__in=recent_users.values('id')
                ).values_list('id', flat=True)
                
                SchoolUser.objects.filter(id__in=schooluser_ids).delete()
                
                deleted_count = recent_users.count()
                recent_users.delete()
                
                print(f"✅ Deleted {deleted_count} recent test users")
    else:
        print("No recent test users found!")

def comprehensive_cleanup(trial_indicators):
    """Comprehensive cleanup of all trial data"""
    print("\n🧹 COMPREHENSIVE TRIAL DATA CLEANUP")
    print("This will run ALL cleanup operations...")
    
    confirm = input("Run comprehensive cleanup? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Comprehensive cleanup cancelled.")
        return
    
    print("\nRunning comprehensive cleanup...")
    
    cleanup_operations = [
        ("Test pattern users", lambda: cleanup_test_users(trial_indicators)),
        ("Generic email users", lambda: cleanup_generic_emails(trial_indicators)),
        ("Incomplete records", lambda: cleanup_incomplete_records(trial_indicators)),
        ("Orphaned records", lambda: cleanup_orphaned_records(trial_indicators)),
        ("Recent test data", lambda: cleanup_recent_test_data(trial_indicators))
    ]
    
    for name, func in cleanup_operations:
        print(f"\n{'='*60}")
        print(f"Cleaning: {name}")
        print('='*60)
        func(trial_indicators)
    
    print(f"\n{'='*60}")
    print("✅ COMPREHENSIVE CLEANUP COMPLETE")
    print('='*60)

def show_data_analysis(trial_indicators):
    """Show detailed analysis of current data"""
    print("\n📊 CURRENT DATA ANALYSIS")
    print("=" * 50)
    
    # User analysis
    total_users = User.objects.count()
    superusers = User.objects.filter(is_superuser=True).count()
    regular_users = total_users - superusers
    
    print(f"👥 USERS:")
    print(f"  Total: {total_users}")
    print(f"  Superusers: {superusers}")
    print(f"  Regular: {regular_users}")
    
    # School analysis
    schools = School.objects.all()
    print(f"\n🏫 SCHOOLS: {schools.count()}")
    for school in schools:
        user_count = SchoolUser.objects.filter(school=school).count()
        print(f"  • {school.name}: {user_count} users")
    
    # Student/Teacher analysis
    students = Student.objects.count()
    teachers = Teacher.objects.count()
    print(f"\n📚 ACADEMIC:")
    print(f"  Students: {students}")
    print(f"  Teachers: {teachers}")
    
    # Test pattern analysis
    print(f"\n🔍 TEST PATTERN ANALYSIS:")
    test_patterns = ['test', 'demo', 'sample', 'temp', 'example']
    
    for pattern in test_patterns:
        pattern_users = User.objects.filter(
            models.Q(username__icontains=pattern) |
            models.Q(email__icontains=pattern),
            is_superuser=False
        ).count()
        if pattern_users > 0:
            print(f"  • '{pattern}' pattern: {pattern_users} users")
    
    # Email domain analysis
    print(f"\n📧 EMAIL DOMAIN ANALYSIS:")
    email_domains = User.objects.filter(
        is_superuser=False
    ).values_list('email', flat=True)
    
    domain_counts = {}
    for email in email_domains:
        if email and '@' in email:
            domain = email.split('@')[1]
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • @{domain}: {count} users")
    
    # Recent activity
    last_week = timezone.now() - timedelta(days=7)
    recent_users = User.objects.filter(
        date_joined__gte=last_week,
        is_superuser=False
    ).count()
    print(f"\n📅 RECENT ACTIVITY:")
    print(f"  Users created last 7 days: {recent_users}")
    
    print(f"\n{'='*50}")
    print("ANALYSIS COMPLETE")
    print('='*50)

if __name__ == '__main__':
    cleanup_trial_data()
