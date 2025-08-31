from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HospitalBilling(models.Model):
    _name = 'hospital.billing'
    _description = 'Hospital Patient Bill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Bill Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.billing') or _('New'),
        tracking=True
    )
    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True, tracking=True)
    doctor_id = fields.Many2one('hospital.doctor', string='Doctor', tracking=True)
    date = fields.Datetime(string='Bill Date', default=fields.Datetime.now, tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id
    )
    line_ids = fields.One2many('hospital.billing.line', 'billing_id', string='Bill Lines', copy=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Taxes', compute='_compute_amounts', store=True)
    amount_total = fields.Monetary(string='Total', compute='_compute_amounts', store=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('paid', 'Paid'),
         ('cancel', 'Cancelled')],
        default='draft', tracking=True
    )
    payment_method = fields.Selection(
        [('cash', 'Cash'),
         ('card', 'Card'),
         ('transfer', 'Bank Transfer'),
         ('insurance', 'Insurance')],
        string='Payment Method'
    )
    payment_date = fields.Datetime(string='Payment Date')
    notes = fields.Text(string='Notes')

    @api.depends('line_ids.price_unit', 'line_ids.quantity', 'line_ids.tax_ids')
    def _compute_amounts(self):
        Tax = self.env['account.tax']
        for bill in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            for line in bill.line_ids:
                if line.tax_ids:
                    taxes_res = Tax.browse(line.tax_ids.ids).compute_all(
                        line.price_unit,
                        currency=bill.currency_id,
                        quantity=line.quantity
                    )
                    line.price_subtotal = taxes_res['total_excluded']
                    amount_untaxed += taxes_res['total_excluded']
                    amount_tax += taxes_res['total_included'] - taxes_res['total_excluded']
                else:
                    subtotal = (line.price_unit or 0.0) * (line.quantity or 0.0)
                    line.price_subtotal = subtotal
                    amount_untaxed += subtotal
            bill.amount_untaxed = amount_untaxed
            bill.amount_tax = amount_tax
            bill.amount_total = amount_untaxed + amount_tax

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_("Add at least one line before confirming the bill."))
            rec.state = 'confirmed'

    def action_mark_paid(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_("Only confirmed bills can be marked as paid."))
            if not rec.payment_method:
                raise UserError(_("Please select a Payment Method first."))
            rec.payment_date = fields.Datetime.now()
            rec.state = 'paid'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.payment_date = False
            rec.payment_method = False

    def action_cancel(self):
        for rec in self:
            if rec.state == 'paid':
                raise UserError(_("You cannot cancel a paid bill."))
            rec.state = 'cancel'

    def print_report(self):
        return self.env.ref('the_healing_hms.hospital_billing_report_action').report_action(self)


class HospitalBillingLine(models.Model):
    _name = 'hospital.billing.line'
    _description = 'Hospital Billing Line'
    _order = 'id asc'

    billing_id = fields.Many2one('hospital.billing', string='Bill', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product',
        string='Service / Product',
        domain=[('sale_ok', '=', True)],
        required=True
    )
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Qty', default=1.0)
    price_unit = fields.Monetary(string='Unit Price')
    currency_id = fields.Many2one(related='billing_id.currency_id', store=True, readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', domain=[('type_tax_use', '=', 'sale')])
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('price_unit', 'quantity', 'tax_ids')
    def _compute_subtotal(self):
        Tax = self.env['account.tax']
        for line in self:
            if line.tax_ids:
                taxes_res = Tax.browse(line.tax_ids.ids).compute_all(
                    line.price_unit,
                    currency=line.billing_id.currency_id,
                    quantity=line.quantity
                )
                line.price_subtotal = taxes_res['total_excluded']
            else:
                line.price_subtotal = (line.price_unit or 0.0) * (line.quantity or 0.0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.name = line.product_id.display_name
                line.price_unit = line.product_id.list_price
                line.tax_ids = line.product_id.taxes_id
