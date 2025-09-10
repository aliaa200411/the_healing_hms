# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalRoomDashboard(models.Model):
    _name = 'hospital.room.dashboard'
    _description = 'Hospital Room Dashboard'

    department_id = fields.Many2one('hospital.department', string="Department")

    total_rooms = fields.Integer(string="Total Rooms", compute='_compute_kpis', store=True)
    available_rooms = fields.Integer(string="Available Rooms", compute='_compute_kpis', store=True)
    occupied_rooms = fields.Integer(string="Occupied Rooms", compute='_compute_kpis', store=True)

    total_beds = fields.Integer(string="Total Beds", compute='_compute_kpis', store=True)
    available_beds = fields.Integer(string="Available Beds", compute='_compute_kpis', store=True)
    occupied_beds = fields.Integer(string="Occupied Beds", compute='_compute_kpis', store=True)

    total_bookings = fields.Integer(string="Total Bookings", compute='_compute_kpis', store=True)
    confirmed_bookings = fields.Integer(string="Confirmed Bookings", compute='_compute_kpis', store=True)
    cancelled_bookings = fields.Integer(string="Cancelled Bookings", compute='_compute_kpis', store=True)

    @api.depends('department_id')
    def _compute_kpis(self):
        for rec in self:
            domain = [('department_id', '=', rec.department_id.id)] if rec.department_id else []

            rooms = self.env['hospital.room'].search(domain)
            beds = self.env['hospital.bed'].search([('room_id', 'in', rooms.ids)])
            bookings = self.env['hospital.booking'].search([('room_id', 'in', rooms.ids)])

            rec.total_rooms = len(rooms)
            rec.available_rooms = len(rooms.filtered(lambda r: r.state == 'available'))
            rec.occupied_rooms = len(rooms.filtered(lambda r: r.state == 'occupied'))

            rec.total_beds = len(beds)
            rec.occupied_beds = len(beds.filtered(lambda b: b.is_occupied))
            rec.available_beds = rec.total_beds - rec.occupied_beds

            rec.total_bookings = len(bookings)
            rec.confirmed_bookings = len(bookings.filtered(lambda b: b.state == 'confirmed'))
            rec.cancelled_bookings = len(bookings.filtered(lambda b: b.state == 'cancelled'))

    # ================== Auto-update dashboard ==================
    @api.model
    def update_room_dashboard(self, department=None):
        """
        Update or create dashboard record for a given department.
        """
        departments = [department] if department else self.env['hospital.department'].search([])
        for dep in departments:
            dash = self.search([('department_id', '=', dep.id)])
            if not dash:
                dash = self.create({'department_id': dep.id})
            else:
                dash._compute_kpis()

# ================== Hooks for room and booking models ==================
class HospitalRoom(models.Model):
    _inherit = 'hospital.room'

    def create(self, vals):
        res = super().create(vals)
        self.env['hospital.room.dashboard'].update_room_dashboard(res.department_id)
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            self.env['hospital.room.dashboard'].update_room_dashboard(rec.department_id)
        return res

    def unlink(self):
        for rec in self:
            self.env['hospital.room.dashboard'].update_room_dashboard(rec.department_id)
        return super().unlink()


class HospitalBooking(models.Model):
    _inherit = 'hospital.booking'

    def create(self, vals):
        res = super().create(vals)
        if res.room_id:
            self.env['hospital.room.dashboard'].update_room_dashboard(res.room_id.department_id)
        return res

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.room_id:
                self.env['hospital.room.dashboard'].update_room_dashboard(rec.room_id.department_id)
        return res

    def unlink(self):
        for rec in self:
            if rec.room_id:
                self.env['hospital.room.dashboard'].update_room_dashboard(rec.room_id.department_id)
        return super().unlink()