"""
Central registry describing all toggleable features in the School ERP.

Each feature entry supplies:
    - key: unique identifier used in configuration storage/templates
    - label: human readable name
    - description: short helper text for configuration UI
    - default: default enabled/disabled state when no config exists
    - roles: list of roles that primarily consume the feature (used for docs/UI)
    - related_models: ORM models powering the feature (for audits/debugging)
    - legacy_field (optional): existing boolean field on SystemConfiguration that
      should stay in sync with this feature flag for backwards compatibility.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class FeatureDefinition:
    key: str
    label: str
    description: str
    default: bool = True
    roles: Iterable[str] = ()
    related_models: Iterable[str] = ()
    legacy_field: Optional[str] = None


FEATURE_GROUPS: List[Dict[str, object]] = [
    {
        "id": "core_modules",
        "label": "Core Modules",
        "features": [
            FeatureDefinition(
                key="crm_enabled",
                label="CRM Module",
                description="Lead, campaign, and application management",
                default=True,
                roles=("super_admin", "school_admin", "admissions"),
                related_models=(
                    "students_app.enrollment_crm_models.Lead",
                    "students_app.enrollment_crm_models.Campaign",
                    "students_app.enrollment_crm_models.Application",
                    "students_app.enrollment_crm_models.LeadActivity",
                    "students_app.enrollment_crm_models.LeadSource",
                ),
                legacy_field="crm_enabled",
            ),
            FeatureDefinition(
                key="erp_enabled",
                label="ERP Module",
                description="Student information system core functionality",
                default=True,
                roles=("school_admin", "super_admin"),
                related_models=("students_app.models.Student",),
                legacy_field="erp_enabled",
            ),
            FeatureDefinition(
                key="id_card_generator",
                label="ID Card Generator",
                description="Advanced ID card batch generation workflows",
                default=True,
                roles=("super_admin", "school_admin"),
                related_models=(
                    "students_app.models.IDCardGenerator",
                    "students_app.models.IDCardData",
                    "students_app.models.StudentIDCard",
                    "students_app.models.IDCardTemplate",
                ),
                legacy_field="id_card_generator",
            ),
            FeatureDefinition(
                key="fee_payment_online",
                label="Online Fee Payment",
                description="Razorpay integration for digital collections",
                default=True,
                roles=("school_admin", "parent"),
                related_models=("students_app.models.FeePayment",),
                legacy_field="fee_payment_online",
            ),
            FeatureDefinition(
                key="attendance_tracking",
                label="Attendance Tracking",
                description="Daily attendance marking and reporting",
                default=True,
                roles=("teacher", "school_admin", "parent"),
                related_models=("students_app.models.Attendance",),
                legacy_field="attendance_tracking",
            ),
            FeatureDefinition(
                key="marks_entry",
                label="Marks Entry",
                description="Exam schedules, marks entry, and report cards",
                default=True,
                roles=("teacher", "school_admin", "student", "parent"),
                related_models=(
                    "students_app.models.Exam",
                    "students_app.models.ExamSchedule",
                    "students_app.models.Marks",
                    "students_app.models.ClassTest",
                    "students_app.models.ClassTestScore",
                ),
                legacy_field="marks_entry",
            ),
            FeatureDefinition(
                key="library_management",
                label="Library Management",
                description="Library catalogue and circulation tracking",
                default=True,
                roles=("librarian", "school_admin", "student", "teacher"),
                related_models=(
                    "students_app.models.BookCategory",
                    "students_app.models.Book",
                    "students_app.models.BookIssue",
                ),
                legacy_field="library_management",
            ),
            FeatureDefinition(
                key="transport_management",
                label="Transport Management",
                description="Routes, buses, and student allocations",
                default=False,
                roles=("school_admin", "transport_manager"),
                related_models=(
                    "students_app.models.TransportRoute",
                    "students_app.models.Bus",
                    "students_app.models.StudentTransport",
                ),
                legacy_field="transport_management",
            ),
            FeatureDefinition(
                key="hostel_management",
                label="Hostel Management",
                description="Hostel, rooms, and student allocations",
                default=False,
                roles=("school_admin", "hostel_manager"),
                related_models=(
                    "students_app.models.Hostel",
                    "students_app.models.HostelRoom",
                    "students_app.models.HostelAllocation",
                ),
                legacy_field="hostel_management",
            ),
            FeatureDefinition(
                key="canteen_management",
                label="Canteen Management",
                description="Canteen menu, orders, and billing",
                default=False,
                roles=("school_admin", "canteen_manager", "student"),
                related_models=(
                    "students_app.models.CanteenItem",
                    "students_app.models.CanteenOrder",
                    "students_app.models.OrderItem",
                ),
                legacy_field="canteen_management",
            ),
        ],
    },
    {
        "id": "activities",
        "label": "Co-curricular & Activities",
        "features": [
            FeatureDefinition(
                key="activity_categories",
                label="Activity Categories",
                description="Configure activity classifications",
                related_models=("students_app.models.ActivityCategory",),
            ),
            FeatureDefinition(
                key="co_curricular_activities",
                label="Co-curricular Activities",
                description="Manage activities and instructors",
                related_models=("students_app.models.CoCurricularActivity",),
            ),
            FeatureDefinition(
                key="activity_registrations",
                label="Activity Registrations",
                description="Track student participation and fees",
                related_models=("students_app.models.ActivityRegistration",),
            ),
        ],
    },
    {
        "id": "alumni",
        "label": "Alumni Management",
        "features": [
            FeatureDefinition(
                key="alumni",
                label="Alumni",
                description="Maintain alumni directory and engagement",
                related_models=("students_app.models.Alumni",),
            ),
        ],
    },
    {
        "id": "crm",
        "label": "Admissions CRM",
        "features": [
            FeatureDefinition(
                key="applications",
                label="Applications",
                description="Application pipeline tracking",
                related_models=("students_app.enrollment_crm_models.Application",),
            ),
            FeatureDefinition(
                key="campaigns",
                label="Campaigns",
                description="Marketing and outreach campaigns",
                related_models=("students_app.enrollment_crm_models.Campaign",),
            ),
            FeatureDefinition(
                key="lead_sources",
                label="Lead Sources",
                description="Manage lead source taxonomy",
                related_models=("students_app.enrollment_crm_models.LeadSource",),
            ),
            FeatureDefinition(
                key="lead_activities",
                label="Lead Activities",
                description="Interaction history with prospective students",
                related_models=("students_app.enrollment_crm_models.LeadActivity",),
            ),
            FeatureDefinition(
                key="leads",
                label="Leads",
                description="Lead intake and qualification",
                related_models=("students_app.enrollment_crm_models.Lead",),
            ),
        ],
    },
    {
        "id": "certificates",
        "label": "Certificates & ID",
        "features": [
            FeatureDefinition(
                key="certificate_templates",
                label="Certificate Templates",
                description="Design templates for student certificates",
                related_models=("students_app.models.CertificateTemplate",),
            ),
            FeatureDefinition(
                key="certificates",
                label="Certificates",
                description="Issue and track student certificates",
                related_models=("students_app.models.Certificate",),
            ),
            FeatureDefinition(
                key="id_card_generators",
                label="ID Card Generators",
                description="Configure generator blueprints",
                related_models=("students_app.models.IDCardGenerator",),
            ),
            FeatureDefinition(
                key="id_card_data_entries",
                label="ID Card Data",
                description="Manage raw data for ID card generation",
                related_models=("students_app.models.IDCardData",),
            ),
        ],
    },
    {
        "id": "education_games",
        "label": "Educational Games",
        "features": [
            FeatureDefinition(
                key="game_categories",
                label="Game Categories",
                description="Organise educational games",
                related_models=("students_app.models.GameCategory",),
            ),
            FeatureDefinition(
                key="educational_games",
                label="Educational Games",
                description="Manage game metadata and lifecycle",
                related_models=("students_app.models.EducationalGame",),
            ),
            FeatureDefinition(
                key="game_questions",
                label="Game Questions",
                description="Maintain question banks per game",
                related_models=("students_app.models.GameQuestion",),
            ),
            FeatureDefinition(
                key="game_answers",
                label="Game Answers",
                description="Configure answer options for games",
                related_models=("students_app.models.GameAnswer",),
            ),
            FeatureDefinition(
                key="game_sessions",
                label="Game Sessions",
                description="Track gameplay sessions and scores",
                related_models=("students_app.models.GameSession",),
            ),
            FeatureDefinition(
                key="game_achievements",
                label="Game Achievements",
                description="Define unlockable achievements",
                related_models=("students_app.models.GameAchievement",),
            ),
            FeatureDefinition(
                key="student_game_achievements",
                label="Student Game Achievements",
                description="Record achievements unlocked by students",
                related_models=("students_app.models.StudentGameAchievement",),
            ),
        ],
    },
    {
        "id": "elections",
        "label": "Student Elections",
        "features": [
            FeatureDefinition(
                key="elections",
                label="Elections",
                description="Configure election events",
                related_models=("students_app.models.Election",),
            ),
            FeatureDefinition(
                key="election_nominations",
                label="Election Nominations",
                description="Manage nomination submissions",
                related_models=("students_app.models.ElectionNomination",),
            ),
            FeatureDefinition(
                key="election_votes",
                label="Election Votes",
                description="Track cast votes",
                related_models=("students_app.models.ElectionVote",),
            ),
            FeatureDefinition(
                key="election_results",
                label="Election Results",
                description="Publish and audit election results",
                related_models=("students_app.models.ElectionResult",),
            ),
        ],
    },
    {
        "id": "exams_online",
        "label": "Online Exams & Mock Tests",
        "features": [
            FeatureDefinition(
                key="online_exams",
                label="Online Exams",
                description="Deliver timed online examinations",
                related_models=("students_app.models.OnlineExam",),
            ),
            FeatureDefinition(
                key="exam_questions",
                label="Exam Questions",
                description="Question bank for online exams",
                related_models=("students_app.models.OnlineExamQuestion",),
            ),
            FeatureDefinition(
                key="exam_attempts",
                label="Exam Attempts",
                description="Track online exam attempts",
                related_models=("students_app.models.OnlineExamAttempt",),
            ),
            FeatureDefinition(
                key="exam_answers",
                label="Exam Answers",
                description="Store responses for online exams",
                related_models=("students_app.models.OnlineExamAnswer",),
            ),
            FeatureDefinition(
                key="mock_test_categories",
                label="Mock Test Categories",
                description="Organise mock test catalog",
                related_models=("students_app.models.MockTestCategory",),
            ),
            FeatureDefinition(
                key="mock_tests",
                label="Mock Tests",
                description="Create mock tests for board prep",
                related_models=("students_app.models.MockTest",),
            ),
            FeatureDefinition(
                key="mock_test_questions",
                label="Mock Test Questions",
                description="Question bank for mock tests",
                related_models=("students_app.models.MockTestQuestion",),
            ),
            FeatureDefinition(
                key="mock_test_answers",
                label="Mock Test Answers",
                description="Answer options for mock tests",
                related_models=("students_app.models.MockTestAnswer",),
            ),
            FeatureDefinition(
                key="mock_test_sessions",
                label="Mock Test Sessions",
                description="Track mock test sessions",
                related_models=("students_app.models.MockTestSession",),
            ),
            FeatureDefinition(
                key="mock_test_attempts",
                label="Mock Test Attempts",
                description="Record responses within sessions",
                related_models=("students_app.models.MockTestAttempt",),
            ),
        ],
    },
    {
        "id": "health",
        "label": "Health & Wellness",
        "features": [
            FeatureDefinition(
                key="health_checkups",
                label="Health Checkups",
                description="Capture annual health screening data",
                related_models=("students_app.models.HealthCheckup",),
            ),
            FeatureDefinition(
                key="medical_records",
                label="Medical Records",
                description="Maintain detailed medical history",
                related_models=("students_app.models.MedicalRecord",),
            ),
        ],
    },
    {
        "id": "homework",
        "label": "Homework & Assignments",
        "features": [
            FeatureDefinition(
                key="homeworks",
                label="Homeworks",
                description="Teacher homework creation",
                related_models=("students_app.models.Homework",),
            ),
            FeatureDefinition(
                key="homework_submissions",
                label="Homework Submissions",
                description="Student submissions and grading",
                related_models=("students_app.models.HomeworkSubmission",),
            ),
        ],
    },
    {
        "id": "hostel",
        "label": "Hostel Operations",
        "features": [
            FeatureDefinition(
                key="hostels",
                label="Hostels",
                description="Manage hostel properties",
                related_models=("students_app.models.Hostel",),
            ),
            FeatureDefinition(
                key="hostel_rooms",
                label="Hostel Rooms",
                description="Room inventory and maintenance",
                related_models=("students_app.models.HostelRoom",),
            ),
            FeatureDefinition(
                key="hostel_allocations",
                label="Hostel Allocations",
                description="Student room allocations",
                related_models=("students_app.models.HostelAllocation",),
            ),
        ],
    },
    {
        "id": "houses",
        "label": "House System",
        "features": [
            FeatureDefinition(
                key="houses",
                label="Houses",
                description="Define school houses",
                related_models=("students_app.models.House",),
            ),
            FeatureDefinition(
                key="house_memberships",
                label="House Memberships",
                description="Assign students to houses",
                related_models=("students_app.models.HouseMembership",),
            ),
            FeatureDefinition(
                key="house_events",
                label="House Events",
                description="Schedule inter-house events",
                related_models=("students_app.models.HouseEvent",),
            ),
            FeatureDefinition(
                key="house_event_results",
                label="House Event Results",
                description="Record outcomes and points",
                related_models=("students_app.models.HouseEventResult",),
            ),
        ],
    },
    {
        "id": "inventory",
        "label": "Inventory & Assets",
        "features": [
            FeatureDefinition(
                key="inventory_categories",
                label="Inventory Categories",
                description="Catalog inventory groups",
                related_models=("students_app.models.InventoryCategory",),
            ),
            FeatureDefinition(
                key="inventory_items",
                label="Inventory Items",
                description="Manage physical items",
                related_models=("students_app.models.InventoryItem",),
            ),
            FeatureDefinition(
                key="inventory_transactions",
                label="Inventory Transactions",
                description="Issue/receive inventory transactions",
                related_models=("students_app.models.InventoryTransaction",),
            ),
        ],
    },
    {
        "id": "leadership",
        "label": "Leadership & Leave",
        "features": [
            FeatureDefinition(
                key="leadership_positions",
                label="Leadership Positions",
                description="Define leadership roles",
                related_models=("students_app.models.LeadershipPosition",),
            ),
            FeatureDefinition(
                key="student_leadership",
                label="Student Leadership",
                description="Assign students to leadership roles",
                related_models=("students_app.models.StudentLeadership",),
            ),
            FeatureDefinition(
                key="leave_types",
                label="Leave Types",
                description="Configure leave categories",
                related_models=("students_app.models.LeaveType",),
            ),
            FeatureDefinition(
                key="leave_applications",
                label="Leave Applications",
                description="Process student/staff leave",
                related_models=("students_app.models.LeaveApplication",),
            ),
        ],
    },
    {
        "id": "finance",
        "label": "Finance & Payroll",
        "features": [
            FeatureDefinition(
                key="school_billing",
                label="School Billing",
                description="Subscription billing for schools",
                related_models=("students_app.models.SchoolBilling",),
            ),
            FeatureDefinition(
                key="salary_components",
                label="Salary Components",
                description="Define payroll components",
                related_models=("students_app.models.SalaryComponent",),
            ),
            FeatureDefinition(
                key="salaries",
                label="Salaries",
                description="Process staff salaries",
                related_models=("students_app.models.Salary",),
            ),
        ],
    },
    {
        "id": "organisation",
        "label": "Organisation & Staff",
        "features": [
            FeatureDefinition(
                key="schools",
                label="Schools",
                description="Manage registered schools",
                related_models=("students_app.models.School",),
            ),
            FeatureDefinition(
                key="staff_categories",
                label="Staff Categories",
                description="Staff categorisation",
                related_models=("students_app.models.StaffCategory",),
            ),
            FeatureDefinition(
                key="staff",
                label="Staff",
                description="Employee records and onboarding",
                related_models=("students_app.models.Staff",),
            ),
        ],
    },
    {
        "id": "sports",
        "label": "Sports & Athletics",
        "features": [
            FeatureDefinition(
                key="sports_categories",
                label="Sports Categories",
                description="Sports taxonomy",
                related_models=("students_app.models.SportsCategory",),
            ),
            FeatureDefinition(
                key="sports",
                label="Sports",
                description="Extracurricular sports programs",
                related_models=("students_app.models.Sport",),
            ),
            FeatureDefinition(
                key="sports_registrations",
                label="Sports Registrations",
                description="Student participation tracking",
                related_models=("students_app.models.SportsRegistration",),
            ),
            FeatureDefinition(
                key="sports_achievements",
                label="Sports Achievements",
                description="Record competition achievements",
                related_models=("students_app.models.SportsAchievement",),
            ),
        ],
    },
]


def _build_feature_map() -> Dict[str, FeatureDefinition]:
    mapping: Dict[str, FeatureDefinition] = {}
    for group in FEATURE_GROUPS:
        for definition in group["features"]:  # type: ignore[index]
            mapping[definition.key] = definition
    return mapping


FEATURE_MAP: Dict[str, FeatureDefinition] = _build_feature_map()


def iter_all_features() -> Iterable[FeatureDefinition]:
    """Convenience generator returning all FeatureDefinition entries."""
    return FEATURE_MAP.values()



