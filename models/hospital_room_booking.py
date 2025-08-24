# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HospitalBooking(models.Model):
    _name = 'hospital.booking'
    _description = 'Hospital Room Booking'

    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer", related='patient_id.partner_id', store=True, readonly=True)

    department_id = fields.Many2one('hospital.department', string="Department", required=True)
    room_id = fields.Many2one('hospital.room', string="Room", required=True)
    bed_id = fields.Many2one('hospital.bed', string="Bed")

    date_from = fields.Datetime(string="From", required=True)
    date_to = fields.Datetime(string="To", required=True)

    price_type = fields.Selection([
        ('hour', 'Per Hour'),
        ('day', 'Per Day')
    ], string="Price Type", required=True, default='hour')
    hours = fields.Float(string="Hours")
    days = fields.Integer(string="Days")
    price = fields.Float(string="Total Price", readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft')

    notes = fields.Text(string="Notes")

    @api.onchange('price_type', 'hours', 'days', 'date_from', 'date_to', 'room_id')
    def _onchange_price(self):
        for rec in self:
            rec.price = 0.0
            if not rec.room_id:
                continue

            price_per_hour = getattr(rec.room_id, 'price_per_hour', 1)
            price_per_day = getattr(rec.room_id, 'price_per_day', 15)

            if rec.date_from and rec.date_to:
                delta = rec.date_to - rec.date_from
                duration_hours = delta.total_seconds() / 3600
                duration_days = delta.days + (1 if delta.seconds > 0 else 0)
            else:
                duration_hours = rec.hours or 0
                duration_days = rec.days or 0

            if rec.price_type == 'hour':
                rec.hours = rec.hours or duration_hours
                rec.price = rec.hours * price_per_hour
            else:
                rec.days = rec.days or duration_days
                rec.price = rec.days * price_per_day

    @api.constrains('price_type', 'hours', 'days')
    def _check_qty_by_type(self):
        for rec in self:
            if rec.price_type == 'hour' and (rec.hours is None or rec.hours <= 0):
                raise ValidationError("Please enter a positive number of hours.")
            if rec.price_type == 'day' and (rec.days is None or rec.days <= 0):
                raise ValidationError("Please enter a positive number of days.")

    def _update_room_state(self, room):
        total_beds = len(room.bed_ids)
        booked_beds = len(room.bed_ids.filtered(
            lambda b: any(booking.state in ['confirmed', 'done'] for booking in b.booking_ids)
        ))
        if booked_beds >= total_beds:
            room.state = 'unavailable'
        elif booked_beds > 0:
            room.state = 'occupied'
        else:
            room.state = 'available'

    def action_draft(self):
        self.write({'state': 'draft'})
        for rec in self:
            if rec.room_id:
                self._update_room_state(rec.room_id)

    def action_confirm(self):
        self.write({'state': 'confirmed'})
        for rec in self:
            if rec.room_id:
                self._update_room_state(rec.room_id)

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        for rec in self:
            if rec.room_id:
                self._update_room_state(rec.room_id)

    def action_create_invoice(self):
        for booking in self:
            if not booking.partner_id:
                raise ValidationError(_("The patient must be linked to a Customer to create an invoice."))

            quantity = booking.hours if booking.price_type == 'hour' else booking.days
            price_unit = getattr(booking.room_id, 'price_per_hour', 1) if booking.price_type == 'hour' else getattr(booking.room_id, 'price_per_day', 15)

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': booking.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': f"Room {booking.room_id.room_number} Booking for {booking.patient_id.name}",
                    'quantity': quantity,
                    'price_unit': price_unit,
                })],
            })
            booking.write({'state': 'invoiced'})

        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }