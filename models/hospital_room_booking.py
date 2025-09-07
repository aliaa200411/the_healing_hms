from odoo import models, fields, api
from odoo.exceptions import ValidationError

class HospitalBooking(models.Model):
    _name = 'hospital.booking'
    _description = 'Hospital Room Booking'

    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer", related='patient_id.partner_id', store=True, readonly=True)

    department_id = fields.Many2one('hospital.department', string="Department", required=True)
    room_id = fields.Many2one('hospital.room', string="Room", required=True)
    bed_id = fields.Many2one('hospital.bed', string="Bed")
    room_type = fields.Selection([
        ('general', 'General'),
        ('vip', 'VIP'),
        ('icu', 'ICU')
    ], string="Room Type")

    date_from = fields.Datetime(string="From", required=True)
    date_to = fields.Datetime(string="To", required=True)

    days = fields.Integer(string="Days", readonly=True)
    price = fields.Float(string="Total Price", readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft')

    notes = fields.Text(string="Notes")

    @api.onchange('date_from', 'date_to', 'room_id')
    def _onchange_price(self):
        for rec in self:
            rec.price = 0.0
            if not rec.room_id:
                rec.days = 0
                continue
            price_per_day = getattr(rec.room_id, 'price_per_day', 15)
            if rec.date_from and rec.date_to:
                delta = rec.date_to - rec.date_from
                rec.days = delta.days + (1 if delta.seconds > 0 else 0)
            else:
                rec.days = 0
            rec.price = rec.days * price_per_day

    @api.constrains('days')
    def _check_days(self):
        for rec in self:
            if rec.days is None or rec.days <= 0:
                raise ValidationError("Please enter a positive number of days.")

    def _update_room_state(self, room):
        total_beds = len(room.bed_ids)
        booked_beds = len(room.bed_ids.filtered(
            lambda b: any(booking.state in ['confirmed', 'invoiced'] for booking in b.booking_ids)
        ))
        if booked_beds >= total_beds:
            room.state = 'unavailable'
        elif booked_beds > 0:
            room.state = 'occupied'
        else:
            room.state = 'available'

    def _update_dashboard(self):
        for rec in self:
            if rec.room_id and rec.room_id.department_id:
                self.env['hospital.room.dashboard'].update_room_dashboard(rec.room_id.department_id)

    def create(self, vals):
        rec = super().create(vals)
        if rec.room_id:
            self._update_room_state(rec.room_id)
        rec._update_dashboard()
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if rec.room_id:
                self._update_room_state(rec.room_id)
        self._update_dashboard()
        return res

    def unlink(self):
        self._update_dashboard()
        return super().unlink()

    def action_draft(self):
        self.write({'state': 'draft'})
        for rec in self:
            if rec.room_id:
                self._update_room_state(rec.room_id)
        self._update_dashboard()

    def action_confirm(self):
        self.write({'state': 'confirmed'})
        for rec in self:
            if rec.room_id:
                self._update_room_state(rec.room_id)
        self._update_dashboard()

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        for rec in self:
            if rec.room_id:
                self._update_room_state(rec.room_id)
        self._update_dashboard()

    def action_create_invoice(self):
        for booking in self:
            if not booking.partner_id:
                partner = self.env['res.partner'].create({'name': booking.patient_id.name})
                booking.patient_id.partner_id = partner
                booking.partner_id = partner

            billing = self.env['hospital.billing'].search([
                ('patient_id', '=', booking.patient_id.id),
                ('state', '=', 'draft')
            ], limit=1)

            if not billing:
                billing = self.env['hospital.billing'].create({
                    'patient_id': booking.patient_id.id,
                    'doctor_id': False,
                    'booking_id': booking.id,
                })

            self.env['hospital.billing.line'].create({
                'billing_id': billing.id,
                'name': f"Room {booking.room_id.room_number} Booking for {booking.patient_id.name}",
                'quantity': 1,
                'price_unit': booking.price,
            })

            booking.state = 'invoiced'

        return {
            'type': 'ir.actions.act_window',
            'name': 'Billing',
            'res_model': 'hospital.billing',
            'view_mode': 'form',
            'res_id': billing.id,
        }
