from odoo import fields, models

class Ambulance(models.Model):
    _name = 'hospital.ambulance'
    _description = 'Ambulance (Temporary)'

    name = fields.Char(string='Name')
    department_id = fields.Many2one('hospital.department', string='Department')
    license_plate = fields.Char(string='License Plate') 
    status = fields.Char(string='Status') 