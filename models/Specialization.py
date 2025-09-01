# models/hospital_specialization.py
from odoo import models, fields

class HospitalSpecialization(models.Model):
    _name = 'hospital.specialization'
    _description = 'Doctor Specialization'

    code = fields.Char(
        string="Specialization ID",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.specialization') or 'NEW')
    name = fields.Char(string="Name", required=True)