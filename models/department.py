# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalDepartment(models.Model):
    _name = 'hospital.department'
    _description = 'Hospital Department'
    _order = 'sequence, name'

    # ================== Fields ==================
    sequence = fields.Char(string="Serial Number", store=True, readonly=True)
    name = fields.Char(string="Department Name", required=True)
    description = fields.Text(string="Description")
    head_doctor_id = fields.Many2one(
    'hospital.staff', 
    string="Head Doctor", 
    domain=[('job_title', '=', 'doctor')]
)
    doctor_ids = fields.One2many(
    'hospital.staff', 
    'department_id', 
    string="Doctors", 
    domain=[('job_title', '=', 'doctor')]
)
    phone = fields.Char(string="Phone", size=20)
    floor = fields.Char(string="Floor")
    wing = fields.Char(string="Wing")

    room_ids = fields.One2many('hospital.room', 'department_id', string="Rooms")

    doctor_count = fields.Integer(string="Number of Doctors", compute='_compute_doctor_count', store=True)
    room_count = fields.Integer(string="Number of Rooms", compute='_compute_room_count', store=True)
    total_capacity = fields.Integer(string="Total Capacity", compute='_compute_total_capacity', store=True)

    # ================== Compute Methods ==================
    @api.depends('doctor_ids')
    def _compute_doctor_count(self):
        for rec in self:
            rec.doctor_count = len(rec.doctor_ids)

    @api.depends('room_ids')
    def _compute_room_count(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)

    @api.depends('room_ids.capacity')
    def _compute_total_capacity(self):
        for rec in self:
            rec.total_capacity = sum(room.capacity for room in rec.room_ids)

    # ================== Overrides ==================
    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('hospital.department') or 'New'
        rec = super().create(vals)
        # Update dashboard immediately
        self.env['hospital.department.dashboard'].with_context(from_department=True).update_department_dashboard(rec)
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            self.env['hospital.department.dashboard'].with_context(from_department=True).update_department_dashboard(rec)
        return res

    def unlink(self):
        for rec in self:
            # delete dashboard record without raising error
            dash = self.env['hospital.department.dashboard'].with_context(from_department=True).search([('department_id', '=', rec.id)])
            dash.unlink()
        return super().unlink()

    # ================== Action Buttons ==================
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
