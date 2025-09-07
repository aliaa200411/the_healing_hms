# -*- coding: utf-8 -*-
from odoo import fields, models, api

class LabRequest(models.Model):
    _name = 'hospital.lab.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Laboratory Request'
    _order = 'request_date desc'

    name = fields.Char(
        string='Request Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: 'New'
    )
    patient_id = fields.Many2one('hospital.patient', string='Patient', required=True)
    doctor_id = fields.Many2one(
        'hospital.staff', 
        string="Requested By",
        domain=[('job_title', '=', 'doctor')]
    )
    price = fields.Float(string='Price', readonly=True)
    test_type_id = fields.Many2one('hospital.lab.test.type', string='Lab Test', required=True)
    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sample_collected', 'Sample Collected'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    notes = fields.Text(string='Notes')
    lab_result_ids = fields.One2many('hospital.lab.result', 'request_id', string='Lab Results')

    # ---------------- Onchange to update price when selecting test ----------------
    @api.onchange('test_type_id')
    def _onchange_test_type_id(self):
        for rec in self:
            rec.price = rec.test_type_id.price if rec.test_type_id else 0.0

    # ---------------- Override create/write to store price ----------------
    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            # تحديث السعر إذا كان في test_type_id
            if vals.get('test_type_id'):
                test = self.env['hospital.lab.test.type'].browse(vals['test_type_id'])
                vals['price'] = test.price

            # توليد الرقم المرجعي من sequence
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('hospital.lab.request') or 'New'

        return super().create(vals_list)


    def write(self, vals):
        if vals.get('test_type_id'):
            test = self.env['hospital.lab.test.type'].browse(vals['test_type_id'])
            vals['price'] = test.price
        return super().write(vals)

    # ---------------- Workflow methods ----------------
    def action_collect_sample(self):
        for rec in self:
            if rec.state == 'draft':
                rec.state = 'sample_collected'

                # إنشاء منتج للفحص إذا لم يكن موجود
                if rec.test_type_id and not rec.test_type_id.product_id:
                    product = self.env['product.product'].create({
                        'name': rec.test_type_id.name,
                        'list_price': rec.test_type_id.price,
                        'sale_ok': True,
                        'purchase_ok': False,
                        'type': 'service',
                    })
                    rec.test_type_id.product_id = product.id

                # البحث عن فاتورة Draft للمريض أو إنشاؤها
                billing = self.env['hospital.billing'].search([
                    ('patient_id', '=', rec.patient_id.id),
                    ('state', '=', 'draft')
                ], limit=1)

                if not billing:
                    billing = self.env['hospital.billing'].create({
                        'patient_id': rec.patient_id.id,
                        'doctor_id': rec.doctor_id.id,
                    })

                # إضافة سطر الفاتورة مباشرة من test_type_id
                if rec.test_type_id and rec.test_type_id.product_id:
                    self.env['hospital.billing.line'].create({
                        'billing_id': billing.id,
                        'product_id': rec.test_type_id.product_id.id,
                        'name': rec.test_type_id.name,
                        'quantity': 1,
                        'price_unit': rec.test_type_id.price,
                        'lab_request_id': rec.id,
                    })

    def action_send_to_lab(self):
        for rec in self:
            if rec.state == 'sample_collected':
                # إنشاء نتيجة جديدة مرتبطة بالطلب
                result = self.env['hospital.lab.result'].create({
                    'request_id': rec.id,
                })
                rec.state = 'in_progress'

    # def action_done(self):
    #     for rec in self:
    #         if rec.state == 'in_progress':
    #             rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            if rec.state in ['sample_collected', 'in_progress']:
                # حذف كل نتائج المختبر المرتبطة بالطلب
                lab_results = self.env['hospital.lab.result'].search([('request_id', '=', rec.id)])
                lab_results.unlink()

                # حذف سطر الفاتورة المرتبط بالطلب فقط
                billing_lines = self.env['hospital.billing.line'].search([('lab_request_id', '=', rec.id)])
                billing_lines.unlink()

                # تغيير الحالة إلى 'cancelled'
                rec.state = 'cancelled'


    def action_reset_to_draft(self):
        for rec in self:
            if rec.state == 'cancelled':
                rec.state = 'draft'

    # ---------------- Print Lab Report ----------------    
    def action_print_results(self):
      return self.env.ref('the_healing_hms.action_report_lab_request_with_results').report_action(self)
