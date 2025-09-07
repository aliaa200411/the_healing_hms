# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# ================== Medicine Dashboard ==================
class HospitalMedicineDashboard(models.Model):
    _name = 'hospital.medicine.dashboard'
    _description = 'Hospital Medicine Dashboard'
    _rec_name = 'medicine_id'
    _order = 'medicine_id'

    # ===== Medicine Info =====
    medicine_id = fields.Many2one('hospital.medicine', string="Medicine", required=True, readonly=True)
    medicine_name = fields.Char(string="Medicine Name", related='medicine_id.name', readonly=True)
    code = fields.Char(string="Medicine Code", related='medicine_id.code', readonly=True)
    unit_price = fields.Monetary(string="Unit Price", related='medicine_id.price_unit', readonly=True)
    currency_id = fields.Many2one('res.currency', related='medicine_id.currency_id', readonly=True)
    notes = fields.Text(string="Notes", related='medicine_id.description', readonly=True)

    # ===== Quantities =====
    total_qty = fields.Float(string="Total Ordered", compute='_compute_kpis', store=True)
    used_qty = fields.Float(string="Used / Sold", compute='_compute_kpis', store=True)
    available_qty = fields.Float(string="Available Qty", compute='_compute_kpis', store=True)

    # ===== Total Value =====
    total_value = fields.Monetary(string="Total Value", compute='_compute_kpis', store=True)

    # ================== Compute KPIs ==================
    @api.depends('medicine_id')
    def _compute_kpis(self):
        PharmacyOrderLine = self.env['hospital.pharmacy.order.line']
        BillingLine = self.env['hospital.billing.line']

        for rec in self:
            med = rec.medicine_id
            if med:
                rec.total_qty = sum(PharmacyOrderLine.search([('medicine_id', '=', med.id)]).mapped('quantity'))
                rec.used_qty = sum(BillingLine.search([('medicine_id', '=', med.id)]).mapped('quantity'))
                rec.available_qty = med.quantity_available
                rec.total_value = rec.available_qty * med.price_unit

    @api.model
    def create_dashboard_records(self):
        """Update or create dashboard records for all medicines"""
        medicines = self.env['hospital.medicine'].search([])
        for med in medicines:
            dashboard = self.search([('medicine_id', '=', med.id)], limit=1)
            if not dashboard:
                self.create({'medicine_id': med.id})
            else:
                dashboard._compute_kpis()


# ================== Medicine Model Extension ==================
class HospitalMedicine(models.Model):
    _inherit = 'hospital.medicine'

    def create_dashboard_record(self):
        dashboard = self.env['hospital.medicine.dashboard'].search([('medicine_id', '=', self.id)], limit=1)
        if not dashboard:
            self.env['hospital.medicine.dashboard'].create({'medicine_id': self.id})

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        rec.create_dashboard_record()
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec.create_dashboard_record()
        self.env['hospital.medicine.dashboard'].create_dashboard_records()
        return res

    def unlink(self):
        for rec in self:
            dash = self.env['hospital.medicine.dashboard'].search([('medicine_id', '=', rec.id)])
            dash.unlink()
        return super().unlink()
