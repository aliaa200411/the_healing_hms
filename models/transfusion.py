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

    # ===== إنشاء سجل =====
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if not rec.name or rec.name in (None, '', 'New'):
                rec.name = self.env['ir.sequence'].next_by_code('blood.bank.transfusion') or 'New'
        rec._update_dashboard()
        return records

    # ===== عند اختيار كيس دم =====
    @api.onchange('bag_id')
    def _onchange_bag_id(self):
        for rec in self:
            if rec.bag_id:
                if rec.bag_id.status == 'available':
                    rec.bag_id.status = 'used'
                    rec.bag_id.transfusion_id = rec.id
                    rec.request_status = 'done'
                    rec._update_dashboard()
            else:
                rec.request_status = 'waiting'

    # ===== التحقق من توافر أكياس الدم =====
    def action_check_availability(self):
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
            rec._update_dashboard()

    # ===== اكتمال نقل الدم =====
    def action_mark_used(self):
        for rec in self:
            if not rec.bag_id:
                raise ValidationError(_("Please select a blood bag before marking as done."))

            rec.bag_id.status = 'used'
            rec.bag_id.transfusion_id = rec.id
            rec.request_status = 'done'
            rec.message_post(body=_("Transfusion completed. Bag %s marked as used.") % rec.bag_id.name)
            rec._update_dashboard()

    # ===== طريقة عرض الاسم =====
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

    # ===== تعديل سجل =====
    def write(self, vals):
        res = super().write(vals)
        self._update_dashboard()
        return res

    # ===== تحديث داشبورد بنك الدم =====
    def _update_dashboard(self):
        dashboard = self.env['blood.bank.dashboard'].sudo().search([], limit=1)
        if dashboard:
            dashboard._compute_kpis()
            dashboard._compute_blood_type_percent()
