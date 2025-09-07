# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

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
    doctor_id = fields.Many2one('hospital.staff', string="Doctor", domain=[('job_title','=','doctor')])
    partner_id = fields.Many2one('res.partner', string='Related Partner')
    prescription_ids = fields.One2many("hospital.prescription", "patient_id", string="Prescriptions")

    # ==== Insurance Fields ====
    has_insurance = fields.Boolean(
        string="Has Insurance?",
        compute="_compute_has_insurance",
        store=True
    )
    billing_ids = fields.One2many(
    'hospital.billing',   # اسم الموديل تبع الفواتير
    'patient_id',         # الحقل الموجود بموديل الفواتير اللي بيربط المريض
    string="Billings"
    )

    insurance_company = fields.Many2one('hospital.insurance', string="Insurance Company")
    insurance_coverage = fields.Float(
        string="Coverage (%)",
        default=0.0,
        help="Percentage of insurance coverage"
    )
    insurance_discount = fields.Float(
        string="Insurance Discount (%)",
        compute="_compute_insurance_discount",
        store=True
    )

    
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
                rec.age = today.year - rec.dob.year - (
                    (today.month, today.day) < (rec.dob.month, rec.dob.day)
                )
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
                    patient.insurance_discount = getattr(
                        patient.insurance_company, 'discount_percentage', 0.0
                    )
            else:
                patient.insurance_discount = 0.0

    # ==== OVERRIDE CREATE ====
    @api.model_create_multi
    def create(self, vals_list):
        patients = super(Patient, self).create(vals_list)
        for patient in patients:
            # توليد patient_code إذا غير موجود
            if not patient.patient_code:
                patient.patient_code = self.env['ir.sequence'].next_by_code('hospital.patient') or _('New')
           
        return patients

    # ==== Smart Button: View Prescriptions ====
    def action_view_prescriptions(self):
        self.ensure_one()
        return {
            'name': _('Prescriptions'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.prescription',
            'view_mode': 'list,form',
            'domain': [('patient_id', '=', self.id)],  # فقط وصفات المريض الحالي
            'target': 'current',
            'context': {'default_patient_id': self.id},
        }

    # ==== Smart Button: Create Prescription ====
    def action_create_prescription(self):
        self.ensure_one()
        return {
            'name': _('New Prescription'),
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.prescription',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_doctor_id': self.doctor_id.id,
                'default_patient_id': self.id,
            },
        }

    # ==== Smart Button: View Patient History (Wizard) ====
    def action_view_patient_history(self):
        self.ensure_one()
        return {
            'name': _('Patient History'),
            'type': 'ir.actions.act_window',
            'res_model': 'patient.history.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_patient_id': self.id},
        }
