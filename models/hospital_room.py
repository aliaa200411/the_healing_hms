# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalRoom(models.Model):
    _name = 'hospital.room'
    _description = 'Hospital Room'
    _order = 'department_id, room_number'

    room_number = fields.Char(string="Room Number", required=True)
    department_id = fields.Many2one('hospital.department', string="Department", ondelete='cascade')
    floor = fields.Char(string="Floor")
    wing = fields.Char(string="Wing")

    room_type = fields.Selection([
        ('single', 'Single (1 Bed)'),
        ('double', 'Double (2 Beds)'),
        ('ward', 'Ward (7 Beds)'),
    ], string="Room Type", default='single', required=True)

    capacity = fields.Integer(
        string="Number of Beds",
        compute="_compute_capacity",
        store=True,
        readonly=True
    )

    state = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('unavailable', 'Unavailable')
    ], string="Status", default='available')

    bed_ids = fields.One2many('hospital.bed', 'room_id', string="Beds")
    available_beds = fields.Integer(string="Available Beds", compute="_compute_available_beds", store=True)

    @api.depends('room_type')
    def _compute_capacity(self):
        mapping = {'single': 1, 'double': 2, 'ward': 7}
        for room in self:
            room.capacity = mapping.get(room.room_type, 1)

    @api.depends('bed_ids.booking_ids.state')
    def _compute_available_beds(self):
        for room in self:
            total_beds = len(room.bed_ids)
            booked_beds = len(room.bed_ids.filtered(
                lambda b: any(booking.state in ['confirmed', 'done'] for booking in b.booking_ids)
            ))
            room.available_beds = total_beds - booked_beds
            room.state = 'occupied' if booked_beds == total_beds else 'available'

    def action_open_bookings(self):
        return {
            'name': 'Bookings',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.booking',
            'view_mode': 'tree,form',
            'domain': [('bed_id.room_id', '=', self.id)],
        }


class HospitalBed(models.Model):
    _name = 'hospital.bed'
    _description = 'Hospital Bed'
    _order = 'name'

    name = fields.Char(string="Bed Name", required=True)
    room_id = fields.Many2one('hospital.room', string="Room", required=True, ondelete='cascade')
    booking_ids = fields.One2many('hospital.booking', 'bed_id', string="Bookings")
    is_occupied = fields.Boolean(string="Occupied", compute="_compute_is_occupied")

    @api.depends('booking_ids.state')
    def _compute_is_occupied(self):
        for bed in self:
            bed.is_occupied = any(b.state == 'confirmed' for b in bed.booking_ids)