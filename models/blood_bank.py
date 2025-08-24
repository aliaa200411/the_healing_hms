from odoo import fields, models

class BloodBank(models.Model):
    _name = 'hospital.blood_bank'
    _description = 'Blood Bank (Temporary)'

    name = fields.Char(string='Name')
    department_id = fields.Many2one('hospital.department', string='Department')
    blood_type = fields.Char(string='Blood Type')  
    quantity = fields.Integer(string='Quantity')
    department_id = fields.Many2one('hospital.department', string='Department')
