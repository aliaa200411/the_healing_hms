from odoo import models, fields, api, _
from odoo.exceptions import UserError

# -----------------------------
# 1. تصنيفات الأدوية
# -----------------------------
class HospitalPharmacyCategory(models.Model):
    _name = 'hospital.pharmacy.category'
    _description = 'Medicine Category'
    _order = 'name'

    name = fields.Char(string="Category Name", required=True)
    description = fields.Text(string="Description")


# -----------------------------
# 2. معلومات الأدوية
# -----------------------------
class HospitalMedicine(models.Model):
    _name = 'hospital.medicine'
    _description = 'Hospital Medicine'
    _order = 'name'

    name = fields.Char(string="Medicine Name", required=True)
    code = fields.Char(
        string="Medicine Code",
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.medicine') or _('New')
    )
    category_id = fields.Many2one('hospital.pharmacy.category', string="Category")
    quantity_available = fields.Float(string="Quantity in Stock", default=0.0)
    price_unit = fields.Monetary(string="Unit Price", required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id
    )
    description = fields.Text(string="Notes")
    product_id = fields.Many2one('product.product', string='Related Product', readonly=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        # إنشاء منتج تلقائي وربطه
        product = self.env['product.product'].create({
            'name': record.name,
            'list_price': record.price_unit,
            'type': 'consu',
            'sale_ok': True,
            'purchase_ok': True,
        })
        record.product_id = product.id
        return record




# -----------------------------
# 4. أوامر الصيدلية
# -----------------------------
class HospitalPharmacyOrder(models.Model):
    _name = 'hospital.pharmacy.order'
    _description = 'Pharmacy Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Prescription Ref",
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.pharmacy.order') or _('New')
    )
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True, tracking=True)

    doctor_id = fields.Many2one(
        'hospital.staff',
        string="Prescribed By",
        tracking=True,
        domain=[('job_title', '=', 'doctor')]
    )

    pharmacist_id = fields.Many2one(
        'hospital.staff',
        string="Pharmacist",
        required=True,
        tracking=True,
        domain=[('job_title', '=', 'pharmacist')]
    )

    date = fields.Datetime(string="Prescription Date", default=fields.Datetime.now)
    line_ids = fields.One2many('hospital.pharmacy.order.line', 'order_id', string="Medicines")
    state = fields.Selection(
        [('draft', 'Draft'), ('dispensed', 'Dispensed'), ('cancel', 'Cancelled')],
        default='draft', tracking=True
    )

    def action_dispense(self):
        for order in self:
            if not order.line_ids:
                raise UserError(_("Please add at least one medicine line."))

            # خصم المخزون
            for line in order.line_ids:
                if line.medicine_id.quantity_available < line.quantity:
                    raise UserError(_("Not enough stock for %s") % line.medicine_id.name)
                line.medicine_id.quantity_available -= line.quantity

            # إنشاء / ربط بالفاتورة
            billing = self.env['hospital.billing'].search(
                [('patient_id', '=', order.patient_id.id), ('state', '=', 'draft')],
                limit=1
            )
            if not billing:
                billing = self.env['hospital.billing'].create({
                    'patient_id': order.patient_id.id,
                    'doctor_id': order.doctor_id.id,
                })

            # إضافة سطور الفاتورة
            for line in order.line_ids:
                product = line.medicine_id.product_id
                self.env['hospital.billing.line'].create({
                    'billing_id': billing.id,
                    'product_id': product.id,
                    'name': line.medicine_id.name,
                    'quantity': line.quantity,
                    'price_unit': line.medicine_id.price_unit,
                })

            order.state = 'dispensed'

    def action_cancel(self):
        for order in self:
            if order.state == 'dispensed':
                raise UserError(_("You cannot cancel a dispensed order."))
            order.state = 'cancel'


# -----------------------------
# 5. تفاصيل الأدوية داخل الوصفة
# -----------------------------
class HospitalPharmacyOrderLine(models.Model):
    _name = 'hospital.pharmacy.order.line'
    _description = 'Pharmacy Order Line'

    order_id = fields.Many2one('hospital.pharmacy.order', string="Prescription", required=True, ondelete='cascade')
    medicine_id = fields.Many2one('hospital.medicine', string="Medicine", required=True)
    quantity = fields.Float(string="Qty", default=1.0)
    price_unit = fields.Monetary(related="medicine_id.price_unit", store=True, readonly=True)
    currency_id = fields.Many2one(related="medicine_id.currency_id", store=True, readonly=True)
