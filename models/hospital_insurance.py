from odoo import models, fields

class HospitalInsurance(models.Model):
    _name = 'hospital.insurance'
    _description = 'Insurance Company'

    name = fields.Char(string="Insurance Company", required=True)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    street = fields.Char(string="Street")
    city = fields.Char(string="City")
    country_id = fields.Many2one('res.country', string="Country")
    discount_percentage = fields.Float(string="Default Coverage (%)", default=0.0)

    # List of patients linked to this insurance
    patient_ids = fields.One2many('hospital.patient', 'insurance_company', string="Patients")
