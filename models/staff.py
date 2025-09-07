# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HospitalStaff(models.Model):
    _name = 'hospital.staff'
    _description = 'Hospital Staff'
    _order = 'name'

    # ===== البيانات الأساسية =====
    name = fields.Char(string="Name", required=True)
    job_title = fields.Selection([
        ('manager', 'Manager'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('accountant', 'Accountant'),
        ('pharmacist', 'Pharmacist'),
        ('ambulance', 'Ambulance Driver'),
        ('lab', 'Lab Technician'),
    ], string="Job Title", required=True)

    user_id = fields.Many2one('res.users', string="Related User")
    department_id = fields.Many2one('hospital.department', string="Department")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    hire_date = fields.Date(string="Hire Date")
    salary = fields.Float(string="Salary")
    active = fields.Boolean(string="Active", default=True)

    # ===== حقول إضافية حسب نوع الموظف =====
    experience_years = fields.Integer(string="Experience (Years)", default=0)
    working_hours = fields.Float(string="Working Hours", default=0.0)
    management = fields.Integer(string="Management", default=0)
    is_available = fields.Boolean(string="Available", default=True)
    ambulance_id = fields.Many2one('healing_hms.ambulance', string="Ambulance")
    status = fields.Selection([
        ('available', 'Available'),
        ('on_duty', 'On Duty'),
        ('off', 'Off Duty')
    ], string="Driver Status", default='available')

    # ===== حقول خاصة بالطبيب =====
    specialization_id = fields.Many2one('hospital.specialization', string="Specialization")
    patient_ids = fields.One2many('hospital.patient', 'doctor_id', string="Patients")
    patient_count = fields.Integer(
        string="Number of Patients",
        compute='_compute_patient_count',
        compute_sudo=True
    )

    @api.depends('patient_ids')
    def _compute_patient_count(self):
        for rec in self:
            rec.patient_count = len(rec.patient_ids) if rec.job_title == 'doctor' else 0

    # ===== Staff ID ديناميكي حسب الوظيفة =====
    staff_id = fields.Char(
        string="Staff ID",
        required=True,
        copy=False,
        readonly=True,
        default='NEW'
    )

    # ===== توليد Staff ID عند الإنشاء =====
    @api.model
    def create(self, vals_list):
        updated_vals_list = []
        for vals in vals_list:
            vals = self._update_staff_id(vals)
            updated_vals_list.append(vals)
        return super().create(updated_vals_list)

    # ===== توليد Staff ID عند تعديل job_title =====
    def write(self, vals):
        if 'job_title' in vals and vals['job_title'] != self.job_title:
            vals = self._update_staff_id(vals)
        return super().write(vals)

    # ===== دالة مساعدة لتوليد Staff ID =====
    def _update_staff_id(self, vals):
        job_title = vals.get('job_title')
        if not job_title:
            return vals
        code_map = {
            'manager': 'hospital.staff.manager',
            'doctor': 'hospital.staff.doctor',
            'nurse': 'hospital.staff.nurse',
            'receptionist': 'hospital.staff.receptionist',
            'accountant': 'hospital.staff.accountant',
            'pharmacist': 'hospital.staff.pharmacist',
            'ambulance': 'hospital.staff.driver',
            'lab': 'hospital.staff.lab',
        }
        seq_code = code_map.get(job_title)
        if seq_code:
            seq_obj = self.env['ir.sequence'].sudo().search([('code','=',seq_code)], limit=1)
            if seq_obj:
                vals['staff_id'] = seq_obj.next_by_id() or 'NEW'
        return vals