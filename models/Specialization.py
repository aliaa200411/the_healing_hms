# models/hospital_specialization.py
from odoo import models, fields

class HospitalSpecialization(models.Model):
    _name = 'hospital.specialization'
    _description = 'Doctor Specialization'

    name = fields.Char(string="Specialization Name", required=True)
    code = fields.Char(string="Code")  
