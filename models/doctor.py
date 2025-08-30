# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Doctor(models.Model):
    _name = "hospital.doctor"
    _description = "Doctor"

    # رقم تعريف الطبيب (يتولد تلقائيًا)
    doctor_id = fields.Char(
        string="Doctor ID",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.doctor') or 'NEW'
    )

    # بيانات الاتصال
    phone = fields.Char(string="Phone")
    user_id = fields.Many2one("res.users", string="User")
    name = fields.Char(string="Doctor Name", required=True)   # 👈 صححنا المسافة

    # التخصص والقسم
    specialization_id = fields.Many2one("hospital.specialization", string="Specialization")
    department_id = fields.Many2one("hospital.department", string="Department")

    # معلومات إضافية
    management = fields.Integer(string="Management")
    experience_years = fields.Integer(string="Experience (Years)")
    working_hours = fields.Float(string="Working Hours")
    is_available = fields.Boolean(string="Available")
    hire_date = fields.Date(string="Hire Date")
    salary = fields.Float(string="Salary")

    # علاقة مع المرضى
    patient_ids = fields.One2many(
        "hospital.patient",  # موديل المرضى
        "doctor_id",         # الحقل المرتبط في موديل المرضى
        string="Patients"
    )

    # حساب عدد المرضى تلقائيًا
    patient_count = fields.Integer(
        string="Number of Patients",
        compute="_compute_patient_count"
    )

    @api.depends('patient_ids')
    def _compute_patient_count(self):
        for rec in self:
            rec.patient_count = len(rec.patient_ids)
