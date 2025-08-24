from odoo import fields, models

class Staff(models.Model):
    _name = 'hospital.staff'
    _description = 'Staff (Temporary)'

    name = fields.Char(string='Name')
    department_id = fields.Many2one('hospital.department', string='Department')
    role = fields.Char(string='Role')  
    phone = fields.Char(string='Phone')  
