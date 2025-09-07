# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PatientHistoryWizard(models.TransientModel):
    _name = "patient.history.wizard"
    _description = "Patient History"

    # ==== Many2one ====
    patient_id = fields.Many2one("hospital.patient", string="Patient", readonly=True)

    # ==== Related fields for display ====
    first_name = fields.Char(related='patient_id.first_name', string="First Name", readonly=True)
    last_name = fields.Char(related='patient_id.last_name', string="Last Name", readonly=True)
    age = fields.Integer(related='patient_id.age', string="Age", readonly=True)
    gender = fields.Selection(related='patient_id.gender', string="Gender", readonly=True)
    phone = fields.Char(related='patient_id.phone', string="Phone", readonly=True)
    email = fields.Char(related='patient_id.email', string="Email", readonly=True)
    address = fields.Char(related='patient_id.address', string="Address", readonly=True)
    blood_type = fields.Selection(related='patient_id.blood_type', string="Blood Type", readonly=True)
    doctor_id = fields.Many2one(
        'hospital.staff', 
        string='Doctor',
        domain=[('job_title', '=', 'doctor')]
    )
    diagnosis = fields.Text(related='patient_id.diagnosis', string="Diagnosis", readonly=True)
    allergies = fields.Text(related='patient_id.allergies', string="Allergies", readonly=True)
    # ==== Related Insurance info ====
    has_insurance = fields.Boolean(related='patient_id.has_insurance', string="Has Insurance?", readonly=True)
    insurance_company = fields.Many2one(related='patient_id.insurance_company', string="Insurance Company", readonly=True)
    insurance_coverage = fields.Float(related='patient_id.insurance_coverage', string="Coverage (%)", readonly=True)
    insurance_discount = fields.Float(related='patient_id.insurance_discount', string="Discount (%)", readonly=True)

    # ==== Related One2many ====
    prescription_ids = fields.One2many("hospital.prescription", compute="_compute_history", string="Prescriptions")
    billing_ids = fields.One2many("hospital.billing", compute="_compute_history", string="Billing")
    appointment_ids = fields.One2many("hospital.appointment", compute="_compute_history", string="Appointments")


    lab_result_ids = fields.One2many(
        'hospital.lab.result', 
        compute='_compute_history', 
        string="Lab Results"
    )

    # ==== Compute method to fill one2many fields ====
    @api.depends('patient_id')
    def _compute_history(self):
        for wiz in self:
            if wiz.patient_id:
                wiz.prescription_ids = self.env['hospital.prescription'].search([('patient_id', '=', wiz.patient_id.id)])
                wiz.billing_ids = self.env['hospital.billing'].search([('patient_id', '=', wiz.patient_id.id)])
                wiz.appointment_ids = self.env['hospital.appointment'].search([('patient_id', '=', wiz.patient_id.id)])

                wiz.diagnosis = wiz.patient_id.diagnosis
                wiz.allergies = wiz.patient_id.allergies
                wiz.lab_result_ids = self.env['hospital.lab.result'].search([('request_id.patient_id', '=', wiz.patient_id.id)])
            else:
                wiz.prescription_ids = [(5, 0, 0)]
                wiz.billing_ids = [(5, 0, 0)]
                wiz.appointment_ids = [(5, 0, 0)]
                wiz.diagnosis = ''
                wiz.allergies = ''
    def action_print_history(self):
        return self.env.ref('the_healing_hms.action_report_patient_history').report_action(self)