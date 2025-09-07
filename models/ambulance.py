# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

class Ambulance(models.Model):
    _name = 'healing_hms.ambulance'
    _description = 'Ambulance'

    name = fields.Char(
        string='Ambulance ID', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('New')
    )
    license_plate = fields.Char(string='License Plate', required=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('maintenance', 'Under Maintenance')
    ], string='Status', default='available')
    capacity = fields.Selection([
        ('1', '1'),
        ('2', '2')
    ], string='Capacity', required=True)
    last_maintenance_date = fields.Date(string='Last Maintenance', required=True)
    next_maintenance_date = fields.Date(string='Next Maintenance', readonly=True)

    # بدل driver_ids على emergency_driver → نجيبهم من staff
    driver_ids = fields.One2many(
        'hospital.staff',
        'ambulance_id',  # نفس الحقل الموجود بالستاف
        string='Drivers',
        domain=[('job_title', '=', 'ambulance')]
    )

    _sql_constraints = [
        ('license_plate_uniq', 'unique(license_plate)', 'License Plate must be unique!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals or vals['name'] == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('healing_hms.ambulance') or 'New'
            if vals.get('last_maintenance_date'):
                last_date = fields.Date.from_string(vals['last_maintenance_date'])
                vals['next_maintenance_date'] = last_date + relativedelta(months=6)
        return super(Ambulance, self).create(vals_list)

    def write(self, vals):
        if vals.get('last_maintenance_date'):
            last_date = fields.Date.from_string(vals['last_maintenance_date'])
            vals['next_maintenance_date'] = last_date + relativedelta(months=6)
        return super(Ambulance, self).write(vals)

    def check_maintenance_due(self):
        today = fields.Date.today()
        for amb in self.search([('next_maintenance_date','<=',today),('status','!=','maintenance')]):
            amb.status = 'maintenance'

    def set_busy(self):
        for amb in self:
            amb.status = 'busy'

    def set_available(self):
        for amb in self:
            amb.status = 'available'
