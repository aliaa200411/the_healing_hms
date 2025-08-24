{
    'name': 'Hospital Departments',
    'version': '1.0',
    'author': 'Lama Zuaiter',
    'category': 'Hospital Management',
    'summary': 'Manage hospital departments, rooms, doctors, staff, and patients',
    'description': 'Hospital management module with departments, rooms, doctors, staff, and patients',
    'depends': ['base', 'mail', 'account'],
    'data': [
        'security/ir.model.access.csv', 
        'views/hospital_menu.xml', 
        'views/Doctor.xml',
        'views/room.xml',          
        'views/hospital_department_views.xml',
        'views/hospital_room_booking_views.xml',    ],
    'installable': True,
    'application': True,
}
