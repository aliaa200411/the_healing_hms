from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

class HospitalBooking(models.Model):
    _name = 'hospital.booking'
    _description = 'Hospital Room Booking'
    _order = 'date_from desc, id desc'

    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 related='patient_id.partner_id', store=True, readonly=True)

    department_id = fields.Many2one('hospital.department', string="Department", required=True)
    room_id = fields.Many2one('hospital.room', string="Room", required=True)
    bed_id = fields.Many2one('hospital.bed', string="Bed",
                             domain="[('room_id', '=', room_id)]")

    room_type = fields.Selection(
        selection=[('single', 'Single'), ('double', 'Double'), ('ward', 'Ward')],
        string="Room Type",
        related='room_id.room_type',
        store=True,
        readonly=True,
    )

    date_from = fields.Datetime(string="Check In", required=True)
    date_to = fields.Datetime(string="Check Out", required=True)

    days = fields.Integer(string="Days", compute='_compute_days_and_price', store=True, readonly=True)
    daily_price = fields.Float(string="Daily Price", compute='_compute_daily_price', store=True, readonly=True)
    price = fields.Float(string="Total Price", compute='_compute_days_and_price', store=True, readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
    ], string="Status", default='draft', tracking=True)

    notes = fields.Text(string="Notes")

    # ----------------------------
    #  Computing
    # ----------------------------

    @api.depends('room_id', 'room_type')
    def _compute_daily_price(self):
        """يجلب سعر اليوم من سجل الغرفة. يفترض وجود حقل price_per_day على الغرفة.
        وإن لم يوجد، نستخدم تسعير افتراضي حسب النوع."""
        for rec in self:
            price = 0.0
            if rec.room_id and hasattr(rec.room_id, 'price_per_day') and rec.room_id.price_per_day:
                price = rec.room_id.price_per_day
            else:
              
                mapping = {
                    'single': 100.0,
                    'double': 70.0,
                    'ward': 50.0,
                }
                price = mapping.get(rec.room_type or 'ward', 50.0)
            rec.daily_price = price

    @api.depends('date_from', 'date_to', 'daily_price')
    def _compute_days_and_price(self):
        for rec in self:
            d = 0
            if rec.date_from and rec.date_to:
                if rec.date_to <= rec.date_from:
                    rec.days = 0
                    rec.price = 0.0
                    continue
                delta = rec.date_to - rec.date_from
              
                seconds = delta.total_seconds()
                d = int(seconds // 86400)
                if seconds % 86400 != 0:
                    d += 1
                if d <= 0:
                    d = 1
            rec.days = d
            rec.price = rec.daily_price * d if d > 0 else 0.0

    # ----------------------------
    #  Constraints & Onchanges
    # ----------------------------

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to <= rec.date_from:
                raise ValidationError(_("Check Out must be after Check In."))

    @api.onchange('room_id')
    def _onchange_room(self):
        for rec in self:
            if rec.bed_id and rec.bed_id.room_id != rec.room_id:
                rec.bed_id = False

    @api.constrains('room_id', 'bed_id', 'date_from', 'date_to', 'state')
    def _check_room_availability(self):
        for rec in self:
            if not rec.room_id or not rec.date_from or not rec.date_to:
                continue

            def overlaps(other):
                return (other.date_from <= rec.date_to) and (other.date_to >= rec.date_from)

            if rec.bed_id:
                conflict = self.search_count([
                    ('id', '!=', rec.id),
                    ('state', 'in', ['confirmed', 'invoiced']),
                    ('bed_id', '=', rec.bed_id.id),
                    ('date_from', '<=', rec.date_to),
                    ('date_to', '>=', rec.date_from),
                ])
                if conflict:
                    raise ValidationError(_("This bed is already booked for the selected period."))

            total_beds = len(rec.room_id.bed_ids) or 0
            if total_beds <= 0:
                raise ValidationError(_("Selected room has no beds defined."))

            booked_beds = 0
            for bed in rec.room_id.bed_ids:
                has_overlap = self.search_count([
                    ('id', '!=', rec.id),
                    ('state', 'in', ['confirmed', 'invoiced']),
                    ('bed_id', '=', bed.id),
                    ('date_from', '<=', rec.date_to),
                    ('date_to', '>=', rec.date_from),
                ])
                if has_overlap:
                    booked_beds += 1

            if rec.bed_id:
                already = self.search_count([
                    ('id', '!=', rec.id),
                    ('state', 'in', ['confirmed', 'invoiced']),
                    ('bed_id', '=', rec.bed_id.id),
                    ('date_from', '<=', rec.date_to),
                    ('date_to', '>=', rec.date_from),
                ]) > 0
                if not already:
                    booked_beds += 1

            if booked_beds >= total_beds:
                raise ValidationError(_("Cannot book this room: all beds are already booked for the selected period."))

    # ----------------------------
    #  تحديث حالة الغرفة
    # ----------------------------

    def _update_room_state_for_period(self, room, date_from, date_to):
        """يحدّث حالة الغرفة بالنسبة لنفس فترة هذا الحجز:
           - unavailable إذا امتلأت الأسرة طوال الفترة
           - occupied إذا في حجوزات لكن لسه في سرير فاضي
           - available إذا ما في حجوزات
        """
        if not room or not date_from or not date_to:
            return
        total_beds = len(room.bed_ids) or 0
        if total_beds <= 0:
            room.state = 'available'
            return

        Booking = self.env['hospital.booking']
        occupied_beds = 0
        for bed in room.bed_ids:
            overlap_count = Booking.search_count([
                ('state', 'in', ['confirmed', 'invoiced']),
                ('bed_id', '=', bed.id),
                ('date_from', '<=', date_to),
                ('date_to', '>=', date_from),
            ])
            if overlap_count:
                occupied_beds += 1

        if occupied_beds >= total_beds:
            room.state = 'unavailable'
        elif occupied_beds > 0:
            room.state = 'occupied'
        else:
            room.state = 'available'

    # ----------------------------
    #  أزرار الإجراءات
    # ----------------------------

    def action_draft(self):
        self.write({'state': 'draft'})
        for rec in self:
            if rec.room_id:
                self._update_room_state_for_period(rec.room_id, rec.date_from, rec.date_to)

    def action_confirm(self):
        self.write({'state': 'confirmed'})
        for rec in self:
            if rec.room_id:
                self._update_room_state_for_period(rec.room_id, rec.date_from, rec.date_to)

    def action_create_invoice(self):
        """إنشاء فاتورة وتحويل الحالة إلى invoiced ثم تحديث حالة الغرفة."""
        for booking in self:
            if not booking.partner_id:
                raise ValidationError(_("The patient must be linked to a Customer to create an invoice."))
            if booking.days <= 0 or booking.price <= 0:
                raise ValidationError(_("Invalid booking duration or price."))

            # بند الفاتورة
            line_name = _("Room %(room)s (%(rtype)s) for %(patient)s - %(days)d day(s)") % {
                'room': getattr(booking.room_id, 'room_number', booking.room_id.display_name),
                'rtype': dict(self._fields['room_type'].selection).get(booking.room_type, 'N/A'),
                'patient': booking.patient_id.name,
                'days': booking.days,
            }

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': booking.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': line_name,
                    'quantity': booking.days,
                    'price_unit': booking.daily_price,
                })],
            })

            booking.write({'state': 'invoiced'})

            if booking.room_id:
                self._update_room_state_for_period(booking.room_id, booking.date_from, booking.date_to)

            return {
                'type': 'ir.actions.act_window',
                'name': _('Invoice'),
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice.id,
            }