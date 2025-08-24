from odoo import models, fields

class MedicalRecord(models.Model):
    _name = 'hospital.medical.record'
    _description = 'Medical Record'

    patient_id = fields.Many2one('hospital.patient', string='Patient')
    doctor_id = fields.Many2one('hospital.doctor', string='Doctor')
    date = fields.Date(string='Date')
    notes = fields.Text(string='Notes')