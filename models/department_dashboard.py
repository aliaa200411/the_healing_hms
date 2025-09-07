# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

# ================== Department Dashboard ==================
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


# ================== Department ==================
class HospitalDepartment(models.Model):
    _name = 'hospital.department'
    _description = 'Hospital Department'
    _order = 'sequence, name'

    # ===== Basic Info =====
    sequence = fields.Char(string="Serial Number", store=True, readonly=True)
    name = fields.Char(string="Department Name", required=True)
    description = fields.Text(string="Description")
    head_doctor_id = fields.Many2one(
        'hospital.staff', 
        string="Head Doctor", 
        domain=[('job_title', '=', 'doctor')]
    )
    phone = fields.Char(string="Phone", size=20)
    floor = fields.Char(string="Floor")
    wing = fields.Char(string="Wing")

    # ===== Relations =====
    doctor_ids = fields.One2many(
        'hospital.staff', 
        'department_id', 
        string="Doctors", 
        domain=[('job_title', '=', 'doctor')]
    )
    room_ids = fields.One2many('hospital.room', 'department_id', string="Rooms")

    # ===== Computed Fields =====
    doctor_count = fields.Integer(string="Number of Doctors", compute='_compute_doctor_count', store=True)
    room_count = fields.Integer(string="Number of Rooms", compute='_compute_room_count', store=True)
    total_capacity = fields.Integer(string="Total Capacity", compute='_compute_total_capacity', store=True)

    @api.depends('doctor_ids')
    def _compute_doctor_count(self):
        for rec in self:
            rec.doctor_count = len([d for d in rec.doctor_ids if d.job_title == 'doctor'])

    @api.depends('room_ids')
    def _compute_room_count(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)

    @api.depends('room_ids.capacity')
    def _compute_total_capacity(self):
        for rec in self:
            rec.total_capacity = sum(room.capacity for room in rec.room_ids)

    # ===== Sequence & Dashboard Management =====
    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('hospital.department') or 'New'
        rec = super().create(vals)
        # Ensure dashboard exists for new department
        self.env['hospital.department.dashboard'].create({'department_id': rec.id})
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            dashboard = self.env['hospital.department.dashboard'].search([('department_id', '=', rec.id)], limit=1)
            if not dashboard:
                self.env['hospital.department.dashboard'].create({'department_id': rec.id})
        return res

    def unlink(self):
        for rec in self:
            dash = self.env['hospital.department.dashboard'].search([('department_id', '=', rec.id)])
            dash.unlink()
        return super().unlink()

    # ===== Footer Buttons =====
    def action_open_doctors(self):
        self.ensure_one()
        return {
            'name': 'Doctors',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.staff',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('the_healing_hms.view_hospital_doctor_list').id, 'list'),
                (self.env.ref('the_healing_hms.view_hospital_doctor_form').id, 'form')
            ],
            'domain': [('department_id', '=', self.id), ('job_title', '=', 'doctor')],
            'context': {'default_department_id': self.id},
        }

    def action_open_rooms(self):
        self.ensure_one()
        return {
            'name': 'Rooms',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.room',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('the_healing_hms.view_hospital_room_list').id, 'list'),
                (self.env.ref('the_healing_hms.view_hospital_room_form').id, 'form')
            ],
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }
