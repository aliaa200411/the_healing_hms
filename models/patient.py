# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HospitalPatient(models.Model):
    _name = 'hospital.patient'
    _description = 'Patient'

    name = fields.Char(string="Patient Name", required=True)
    age = fields.Integer(string="Age")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    partner_id = fields.Many2one('res.partner', string="Customer", readonly=True,
                                 help="Customer linked to this patient for invoices")

    @api.model
    def create(self, vals):
        if not vals.get('partner_id'):
            partner = self.env['res.partner'].create({
                'name': vals.get('name'),
                'customer_rank': 1,  
            })
            vals['partner_id'] = partner.id
        return super().create(vals)

    @api.onchange('name')
    def _onchange_name(self):
        if self.name and self.partner_id:
            self.partner_id.name = self.name
