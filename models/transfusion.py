# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BloodTransfusion(models.Model):
    _name = 'blood.bank.transfusion'
    _description = 'Blood Transfusion Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Request Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('blood.bank.transfusion') or _('New'),
        tracking=True,
    )

    patient_id = fields.Many2one(
        'hospital.patient',
        string='Patient',
        required=True,
        tracking=True,
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

    request_status = fields.Selection(
        [
            ('waiting', 'Waiting for donor'),
            ('done', 'Transfused'),
        ],
        string="Request Status",
        default="waiting",
        tracking=True,
    )

    bag_id = fields.Many2one(
        'blood.bank.bag',
        string="Matched Blood Bag",
        domain="[('blood_type','=',blood_type), ('rh','=',rh), ('status','=','available')]",
        tracking=True,
    )

    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.name or rec.name in (None, '', 'New'):
                rec.name = self.env['ir.sequence'].next_by_code('blood.bank.transfusion') or 'New'
        return records

    @api.onchange('bag_id')
    def _onchange_bag_id(self):
        """When a blood bag is selected, mark it as used automatically."""
        for rec in self:
            if rec.bag_id:
                if rec.bag_id.status == 'available':
                    rec.bag_id.status = 'used'
                    rec.bag_id.transfusion_id = rec.id
                    rec.request_status = 'done'
            else:
                rec.request_status = 'waiting'

    def action_check_availability(self):
        """Check for available blood bags only."""
        Bag = self.env['blood.bank.bag']
        for rec in self:
            if rec.request_status == 'done':
                raise ValidationError(_("This request is already completed."))

            bag = Bag.search([
                ('blood_type', '=', rec.blood_type),
                ('rh', '=', rec.rh),
                ('status', '=', 'available'),
            ], limit=1, order='expiry_date asc')

            if bag:
                rec.bag_id = bag.id
                rec.request_status = 'waiting'
                rec.message_post(body=_("Blood bag %s is available for this request.") % bag.name)
            else:
                rec.bag_id = False
                rec.request_status = 'waiting'
                rec.message_post(body=_("No available blood bags for %s%s. Waiting for donor...") % (rec.blood_type, rec.rh))

    def action_mark_used(self):
        """Complete the transfusion and mark the bag as used."""
        for rec in self:
            if not rec.bag_id:
                raise ValidationError(_("Please select a blood bag before marking as done."))

            rec.bag_id.status = 'used'
            rec.bag_id.transfusion_id = rec.id
            rec.request_status = 'done'
            rec.message_post(body=_("Transfusion completed. Bag %s marked as used.") % rec.bag_id.name)

    def name_get(self):
        result = []
        for rec in self:
            display = rec.name or ''
            parts = []
            if rec.patient_id:
                parts.append(rec.patient_id.display_name)
            if rec.blood_type and rec.rh:
                parts.append("%s%s" % (rec.blood_type, rec.rh))
            if parts:
                display = "%s (%s)" % (display, ' - '.join(parts))
            result.append((rec.id, display))
        return result
