from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AmbulanceRequest(models.Model):
    _name = 'emergency.ambulance.request'
    _description = 'Ambulance Request'

    patient_name = fields.Char(string='Patient Name', required=True)
    patient_id = fields.Many2one('hospital.patient', string="Patient")
    patient_location = fields.Char(string='Patient Location', required=True)
    requested_time = fields.Datetime(string='Requested Time', default=fields.Datetime.now)
    assigned_ambulance_id = fields.Many2one('healing_hms.ambulance', string='Assigned Ambulance')
    assigned_driver_id = fields.Many2one('healing_hms.emergency_driver', string='Assigned Driver')
    status = fields.Selection([
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='assigned')
    notes = fields.Text(string='Notes')

    @api.onchange('assigned_ambulance_id')
    def _onchange_ambulance(self):
        if self.assigned_ambulance_id and self.assigned_ambulance_id.status != 'available':
            raise ValidationError('This ambulance is not available!')
        elif self.assigned_ambulance_id:
            self.assigned_ambulance_id.status = 'busy'

    @api.onchange('assigned_driver_id')
    def _onchange_driver(self):
        if self.assigned_driver_id and self.assigned_driver_id.status != 'available':
            raise ValidationError('This driver is not available!')
        elif self.assigned_driver_id:
            self.assigned_driver_id.status = 'on_duty'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ambulance = self.env['healing_hms.ambulance'].search([('status', '=', 'available')], limit=1)
        driver = self.env['healing_hms.emergency_driver'].search([('status', '=', 'available')], limit=1)
        if ambulance:
            res['assigned_ambulance_id'] = ambulance.id
        if driver:
            res['assigned_driver_id'] = driver.id
        return res

    def action_complete(self):
        for rec in self:
            rec.status = 'completed'
            if rec.assigned_ambulance_id:
                rec.assigned_ambulance_id.status = 'available'
            if rec.assigned_driver_id:
                rec.assigned_driver_id.status = 'available'

    def action_cancel(self):
        for rec in self:
            rec.status = 'cancelled'
            if rec.assigned_ambulance_id:
                rec.assigned_ambulance_id.status = 'available'
            if rec.assigned_driver_id:
                rec.assigned_driver_id.status = 'available'
