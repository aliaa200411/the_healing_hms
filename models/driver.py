from odoo import models, fields, api, _

class EmergencyDriver(models.Model):
    _name = 'healing_hms.emergency_driver'
    _description = 'Emergency Driver'

    name = fields.Char(string="Driver Name", required=True)
    ambulance_id = fields.Many2one('healing_hms.ambulance', string="Ambulance")
    phone = fields.Char(string="Phone")  
    ambulance_license_number = fields.Char(
        string="Ambulance License Number",
        related='ambulance_id.license_plate',
        store=True,
        readonly=True
    )
    status = fields.Selection([
        ('available', 'Available'),
        ('on_duty', 'On Duty'),
        ('off', 'Off Duty')
    ], string="Status", default='available')