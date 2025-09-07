from odoo import models, fields, api, _
from odoo.exceptions import UserError

# ==========================
# 1. تصنيفات الأدوية
# ==========================
class HospitalPharmacyCategory(models.Model):
    _name = 'hospital.pharmacy.category'
    _description = 'Medicine Category'
    _order = 'name'

    name = fields.Char(string="Category Name", required=True)
    description = fields.Text(string="Description")

# ==========================
# 2. معلومات الأدوية
# ==========================
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

# ==========================
# 3. الصيدلي
# ==========================
class HospitalPharmacist(models.Model):
    _name = 'hospital.pharmacist'
    _description = 'Hospital Pharmacist'
    _order = 'name'

    name = fields.Char(string="Pharmacist Name", required=True)
    code = fields.Char(
        string="Pharmacist Code",
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.pharmacist') or _('New')
    )
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    active = fields.Boolean(string="Active", default=True)

# ==========================
# 4. أوامر الصيدلية
# ==========================
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
    doctor_id = fields.Many2one('hospital.doctor', string="Prescribed By", tracking=True)
    pharmacist_id = fields.Many2one('hospital.pharmacist', string="Pharmacist", required=True, tracking=True)
    date = fields.Datetime(string="Prescription Date", default=fields.Datetime.now)
    line_ids = fields.One2many('hospital.pharmacy.order.line', 'order_id', string="Medicines")
    state = fields.Selection(
        [('draft', 'Draft'), ('dispensed', 'Dispensed'), ('cancel', 'Cancelled')],
        default='draft',
        tracking=True
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
            
            order.state = 'dispensed'
            # لا داعي لتحديث الداشبورد يدوياً

    def action_cancel(self):
        for order in self:
            if order.state == 'dispensed':
                raise UserError(_("You cannot cancel a dispensed order."))
            order.state = 'cancel'
            # لا داعي لتحديث الداشبورد يدوياً

# ==========================
# 5. تفاصيل الأدوية داخل الوصفة
# ==========================
class HospitalPharmacyOrderLine(models.Model):
    _name = 'hospital.pharmacy.order.line'
    _description = 'Pharmacy Order Line'

    order_id = fields.Many2one('hospital.pharmacy.order', string="Prescription", required=True, ondelete='cascade')
    medicine_id = fields.Many2one('hospital.medicine', string="Medicine", required=True)
    quantity = fields.Float(string="Qty", default=1.0)
    price_unit = fields.Monetary(related="medicine_id.price_unit", store=True, readonly=True)
    currency_id = fields.Many2one(related="medicine_id.currency_id", store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return res

    def unlink(self):
        res = super().unlink()
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return res

