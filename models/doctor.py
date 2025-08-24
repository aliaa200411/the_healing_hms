from odoo import models, fields

class HospitalDoctor(models.Model):
    _name = 'hospital.doctor'
    _description = 'Doctor'

    name = fields.Char(string='Doctor Name', required=True)
    user_id = fields.Many2one('res.users', string='Related User')
    phone = fields.Char(string='Phone')  
    specialization_id = fields.Many2one('hospital.specialization', string='Specialization')
    management_years = fields.Integer(string='Years of Management')
    department_id = fields.Many2one('hospital.department', string='Department')
