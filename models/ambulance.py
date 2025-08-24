from odoo import fields, models

class Ambulance(models.Model):
    _name = 'hospital.ambulance'
    _description = 'Ambulance (Temporary)'

    name = fields.Char(string='Name')
    department_id = fields.Many2one('hospital.department', string='Department')
    license_plate = fields.Char(string='License Plate')  # إضافة الحقل
    status = fields.Char(string='Status')  # مثال من الـ ER Diagram