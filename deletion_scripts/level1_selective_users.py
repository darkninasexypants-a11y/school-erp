#!/usr/bin/env python
"""
LEVEL 1: SELECTIVE USER DELETION
Delete specific users by email, username, or criteria
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
from students_app.models import SchoolUser, Student, Teacher, Staff, Parent

def delete_selective_users():
    print("=" * 80)
    print("🎯 LEVEL 1: SELECTIVE USER DELETION")
    print("=" * 80)
    print("\nChoose deletion method:")
    print("1. Delete by email addresses")
    print("2. Delete by usernames")
    print("3. Delete by user type (student/teacher/staff/parent)")
    print("4. Delete by date range")
    print("5. Delete inactive users")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == '1':
        delete_by_email()
    elif choice == '2':
        delete_by_username()
    elif choice == '3':
        delete_by_user_type()
    elif choice == '4':
        delete_by_date_range()
    elif choice == '5':
        delete_inactive_users()
    else:
        print("Invalid choice!")

def delete_by_email():
    print("\n--- Delete by Email Addresses ---")
    emails_input = input("Enter email addresses (comma-separated): ").strip()
    emails = [email.strip() for email in emails_input.split(',') if email.strip()]
    
    if not emails:
        print("No emails provided!")
        return
    
    print(f"\nUsers to delete: {len(emails)}")
    for email in emails:
        user = User.objects.filter(email=email).first()
        if user:
            print(f"  ✓ {email} - {user.get_full_name() or user.username}")
        else:
            print(f"  ❌ {email} - Not found")
    
    confirm = input(f"\nDelete these {len(emails)} users? (yes/no): ").strip().lower()
    if confirm == 'yes':
        with transaction.atomic():
            deleted_count = 0
            for email in emails:
                try:
                    user = User.objects.get(email=email)
                    if user.is_superuser:
                        print(f"  ⚠️  SKIPPED {email} - Superuser (protected)")
                        continue
                    username = user.username
                    user.delete()
                    deleted_count += 1
                    print(f"  ✅ DELETED {email} ({username})")
                except User.DoesNotExist:
                    print(f"  ❌ {email} - Not found")
            print(f"\n✅ Successfully deleted {deleted_count} users")

def delete_by_username():
    print("\n--- Delete by Usernames ---")
    usernames_input = input("Enter usernames (comma-separated): ").strip()
    usernames = [username.strip() for username in usernames_input.split(',') if username.strip()]
    
    if not usernames:
        print("No usernames provided!")
        return
    
    print(f"\nUsers to delete: {len(usernames)}")
    for username in usernames:
        user = User.objects.filter(username=username).first()
        if user:
            print(f"  ✓ {username} - {user.email}")
        else:
            print(f"  ❌ {username} - Not found")
    
    confirm = input(f"\nDelete these {len(usernames)} users? (yes/no): ").strip().lower()
    if confirm == 'yes':
        with transaction.atomic():
            deleted_count = 0
            for username in usernames:
                try:
                    user = User.objects.get(username=username)
                    if user.is_superuser:
                        print(f"  ⚠️  SKIPPED {username} - Superuser (protected)")
                        continue
                    email = user.email
                    user.delete()
                    deleted_count += 1
                    print(f"  ✅ DELETED {username} ({email})")
                except User.DoesNotExist:
                    print(f"  ❌ {username} - Not found")
            print(f"\n✅ Successfully deleted {deleted_count} users")

def delete_by_user_type():
    print("\n--- Delete by User Type ---")
    print("1. Students only")
    print("2. Teachers only")
    print("3. Staff only")
    print("4. Parents only")
    print("5. All non-superusers")
    
    type_choice = input("Choose user type (1-5): ").strip()
    
    type_map = {
        '1': ('Student', Student),
        '2': ('Teacher', Teacher),
        '3': ('Staff', Staff),
        '4': ('Parent', Parent),
        '5': ('All Non-Superusers', None)
    }
    
    if type_choice not in type_map:
        print("Invalid choice!")
        return
    
    type_name, model_class = type_map[type_choice]
    
    if type_choice == '5':
        users_to_delete = User.objects.filter(is_superuser=False)
    else:
        user_ids = model_class.objects.values_list('user_id', flat=True)
        users_to_delete = User.objects.filter(id__in=user_ids, is_superuser=False)
    
    count = users_to_delete.count()
    print(f"\n{type_name} to delete: {count}")
    
    if count > 0:
        print("Sample users:")
        for user in users_to_delete[:5]:
            print(f"  • {user.email} ({user.username})")
        if count > 5:
            print(f"  ... and {count - 5} more")
    
    confirm = input(f"\nDelete all {type_name.lower()}? (yes/no): ").strip().lower()
    if confirm == 'yes':
        with transaction.atomic():
            deleted_count = users_to_delete.count()
            users_to_delete.delete()
            print(f"✅ Successfully deleted {deleted_count} {type_name.lower()}")

def delete_by_date_range():
    print("\n--- Delete by Date Range ---")
    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
    end_date = input("Enter end date (YYYY-MM-DD): ").strip()
    
    try:
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        users_to_delete = User.objects.filter(
            date_joined__gte=start,
            date_joined__lte=end,
            is_superuser=False
        )
        
        count = users_to_delete.count()
        print(f"\nUsers to delete (created {start_date} to {end_date}): {count}")
        
        if count > 0:
            print("Sample users:")
            for user in users_to_delete[:5]:
                print(f"  • {user.email} - Joined: {user.date_joined.date()}")
            if count > 5:
                print(f"  ... and {count - 5} more")
        
        confirm = input(f"\nDelete these {count} users? (yes/no): ").strip().lower()
        if confirm == 'yes':
            with transaction.atomic():
                users_to_delete.delete()
                print(f"✅ Successfully deleted {count} users")
                
    except ValueError as e:
        print(f"Invalid date format: {e}")

def delete_inactive_users():
    print("\n--- Delete Inactive Users ---")
    print("1. Delete users with is_active=False")
    print("2. Delete users who haven't logged in for X days")
    
    inactive_choice = input("Choose option (1-2): ").strip()
    
    if inactive_choice == '1':
        users_to_delete = User.objects.filter(is_active=False, is_superuser=False)
        count = users_to_delete.count()
        print(f"\nInactive users to delete: {count}")
        
        if count > 0:
            confirm = input(f"Delete these {count} inactive users? (yes/no): ").strip().lower()
            if confirm == 'yes':
                with transaction.atomic():
                    users_to_delete.delete()
                    print(f"✅ Successfully deleted {count} inactive users")
    
    elif inactive_choice == '2':
        days = input("Delete users who haven't logged in for how many days? ").strip()
        try:
            days = int(days)
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=days)
            users_to_delete = User.objects.filter(
                last_login__lt=cutoff_date,
                is_superuser=False
            )
            
            count = users_to_delete.count()
            print(f"\nUsers to delete (haven't logged in for {days}+ days): {count}")
            
            if count > 0:
                confirm = input(f"Delete these {count} users? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    with transaction.atomic():
                        users_to_delete.delete()
                        print(f"✅ Successfully deleted {count} users")
        except ValueError:
            print("Invalid number of days!")

if __name__ == '__main__':
    delete_selective_users()
