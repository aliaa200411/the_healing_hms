# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class HospitalPatientDashboard(models.Model):
    _name = 'hospital.patient.dashboard'
    _description = 'Hospital Patient Dashboard'
    _auto = True

    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True)

    # ==== بيانات المريض ====
    first_name = fields.Char(related='patient_id.first_name', store=True)
    last_name = fields.Char(related='patient_id.last_name', store=True)

    # حذف age من measures (ما يبين بالقائمة)
    age = fields.Integer(compute="_compute_hide_age", store=False)

    gender = fields.Selection(
        [('male', 'ذكر'), ('female', 'أنثى')],
        related='patient_id.gender',
        store=True
    )
    blood_type = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-')
    ], related='patient_id.blood_type', store=True)
    phone = fields.Char(related='patient_id.phone', store=True)
    email = fields.Char(related='patient_id.email', store=True)
    nationality = fields.Char(related='patient_id.nationality', store=True)
    address = fields.Char(related='patient_id.address', store=True)
    allergies = fields.Text(related='patient_id.allergies', store=True)
    diagnosis = fields.Text(related='patient_id.diagnosis', store=True)
    doctor_id = fields.Many2one(related='patient_id.doctor_id', store=True)
    has_insurance = fields.Boolean(related='patient_id.has_insurance', store=True)
    insurance_company = fields.Many2one(
        'hospital.insurance',
        related='patient_id.insurance_company',
        store=True
    )

    # ==== نسب للجراف ====
    gender_ratio = fields.Float(string="Gender Ratio (%)", compute="_compute_gender_ratio", store=True)
    insurance_with_ratio = fields.Float(string="Patients with Insurance (%)", compute="_compute_insurance_ratios", store=True)
    avg_age = fields.Float(string="Average Age", compute="_compute_avg_age", store=True)

    month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)],
        string="Month",
        default=lambda self: str(datetime.now().month)
    )

    # ==== منع ظهور age ====
    def _compute_hide_age(self):
        for rec in self:
            rec.age = False

    # ==== حساب نسبة الجندر ====
    @api.depends('patient_id.gender')
    def _compute_gender_ratio(self):
        patients = self.env['hospital.patient'].search([])
        total = len(patients)

        male_total = len(patients.filtered(lambda p: p.gender == 'male'))
        female_total = total - male_total

        male_ratio = (male_total / total) * 100 if total > 0 else 0
        female_ratio = (female_total / total) * 100 if total > 0 else 0

        for rec in self:
            if rec.gender == 'male':
                rec.gender_ratio = male_ratio
            elif rec.gender == 'female':
                rec.gender_ratio = female_ratio
            else:
                rec.gender_ratio = 0.0

    # ==== حساب نسب التأمين ====
    @api.depends('patient_id.has_insurance')
    def _compute_insurance_ratios(self):
        patients = self.env['hospital.patient'].search([])
        total = len(patients)

        if total == 0:
            yes_ratio = 0
        else:
            yes_total = len(patients.filtered(lambda p: p.has_insurance))
            yes_ratio = (yes_total / total) * 100

        for rec in self:
            rec.insurance_with_ratio = yes_ratio

    # ==== حساب متوسط العمر ====
    @api.depends('patient_id.age')
    def _compute_avg_age(self):
        patients = self.env['hospital.patient'].search([('age', '!=', False)])
        total_age = sum(patients.mapped('age'))
        avg_age = total_age / len(patients) if patients else 0.0

        for rec in self:
            rec.avg_age = avg_age

    # ==== تحديث Dashboard ====
    @api.model
    def update_patient_dashboard(self, patient):
        dashboard = self.search([('patient_id', '=', patient.id)])
        vals = {
            'patient_id': patient.id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'age': patient.age,
            'gender': patient.gender,
            'blood_type': patient.blood_type,
            'phone': patient.phone,
            'email': patient.email,
            'nationality': patient.nationality,
            'address': patient.address,
            'allergies': patient.allergies,
            'diagnosis': patient.diagnosis,
            'doctor_id': patient.doctor_id.id if patient.doctor_id else False,
            'has_insurance': patient.has_insurance,
            'insurance_company': patient.insurance_company.id if patient.insurance_company else False,
        }
        if dashboard:
            dashboard.write(vals)
        else:
            self.create(vals)
