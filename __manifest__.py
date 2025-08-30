{
    "name": "Hospital Management System",
    "version": "1.0",
    "summary": "A complete Hospital Management System to manage patients, doctors, staff, appointments, and hospital operations efficiently",
    "sequence": 10,
    "description": """
        The Healing HMS - Patient Management Module
        - Manage patients, medical history, and appointments
        - Role-based access for staff and admin
        - Integration with other hospital modules
    """,
    "category": "Healthcare",
    "author": "The Healing Coders (Aliaa, Mariam, Lama)",
    "depends": ['base', 'mail', 'account', 'product'],
    "data": [
        # Security
        'security/ir.model.access.csv',

        # Menu should be loaded first
        'views/hospital_menu.xml',

        # Hospital Views
        'views/medical_record.xml',
        'views/Doctor.xml',
        'views/room.xml',
        'views/hospital_department_views.xml',
        'views/hospital_room_booking_views.xml',
        'views/staff_views.xml',
        'views/hospital_billing_views.xml',
        'views/appointment_views.xml',

        # Blood Bank Views
        'views/blood_bag_views.xml',
        'views/donor_views.xml',
        'views/transfusion_views.xml',

        # Sequences
        'data/doctor_sequence.xml',
        'data/specialization_sequence.xml',
        'data/staff_sequence.xml',
        'data/billing_sequence.xml',

        # Reports
        'reports/hospital_billing_report.xml',
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
