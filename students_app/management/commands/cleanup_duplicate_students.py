"""
Management command to clean up duplicate students in the database
Usage: python manage.py cleanup_duplicate_students
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from students_app.models import Student, Class, Section
from django.db import transaction


class Command(BaseCommand):
    help = 'Clean up duplicate students and fix database issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--fix-classes',
            action='store_true',
            help='Fix duplicate classes with same name',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        fix_classes = options['fix_classes']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Step 1: Find and fix duplicate classes
        if fix_classes:
            self.stdout.write(self.style.SUCCESS('\n=== Fixing Duplicate Classes ==='))
            duplicate_classes = Class.objects.values('name').annotate(
                count=Count('id')
            ).filter(count__gt=1)

            for dup in duplicate_classes:
                classes = Class.objects.filter(name=dup['name']).order_by('id')
                self.stdout.write(f"Found {dup['count']} classes with name '{dup['name']}'")
                
                if not dry_run:
                    # Keep the first one, merge others
                    main_class = classes.first()
                    for dup_class in classes[1:]:
                        # Move students to main class
                        Student.objects.filter(current_class=dup_class).update(current_class=main_class)
                        # Move sections to main class
                        Section.objects.filter(class_assigned=dup_class).update(class_assigned=main_class)
                        # Delete duplicate class
                        dup_class.delete()
                        self.stdout.write(f"  Merged class ID {dup_class.id} into {main_class.id}")
                else:
                    for cls in classes:
                        self.stdout.write(f"  Would merge class ID {cls.id} (numeric_value: {cls.numeric_value})")

        # Step 2: Find duplicate students by admission number
        self.stdout.write(self.style.SUCCESS('\n=== Finding Duplicate Students by Admission Number ==='))
        duplicate_admissions = Student.objects.values('admission_number').annotate(
            count=Count('id')
        ).filter(count__gt=1, admission_number__isnull=False).exclude(admission_number='')

        total_duplicates = 0
        for dup in duplicate_admissions:
            students = Student.objects.filter(admission_number=dup['admission_number']).order_by('id')
            self.stdout.write(f"\nFound {dup['count']} students with admission number '{dup['admission_number']}':")
            
            # Keep the first (oldest) student, mark others for deletion
            main_student = students.first()
            duplicates = students[1:]
            
            for student in students:
                self.stdout.write(f"  ID {student.id}: {student.get_full_name()} - Class: {student.current_class.name if student.current_class else 'None'} - Section: {student.section.name if student.section else 'None'}")
            
            if not dry_run:
                # Move attendance records, marks, etc. to main student if needed
                # Then delete duplicates
                for dup_student in duplicates:
                    # You might want to merge data here instead of just deleting
                    dup_student.delete()
                    total_duplicates += 1
                    self.stdout.write(self.style.WARNING(f"  Deleted duplicate student ID {dup_student.id}"))
            else:
                self.stdout.write(self.style.WARNING(f"  Would delete {len(duplicates)} duplicate(s)"))

        # Step 3: Find students with same name, parent, and phone in different classes
        self.stdout.write(self.style.SUCCESS('\n=== Finding Students with Same Details in Different Classes ==='))
        students_with_duplicates = Student.objects.values(
            'first_name', 'last_name', 'father_name', 'father_phone'
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1,
            father_phone__isnull=False
        ).exclude(father_phone='')

        for dup_group in students_with_duplicates[:20]:  # Limit to first 20 for safety
            students = Student.objects.filter(
                first_name=dup_group['first_name'],
                last_name=dup_group['last_name'],
                father_name=dup_group['father_name'],
                father_phone=dup_group['father_phone']
            ).order_by('id')
            
            if students.count() > 1:
                self.stdout.write(f"\nFound {students.count()} students with same details:")
                self.stdout.write(f"  Name: {dup_group['first_name']} {dup_group['last_name']}")
                self.stdout.write(f"  Parent: {dup_group['father_name']} - {dup_group['father_phone']}")
                
                for student in students:
                    self.stdout.write(f"    ID {student.id}: Admission {student.admission_number} - Class: {student.current_class.name if student.current_class else 'None'}")
                
                if not dry_run:
                    # Keep the one with the most complete data or oldest
                    main_student = students.first()
                    for dup_student in students[1:]:
                        # Check if they have same admission number (definitely duplicate)
                        if dup_student.admission_number == main_student.admission_number:
                            dup_student.delete()
                            total_duplicates += 1
                            self.stdout.write(self.style.WARNING(f"  Deleted duplicate student ID {dup_student.id}"))
                        else:
                            self.stdout.write(self.style.WARNING(f"  Skipped student ID {dup_student.id} - different admission number"))

        # Step 4: Summary
        self.stdout.write(self.style.SUCCESS(f'\n=== Summary ==='))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes made. Run without --dry-run to apply changes.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Cleaned up {total_duplicates} duplicate student(s)'))















