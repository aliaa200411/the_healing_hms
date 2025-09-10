# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class BloodBag(models.Model):
    _name = 'blood.bank.bag'
    _description = 'Blood Bag'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expiry_date, name'

    # ===== المرجع التلقائي للكيس =====
    name = fields.Char(
        string='Bag Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('blood.bank.bag') or _('New')
    )

    # ===== نوع الدم وRH =====
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

    # ===== المتبرع =====
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

    # ===== تاريخ انتهاء الصلاحية محسوب تلقائيًا =====
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

    # ===== حالة الكيس: متاح، منتهي، مستخدم =====
    status = fields.Selection(
        [
            ('available', 'Available'),
            ('expired', 'Expired'),
            ('used', 'Used'),
        ],
        string='Status',
        default='available',
        tracking=True,
    )

    notes = fields.Text(string='Notes')

    # ===== الأيام المتبقية للصلاحية =====
    days_left = fields.Integer(
        string='Days Left',
        compute='_compute_days_left',
        store=True,
        help='Number of days until expiry (negative if already expired).'
    )

    # ===== العلاقة مع عملية نقل الدم =====
    transfusion_id = fields.Many2one(
        'blood.bank.transfusion',
        string='Used in Transfusion',
        readonly=True,
        copy=False,
    )

    # ===== الحسابات =====
    @api.depends('donation_date')
    def _compute_expiry_date(self):
        for rec in self:
            rec.expiry_date = rec.donation_date + timedelta(days=35) if rec.donation_date else False

    @api.depends('expiry_date')
    def _compute_days_left(self):
        today = fields.Date.context_today(self)
        for rec in self:
            rec.days_left = (rec.expiry_date - today).days if rec.expiry_date else 0

    # ===== التحقق من الحالة عند التغيير =====
    @api.onchange('donation_date', 'expiry_date')
    def _onchange_update_status(self):
        for rec in self:
            if rec.expiry_date and rec.days_left < 0:
                rec.status = 'expired'
            elif rec.status == 'expired' and rec.days_left >= 0:
                rec.status = 'available'

    # ===== وظائف أكشن =====
    def action_mark_used(self, transfusion=None):
        for rec in self:
            if rec.status != 'available':
                raise ValidationError(_('Only available bags can be marked as used. (Bag %s)') % rec.name)
            rec.status = 'used'
            if transfusion:
                rec.transfusion_id = transfusion.id
        self._update_dashboard()
        return True

    # ===== طريقة عرض الاسم =====
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

    # ===== إنشاء سجل =====
    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._onchange_update_status()
        if record.transfusion_id and record.status == 'available':
            record.status = 'used'
        record._update_dashboard()
        return record

    # ===== تعديل سجل =====
    def write(self, vals):
        res = super().write(vals)
        self._onchange_update_status()
        for rec in self:
            if vals.get('transfusion_id') and rec.status == 'available' and rec.transfusion_id:
                rec.status = 'used'
        self._update_dashboard()
        return res

    # ===== تحديث داشبورد بنك الدم =====
    def _update_dashboard(self):
        dashboard_model = self.env['blood.bank.dashboard']
        dashboard = dashboard_model.sudo().search([], limit=1)
        if not dashboard:
            dashboard = dashboard_model.sudo().create({'name': 'Blood Bank Overview'})
        dashboard._compute_kpis()
        dashboard._compute_blood_type_percent()