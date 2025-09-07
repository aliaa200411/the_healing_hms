# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime

class Patient(models.Model):
    _name = "hospital.patient"
    _description = "Hospital Patient"

    # ==== Basic Info ====
    patient_code = fields.Char(string="Patient Code", copy=False, readonly=True, index=True)
    first_name = fields.Char(string="First Name", required=True)
    last_name = fields.Char(string="Last Name", required=True)
    name = fields.Char(string="Full Name", compute="_compute_name", store=True)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    total_count = fields.Integer(string="Total Count", compute="_compute_total_count", store=True)
    nationality = fields.Char(string="Nationality")
    dob = fields.Date(string="Date of Birth")
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    blood_type = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-')
    ], string="Blood Type")
    allergies = fields.Text(string="Allergies")
    address = fields.Char(string="Address")

    # ==== Relationships ====
    appointment_ids = fields.One2many("hospital.appointment", "patient_id", string="Appointments")
    diagnosis = fields.Text(string='Diagnosis')
    doctor_id = fields.Many2one('hospital.doctor', string='Doctor')
    partner_id = fields.Many2one('res.partner', string='Related Partner')

    # ==== Insurance Fields ====
    has_insurance = fields.Boolean(string="Has Insurance?", compute="_compute_has_insurance", store=True)
    insurance_company = fields.Many2one('hospital.insurance', string="Insurance Company")

    insurance_coverage = fields.Float(string="Coverage (%)", default=0.0)
    insurance_discount = fields.Float(string="Insurance Discount (%)", compute="_compute_insurance_discount", store=True)

    # ==== COMPUTE METHODS ====
    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.first_name or ''} {rec.last_name or ''}".strip()

    @api.depends('dob')
    def _compute_age(self):
        for rec in self:
            if rec.dob:
                today = fields.Date.today()
                rec.age = today.year - rec.dob.year - ((today.month, today.day) < (rec.dob.month, rec.dob.day))
            else:
                rec.age = 0

    @api.depends('insurance_company')
    def _compute_has_insurance(self):
        for patient in self:
            patient.has_insurance = bool(patient.insurance_company)

    @api.depends('insurance_company', 'insurance_coverage', 'has_insurance')
    def _compute_insurance_discount(self):
        for patient in self:
            if patient.has_insurance and patient.insurance_company:
                if patient.insurance_coverage > 0:
                    patient.insurance_discount = patient.insurance_coverage
                else:
                    patient.insurance_discount = getattr(patient.insurance_company, 'discount_percentage', 0.0)
            else:
                patient.insurance_discount = 0.0

    # ==== OVERRIDE CREATE ====
    @api.model_create_multi
    def create(self, vals_list):
        records = super(Patient, self).create(vals_list)
        for rec in records:
            self.env['hospital.patient.dashboard'].update_patient_dashboard(rec)
        return records

    # ==== OVERRIDE WRITE ====
    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            self.env['hospital.patient.dashboard'].update_patient_dashboard(rec)
        return res

    # ==== OVERRIDE UNLINK ====
    def unlink(self):
        for rec in self:
            dash = self.env['hospital.patient.dashboard'].search([('patient_id','=',rec.id)])
            dash.unlink()
        return super().unlink()

    # ==== ACTIONS ====
    def action_print_medical_record(self):
        return self.env.ref('the_healing_hms.action_report_medical_record').report_action(self)

    # ==== COMPUTE TOTAL COUNT (EXAMPLE FIELD) ====
    @api.depends('appointment_ids')
    def _compute_total_count(self):
        for rec in self:
            rec.total_count = len(rec.appointment_ids)