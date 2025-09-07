from odoo import models, fields, api
from datetime import datetime

class HospitalPatientDashboard(models.Model):
    _name = 'hospital.patient.dashboard'
    _description = 'Hospital Patient Dashboard'
    _auto = True

    # العلاقة مع المريض
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True)

    # بيانات أساسية للـ Dashboard
    first_name = fields.Char(
        string="First Name",
        related='patient_id.first_name',
        store=True
    )
    last_name = fields.Char(
        string="Last Name",
        related='patient_id.last_name',
        store=True
    )
    age = fields.Integer(
        string="Age",
        related='patient_id.age',
        store=True
    )
    gender = fields.Selection(
        [('male','ذكر'), ('female','أنثى')],
        string="Gender",
        related='patient_id.gender',
        store=True
    )
    blood_type = fields.Selection(
        [
            ('a+', 'A+'), ('a-', 'A-'),
            ('b+', 'B+'), ('b-', 'B-'),
            ('ab+', 'AB+'), ('ab-', 'AB-'),
            ('o+', 'O+'), ('o-', 'O-')
        ],
        string="Blood Type",
        related='patient_id.blood_type',
        store=True
    )
    phone = fields.Char(related='patient_id.phone', store=True)
    email = fields.Char(related='patient_id.email', store=True)
    nationality = fields.Char(related='patient_id.nationality', store=True)
    address = fields.Char(related='patient_id.address', store=True)
    allergies = fields.Text(related='patient_id.allergies', store=True)
    diagnosis = fields.Text(related='patient_id.diagnosis', store=True)
    doctor_id = fields.Many2one(related='patient_id.doctor_id', store=True)
    total_count = fields.Integer(related='patient_id.total_count', store=True)
    has_insurance = fields.Boolean(
        string="Has Insurance",
        related='patient_id.has_insurance',
        store=True
    )
    insurance_company = fields.Many2one(
        'hospital.insurance',
        string="Insurance Company",
        related='patient_id.insurance_company',
        store=True
    )
    insurance_coverage = fields.Float(related='patient_id.insurance_coverage', store=True)
    insurance_discount = fields.Float(related='patient_id.insurance_discount', store=True)

    # حقول رقمية للـ Graph
    has_insurance_int = fields.Integer(
        string="Insurance (Int)",
        compute="_compute_has_insurance_int",
        store=True
    )
    male_count = fields.Integer(
        string="Male Count",
        compute="_compute_gender_count",
        store=True
    )
    female_count = fields.Integer(
        string="Female Count",
        compute="_compute_gender_count",
        store=True
    )

    @api.depends('has_insurance')
    def _compute_has_insurance_int(self):
        for rec in self:
            rec.has_insurance_int = 1 if rec.has_insurance else 0

    @api.depends('gender')
    def _compute_gender_count(self):
        for rec in self:
            rec.male_count = 1 if rec.gender == 'male' else 0
            rec.female_count = 1 if rec.gender == 'female' else 0

    # اختيار الشهر للفلترة أو التقارير
    month = fields.Selection(
        [(str(i), str(i)) for i in range(1, 13)],
        string="Month",
        default=lambda self: str(datetime.now().month)
    )

    @api.model
    def update_patient_dashboard(self, patient):
        """تحديث أو إنشاء صف Dashboard عند أي تعديل بالمريض"""
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
            'total_count': patient.total_count,
            'has_insurance': patient.has_insurance,
            'insurance_company': patient.insurance_company.id if patient.insurance_company else False,
            'insurance_coverage': patient.insurance_coverage,
            'insurance_discount': patient.insurance_discount
        }
        if dashboard:
            dashboard.write(vals)
        else:
            self.create(vals)
