{
    "name": "Hospital  Management System ",
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
    "depends": ["base", 'mail', 'account'],
    "data": [
        'security/ir.model.access.csv', 
        'views/hospital_menu.xml', 
        'views/Doctor.xml',
        'views/room.xml',          
        'views/hospital_department_views.xml',
        'views/hospital_room_booking_views.xml',
        
    ],
      
    "installable": True,
    "application": True,
}