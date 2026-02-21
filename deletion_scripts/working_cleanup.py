#!/usr/bin/env python
"""
WORKING CLEANUP - Remove leftover trial data (fixed version)
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

def working_cleanup():
    print("=" * 80)
    print("🧹 WORKING TRIAL DATA CLEANUP")
    print("=" * 80)
    
    total_deleted = 0
    
    # 1. Clean up test pattern users
    print("\n1. Cleaning test pattern users...")
    test_patterns = ['test', 'demo', 'sample', 'temp', 'dummy', 'example']
    
    for pattern in test_patterns:
        test_users = User.objects.filter(
            models.Q(username__icontains=pattern) |
            models.Q(email__icontains=pattern),
            is_superuser=False
        )
        
        if test_users.exists():
            count = test_users.count()
            print(f"  Found {count} users with '{pattern}' pattern")
            
            # Get SchoolUser IDs first (avoid complex subqueries)
            user_ids = []
            for user in test_users:
                user_ids.append(user.id)
            
            schooluser_ids = []
            for uid in user_ids:
                try:
                    su = SchoolUser.objects.filter(user_id=uid).first()
                    if su:
                        schooluser_ids.append(su.id)
                except:
                    pass
            
            # Delete SchoolUser profiles first
            if schooluser_ids:
                SchoolUser.objects.filter(id__in=schooluser_ids).delete()
                print(f"    Deleted {len(schooluser_ids)} SchoolUser profiles")
            
            # Then delete users
            test_users.delete()
            print(f"    Deleted {count} users")
            total_deleted += count
    
    # 2. Clean up empty emails
    print("\n2. Cleaning empty emails...")
    empty_email_users = User.objects.filter(
        models.Q(email='') | models.Q(email__isnull=True),
        is_superuser=False
    )
    
    if empty_email_users.exists():
        count = empty_email_users.count()
        print(f"  Found {count} users with empty emails")
        
        user_ids = [u.id for u in empty_email_users]
        schooluser_ids = []
        for uid in user_ids:
            try:
                su = SchoolUser.objects.filter(user_id=uid).first()
                if su:
                    schooluser_ids.append(su.id)
            except:
                pass
        
        if schooluser_ids:
            SchoolUser.objects.filter(id__in=schooluser_ids).delete()
            print(f"    Deleted {len(schooluser_ids)} SchoolUser profiles")
        
        empty_email_users.delete()
        print(f"    Deleted {count} users")
        total_deleted += count
    
    # 3. Clean up example.com emails
    print("\n3. Cleaning example.com emails...")
    example_users = User.objects.filter(
        email__endswith='@example.com',
        is_superuser=False
    )
    
    if example_users.exists():
        count = example_users.count()
        print(f"  Found {count} users with @example.com emails")
        
        user_ids = [u.id for u in example_users]
        schooluser_ids = []
        for uid in user_ids:
            try:
                su = SchoolUser.objects.filter(user_id=uid).first()
                if su:
                    schooluser_ids.append(su.id)
            except:
                pass
        
        if schooluser_ids:
            SchoolUser.objects.filter(id__in=schooluser_ids).delete()
            print(f"    Deleted {len(schooluser_ids)} SchoolUser profiles")
        
        example_users.delete()
        print(f"    Deleted {count} users")
        total_deleted += count
    
    # 4. Manual duplicate cleanup
    print("\n4. Cleaning known duplicates...")
    
    # Handle sita.verma@school.com duplicates
    sita_users = User.objects.filter(
        email='sita.verma@school.com',
        is_superuser=False
    ).order_by('id')
    
    if sita_users.count() > 1:
        # Keep first, delete rest
        duplicate_sita = sita_users[1:]
        count = duplicate_sita.count()
        print(f"  Found {count} duplicate sita.verma@school.com users")
        
        user_ids = [u.id for u in duplicate_sita]
        schooluser_ids = []
        for uid in user_ids:
            try:
                su = SchoolUser.objects.filter(user_id=uid).first()
                if su:
                    schooluser_ids.append(su.id)
            except:
                pass
        
        if schooluser_ids:
            SchoolUser.objects.filter(id__in=schooluser_ids).delete()
            print(f"    Deleted {len(schooluser_ids)} SchoolUser profiles")
        
        duplicate_sita.delete()
        print(f"    Deleted {count} duplicate users")
        total_deleted += count
    
    # Handle 1913pandey@gmail.com duplicates
    pandey_users = User.objects.filter(
        email='1913pandey@gmail.com',
        is_superuser=False
    ).order_by('id')
    
    if pandey_users.count() > 1:
        # Keep first, delete rest
        duplicate_pandey = pandey_users[1:]
        count = duplicate_pandey.count()
        print(f"  Found {count} duplicate 1913pandey@gmail.com users")
        
        user_ids = [u.id for u in duplicate_pandey]
        schooluser_ids = []
        for uid in user_ids:
            try:
                su = SchoolUser.objects.filter(user_id=uid).first()
                if su:
                    schooluser_ids.append(su.id)
            except:
                pass
        
        if schooluser_ids:
            SchoolUser.objects.filter(id__in=schooluser_ids).delete()
            print(f"    Deleted {len(schooluser_ids)} SchoolUser profiles")
        
        duplicate_pandey.delete()
        print(f"    Deleted {count} duplicate users")
        total_deleted += count
    
    # 5. Clean up any remaining obvious test data
    print("\n5. Cleaning remaining obvious test data...")
    
    # Users with numeric usernames (likely auto-generated test data)
    numeric_users = User.objects.filter(
        username__regex=r'^\d+$',
        is_superuser=False
    )
    
    if numeric_users.exists():
        count = numeric_users.count()
        print(f"  Found {count} users with numeric usernames")
        
        user_ids = [u.id for u in numeric_users]
        schooluser_ids = []
        for uid in user_ids:
            try:
                su = SchoolUser.objects.filter(user_id=uid).first()
                if su:
                    schooluser_ids.append(su.id)
            except:
                pass
        
        if schooluser_ids:
            SchoolUser.objects.filter(id__in=schooluser_ids).delete()
            print(f"    Deleted {len(schooluser_ids)} SchoolUser profiles")
        
        numeric_users.delete()
        print(f"    Deleted {count} numeric username users")
        total_deleted += count
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)
    print(f"Total users deleted: {total_deleted}")
    
    # Show final state
    print(f"\nFinal database state:")
    print(f"Total Users: {User.objects.count()}")
    print(f"Superusers: {User.objects.filter(is_superuser=True).count()}")
    print(f"Regular Users: {User.objects.filter(is_superuser=False).count()}")
    print(f"SchoolUser profiles: {SchoolUser.objects.count()}")
    
    # Check if any obvious test data remains
    remaining_test = User.objects.filter(
        models.Q(username__icontains='test') |
        models.Q(email__icontains='test') |
        models.Q(email__endswith='@example.com'),
        is_superuser=False
    ).count()
    
    if remaining_test > 0:
        print(f"\n⚠️  Still {remaining_test} potential test users remain")
        print("You may need to clean these manually")
    else:
        print(f"\n🎉 All obvious trial data cleaned successfully!")

if __name__ == '__main__':
    working_cleanup()
