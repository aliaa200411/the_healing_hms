# -*- coding: utf-8 -*-
from odoo import fields, models, api

class LabTestType(models.Model):
    _name = 'hospital.lab.test.type'
    _description = 'Laboratory Test Type'
    _order = 'name asc'

    name = fields.Char(string='Test Name', required=True)
    code = fields.Char(string='Code')
    description = fields.Text(string='Description')
    price = fields.Float(string='Price', required=True)
    duration_hours = fields.Float(string='Estimated Duration (hours)')
    notes = fields.Text(string='Notes')
    product_id = fields.Many2one('product.product', string='Related Product', domain=[('sale_ok','=',True)])
    sequence = fields.Integer(string='Sequence', default=10)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if not record.product_id:
            product = self.env['product.product'].create({
                'name': record.name,
                'list_price': record.price,
                'sale_ok': True,
                'purchase_ok': False,
                'type': 'service', 
            })
            record.product_id = product.id
        return record