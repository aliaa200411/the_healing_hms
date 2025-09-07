from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalMedicalRecord(models.Model):
    _name = 'hospital.medical.record'
    _description = 'Medical Record'

    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True)
    doctor_id = fields.Many2one(
        'hospital.staff',
        string="Doctor",
        required=True,
        domain=[('job_title','=','doctor')]
    )
    record_date = fields.Date(string="Record Date", required=True)
    diagnosis = fields.Text(string="Diagnosis")
    treatments = fields.Text(string="Treatments / Procedures")
    notes = fields.Text(string="Notes")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")

    @api.constrains('record_date')
    def _check_record_date(self):
        for rec in self:
            if rec.record_date > fields.Date.today():
                raise ValidationError("Record date cannot be in the future.")
