from odoo import models, fields, api, _
from odoo.exceptions import UserError

# ---------------- Hospital Billing ----------------
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
    doctor_id = fields.Many2one('hospital.staff', string='Doctor', domain="[('job_title','=','doctor')]", tracking=True)
    booking_id = fields.Many2one('hospital.booking', string="Room Booking")  # ربط الحجز
    date = fields.Datetime(string='Bill Date', default=fields.Datetime.now, tracking=True)
    has_insurance = fields.Boolean(string="Has Insurance?", related='patient_id.has_insurance', readonly=True)
    insurance_company_id = fields.Many2one('hospital.insurance', string="Insurance Company")
    insurance_discount = fields.Float(string="Insurance (%)")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id.id)
    line_ids = fields.One2many('hospital.billing.line', 'billing_id', string='Bill Lines', copy=True)
    amount_untaxed = fields.Monetary(string='Untaxed Amount', compute='_compute_amounts', store=True)
    amount_tax = fields.Monetary(string='Taxes', compute='_compute_amounts', store=True)
    amount_discount = fields.Monetary(string="Insurance Discount", compute='_compute_amounts', store=True, readonly=True)
    amount_total = fields.Monetary(string='Total', compute='_compute_amounts', store=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('paid', 'Paid'), ('cancelled', 'Cancelled')], default='draft', tracking=True)
    payment_method = fields.Selection([('cash', 'Cash'), ('card', 'Card'), ('transfer', 'Bank Transfer'), ('insurance', 'Insurance')], string='Payment Method')
    payment_date = fields.Datetime(string='Payment Date')
    notes = fields.Text(string='Notes')

    @api.depends('line_ids.price_unit', 'line_ids.quantity', 'line_ids.tax_ids', 'insurance_discount')
    def _compute_amounts(self):
        for bill in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            for line in bill.line_ids:
                if line.tax_ids:
                    taxes_res = line.tax_ids.compute_all(line.price_unit, currency=bill.currency_id, quantity=line.quantity)
                    amount_untaxed += taxes_res['total_excluded']
                    amount_tax += taxes_res['total_included'] - taxes_res['total_excluded']
                else:
                    amount_untaxed += (line.price_unit or 0.0) * (line.quantity or 0.0)
            discount = (amount_untaxed * bill.insurance_discount / 100.0) if bill.insurance_discount else 0.0
            bill.amount_untaxed = amount_untaxed
            bill.amount_tax = amount_tax
            bill.amount_discount = discount
            bill.amount_total = (amount_untaxed - discount) + amount_tax

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

    @api.onchange('patient_id')
    def _onchange_patient_id(self):
        if self.patient_id and self.patient_id.has_insurance:
            self.insurance_company_id = self.patient_id.insurance_company
            self.insurance_discount = self.patient_id.insurance_discount
        else:
            self.insurance_company_id = False
            self.insurance_discount = 0.0

    @api.onchange('payment_method')
    def _onchange_payment_method(self):
        if self.payment_method == 'insurance' and not self.patient_id.has_insurance:
            self.payment_method = False
            return {'warning': {'title': "Warning", 'message': "This patient does not have insurance!"}}


# ---------------- Hospital Billing Line ----------------
class HospitalBillingLine(models.Model):
    _name = 'hospital.billing.line'
    _description = 'Hospital Billing Line'
    _order = 'id asc'

    billing_id = fields.Many2one('hospital.billing', string='Bill', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Service / Product', domain=[('sale_ok', '=', True)])
    medicine_id = fields.Many2one('hospital.medicine', string='Medicine')
    name = fields.Char(string='Description')
    quantity = fields.Float(string='Qty', default=1.0)
    price_unit = fields.Monetary(string='Unit Price')
    currency_id = fields.Many2one(related='billing_id.currency_id', store=True, readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', domain=[('type_tax_use', '=', 'sale')])
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_subtotal', store=True)
    lab_request_id = fields.Many2one('hospital.lab.request', string='Lab Request')

    @api.depends('price_unit', 'quantity', 'tax_ids')
    def _compute_subtotal(self):
        for line in self:
            if line.tax_ids:
                taxes_res = line.tax_ids.compute_all(line.price_unit, currency=line.currency_id, quantity=line.quantity)
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

    @api.onchange('medicine_id')
    def _onchange_medicine_id(self):
        for line in self:
            if line.medicine_id:
                line.name = line.medicine_id.name
                line.price_unit = line.medicine_id.price_unit

    def create(self, vals):
        res = super().create(vals)
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return res

    def write(self, vals):
        res = super().write(vals)
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return res