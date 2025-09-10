# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class HospitalDepartmentDashboard(models.Model):
    _name = 'hospital.department.dashboard'
    _description = 'Hospital Department Dashboard'
    _rec_name = 'department_id'
    _order = 'department_id'

    # ===== Department =====
    department_id = fields.Many2one('hospital.department', string="Department", required=True, readonly=True)

    # ===== KPIs =====
    total_doctors = fields.Integer(string="Total Doctors", compute='_compute_kpis', store=True)
    total_rooms = fields.Integer(string="Total Rooms", compute='_compute_kpis', store=True)
    total_capacity = fields.Integer(string="Total Capacity", compute='_compute_kpis', store=True)
    month = fields.Char(string="Month", compute='_compute_kpis')

    # ===== Rooms =====
    occupied_rooms = fields.Integer(string="Occupied Rooms", compute='_compute_kpis', store=True)
    available_rooms = fields.Integer(string="Available Rooms", compute='_compute_kpis', store=True)

    # ===== Doctors =====
    doctor_available = fields.Integer(string="Available Doctors", compute='_compute_kpis', store=True)
    doctor_busy = fields.Integer(string="Busy Doctors", compute='_compute_kpis', store=True)

    # ================== Compute KPIs ==================
    @api.depends('department_id.doctor_ids', 'department_id.room_ids', 'department_id.total_capacity')
    def _compute_kpis(self):
        for rec in self:
            dep = rec.department_id
            if dep:
                doctors = [d for d in dep.doctor_ids if d.job_title == 'doctor']
                total_doctors = len(doctors)
                total_rooms = len(dep.room_ids)
                occupied_rooms = len([r for r in dep.room_ids if r.state == 'occupied'])
                available_rooms = total_rooms - occupied_rooms
                doctor_available = len([d for d in doctors if d.is_available])
                doctor_busy = total_doctors - doctor_available
                month_label = datetime.today().strftime("%B %Y")

                rec.total_doctors = total_doctors
                rec.total_rooms = total_rooms
                rec.total_capacity = dep.total_capacity
                rec.occupied_rooms = occupied_rooms
                rec.available_rooms = available_rooms
                rec.doctor_available = doctor_available
                rec.doctor_busy = doctor_busy
                rec.month = month_label

    # ================== Update Dashboard ==================
    @api.model
    def update_department_dashboard(self, department):
        """
        تنشئ أو تحدّث سجل الداشبورد بناءً على بيانات الديبارتمنت
        """
        dashboard = self.search([('department_id', '=', department.id)], limit=1)
        if not dashboard:
            dashboard = self.create({'department_id': department.id})
        else:
            # إعادة حساب الحقول المحسوبة
            dashboard._compute_kpis()
        return dashboard