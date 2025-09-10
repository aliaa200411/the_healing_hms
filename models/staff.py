# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HospitalStaff(models.Model):
    _name = 'hospital.staff'
    _description = 'Hospital Staff'
    _order = 'name'

    # ===== البيانات الأساسية =====
    name = fields.Char(string="Name", required=True)
    job_title = fields.Selection([
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('receptionist', 'Receptionist'),
        ('accountant', 'Accountant'),
        ('pharmacist', 'Pharmacist'),
        ('ambulance', 'Ambulance Driver'),
        ('lab', 'Lab Technician'),
    ], string="Job Title", required=True)

    user_id = fields.Many2one(
        'res.users', string="Related User", readonly=True, ondelete='cascade'
    )
    department_id = fields.Many2one('hospital.department', string="Department")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email", required=True)
    hire_date = fields.Date(string="Hire Date")
    salary = fields.Float(string="Salary")
    active = fields.Boolean(string="Active", default=True)

    # ===== تحقق من uniqueness =====
    _sql_constraints = [
        ('unique_staff_email', 'unique(email)', 'Email must be unique for each staff member!'),
    ]

    # ===== حقول إضافية =====
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

    # ===== خاص بالطبيب =====
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

    # ===== Staff ID =====
    staff_id = fields.Char(
        string="Staff ID",
        required=True,
        copy=False,
        readonly=True,
        default='NEW'
    )

    # ===== توليد Staff ID عند الإنشاء + إنشاء يوزر تلقائي =====
    @api.model
    def create(self, vals):
        if not vals.get('email'):
            raise ValidationError(_("Email is required for staff and must be unique."))
        vals = self._update_staff_id(vals)
        staff = super().create(vals)
        staff._create_user_from_staff()
        return staff

    # ===== تعديل job_title يحدث Staff ID + الجروب =====
    def write(self, vals):
        if 'job_title' in vals:
            for rec in self:
                updated_vals = rec._update_staff_id(vals.copy())
                super(HospitalStaff, rec).write(updated_vals)
                rec._update_user_groups()
            return True
        return super().write(vals)

    # ===== توليد Staff ID =====
    def _update_staff_id(self, vals):
        if not isinstance(vals, dict):
            vals = {}

        job_title = vals.get('job_title')
        if not job_title:
            return vals

        code_map = {
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
            seq_obj = self.env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
            if seq_obj:
                vals['staff_id'] = seq_obj.next_by_id() or 'NEW'
        return vals

    # ===== إنشاء يوزر تلقائي للموظف =====
    def _create_user_from_staff(self):
        self.ensure_one()
        if not self.user_id:
            if not self.email:
                raise ValidationError(_("Email must be provided by the admin to create a user."))

            # Mapping job_title -> groups
            group_map = {
                'doctor': 'the_healing_hms.group_hospital_doctor',
                'nurse': 'the_healing_hms.group_hospital_nurse',
                'receptionist': 'the_healing_hms.group_hospital_receptionist',
                'accountant': 'the_healing_hms.group_hospital_accountant',
                'pharmacist': 'the_healing_hms.group_hospital_pharmacist',
                'ambulance': 'the_healing_hms.group_hospital_driver',
                'lab': 'the_healing_hms.group_hospital_lab',
            }

            groups = [self.env.ref('base.group_user').id]  # Internal User by default

            group_xml_id = group_map.get(self.job_title)
            if group_xml_id:
                try:
                    groups.append(self.env.ref(group_xml_id).id)
                except ValueError:
                    pass

            default_password = "1234"  # كلمة السر الافتراضية

            user_vals = {
                'name': self.name,
                'login': self.email,
                'email': self.email,
                'phone': self.phone,
                'groups_id': [(6, 0, groups)],
                'password': default_password,  # تعيين كلمة سر افتراضية
            }

            user = self.env['res.users'].sudo().create(user_vals)
            self.user_id = user.id

            # إرسال إيميل بكلمة السر
            mail_values = {
                'subject': _("Welcome to Hospital System"),
                'body_html': _(
                    "<p>Hello <b>%s</b>,</p>"
                    "<p>Your account has been created in the Hospital Management System.</p>"
                    "<p><b>Login:</b> %s</p>"
                    "<p><b>Password:</b> %s</p>"
                    "<p>Please login and change your password immediately.</p>"
                ) % (self.name, self.email, default_password),
                'email_to': self.email,
                'email_from': self.env.user.email or 'admin@example.com',
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

    # ===== تحديث جروبات اليوزر إذا تغيرت الوظيفة =====
    def _update_user_groups(self):
        self.ensure_one()
        if self.user_id:
            group_map = {
                'doctor': 'the_healing_hms.group_hospital_doctor',
                'nurse': 'the_healing_hms.group_hospital_nurse',
                'receptionist': 'the_healing_hms.group_hospital_receptionist',
                'accountant': 'the_healing_hms.group_hospital_accountant',
                'pharmacist': 'the_healing_hms.group_hospital_pharmacist',
                'ambulance': 'the_healing_hms.group_hospital_driver',
                'lab': 'the_healing_hms.group_hospital_lab',
            }

            groups = [self.env.ref('base.group_user').id]  # Always internal user

            group_xml_id = group_map.get(self.job_title)
            if group_xml_id:
                try:
                    groups.append(self.env.ref(group_xml_id).id)
                except ValueError:
                    pass

            self.user_id.sudo().write({'groups_id': [(6, 0, groups)]})
