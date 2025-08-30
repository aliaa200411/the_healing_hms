# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class BloodBag(models.Model):
    _name = 'blood.bank.bag'
    _description = 'Blood Bag'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date, name'

    name = fields.Char(
        string='Bag Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('blood.bank.bag') or _('New')
    )
    blood_type = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')],
        string='Blood Type',
        required=True,
        tracking=True,
    )
    rh = fields.Selection(
        [('+', '+'), ('-', '-')],
        string='Rh',
        required=True,
        default='+',
        tracking=True,
    )
    donor_id = fields.Many2one(
        'res.partner',
        string="Donor's Name",
        ondelete='set null',
    )
    donation_date = fields.Date(
        string='Donation Date',
        required=True,
        default=fields.Date.context_today,
    )
    expiry_date = fields.Date(
        string='Expiry Date',
        compute='_compute_expiry_date',
        store=True,
        readonly=True,
    )
    units = fields.Float(
        string='Units (ml)',
        default=450.0,
    )
    status = fields.Selection(
        [
            ('available', 'Available'),
            ('reserved', 'Reserved'),
            ('used', 'Used'),
            ('expired', 'Expired'),
            ('quarantined', 'Quarantined'),
        ],
        string='Status',
        default='available',
        tracking=True,
    )
    notes = fields.Text(string='Notes')

    days_left = fields.Integer(
        string='Days Left',
        compute='_compute_days_left',
        store=True,
        help='Number of days until expiry (negative if already expired).'
    )

    reserved_for = fields.Many2one(
        'blood.bank.transfusion',
        string='Reserved For',
        readonly=True,
        copy=False,
    )

    # ---------- Computed fields ----------
    @api.depends('donation_date')
    def _compute_expiry_date(self):
        """ expiry_date = donation_date + 35 days """
        for rec in self:
            if rec.donation_date:
                rec.expiry_date = rec.donation_date + timedelta(days=35)
            else:
                rec.expiry_date = False

    @api.depends('expiry_date')
    def _compute_days_left(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.expiry_date:
                rec.days_left = (rec.expiry_date - today).days
            else:
                rec.days_left = 0

    @api.onchange('donation_date', 'expiry_date')
    def _onchange_update_status(self):
        for rec in self:
            if rec.expiry_date and rec.days_left < 0:
                rec.status = 'expired'
            elif rec.status == 'expired' and rec.days_left >= 0:
                rec.status = 'available'

    # ---------- Actions ----------
    def action_reserve(self, transfusion=None):
        for rec in self:
            if rec.status != 'available':
                raise ValidationError(_('Only available bags can be reserved. (Bag %s)') % rec.name)
            rec.status = 'reserved'
            if transfusion:
                rec.reserved_for = transfusion.id
        return True

    def action_unreserve(self):
        for rec in self:
            if rec.status == 'reserved':
                rec.status = 'available'
                rec.reserved_for = False
        return True

    def action_mark_used(self):
        for rec in self:
            if rec.status not in ('available', 'reserved'):
                raise ValidationError(_('Only available or reserved bags can be marked as used. (Bag %s)') % rec.name)
            rec.status = 'used'
        return True

    def action_mark_expired(self):
        for rec in self:
            rec.status = 'expired'
        return True

    # ---------- Naming ----------
    def name_get(self):
        result = []
        for rec in self:
            display = rec.name
            if rec.blood_type and rec.rh:
                display += f" ({rec.blood_type}{rec.rh})"
            if rec.donor_id:
                display += f" - {rec.donor_id.name}"
            result.append((rec.id, display))
        return result

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._onchange_update_status()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._onchange_update_status()
        return res
