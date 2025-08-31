from odoo import models, fields, api

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

    # List of patients linked to this insurance (One2many)
    patient_ids = fields.One2many('hospital.patient', 'insurance_company', string="Patients")

    # Count of patients (Smart Button)
    patient_count = fields.Integer(string="Number of Patients", compute="_compute_patient_count")

    @api.depends('patient_ids')
    def _compute_patient_count(self):
        for insurance in self:
            insurance.patient_count = len(insurance.patient_ids)

    # Smart Button Action
    def action_view_patients(self):
        self.ensure_one()
        return {
            'name': 'Patients',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.patient',
            'view_mode': 'list,form',
            'domain': [('insurance_company', '=', self.id)],
            'target': 'current',
        }