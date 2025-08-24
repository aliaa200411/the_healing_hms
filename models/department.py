# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalDepartment(models.Model):
    _name = 'hospital.department'
    _description = 'Hospital Department'
    _order = 'sequence, name'

    sequence = fields.Char(string="Serial Number", store=True, readonly=True)

    name = fields.Char(string="Department Name", required=True)
    description = fields.Text(string="Description")
    head_doctor_id = fields.Many2one('hospital.doctor', string="Head Doctor")
    doctor_ids = fields.One2many('hospital.doctor', 'department_id', string="Doctors")
    phone = fields.Char(string="Phone", size=20)
    floor = fields.Char(string="Floor")
    wing = fields.Char(string="Wing")

    doctor_count = fields.Integer(string="Number of Doctors", compute='_compute_doctor_count', store=True)
    room_count = fields.Integer(string="Number of Rooms", compute='_compute_room_count', store=True)
    total_capacity = fields.Integer(string="Total Capacity", compute='_compute_total_capacity', store=True)
    head_doctor_phone = fields.Char(string="Head Doctor Phone", compute='_compute_head_doctor_phone', store=True)

    room_ids = fields.One2many('hospital.room', 'department_id', string="Rooms")

    @api.depends('doctor_ids')
    def _compute_doctor_count(self):
        for rec in self:
            rec.doctor_count = len(rec.doctor_ids)

    @api.depends('head_doctor_id')
    def _compute_head_doctor_phone(self):
        for rec in self:
            rec.head_doctor_phone = rec.head_doctor_id.phone if rec.head_doctor_id else ''

    @api.depends('room_ids')
    def _compute_room_count(self):
        for rec in self:
            rec.room_count = len(rec.room_ids)

    @api.depends('room_ids.capacity')
    def _compute_total_capacity(self):
        for rec in self:
            rec.total_capacity = sum(room.capacity for room in rec.room_ids)

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('hospital.department') or 'New'
        return super().create(vals)

    def action_open_doctors(self):
        self.ensure_one()
        return {
            'name': 'Doctors',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.doctor',
            'view_mode': 'list,form',
            'views': [(self.env.ref('hospital_departments.view_hospital_doctor_list').id, 'list'),
                      (self.env.ref('hospital_departments.view_hospital_doctor_form').id, 'form')],
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }

    def action_open_rooms(self):
        self.ensure_one()
        return {
            'name': 'Rooms',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.room',
            'view_mode': 'list,form',
            'views': [(self.env.ref('hospital_departments.view_hospital_room_list').id, 'list'),
                      (self.env.ref('hospital_departments.view_hospital_room_form').id, 'form')],
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }
