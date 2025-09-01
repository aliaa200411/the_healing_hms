from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AmbulanceRequest(models.Model):
    _name = 'emergency.ambulance.request'
    _description = 'Ambulance Request'

    patient_name = fields.Char(string='Patient Name', required=True)
    patient_id = fields.Many2one('hospital.patient', string="Patient")
    patient_location = fields.Char(string='Patient Location', required=True)
    requested_time = fields.Datetime(string='Requested Time', default=fields.Datetime.now)

    assigned_ambulance_id = fields.Many2one(
        'healing_hms.ambulance',
        string='Assigned Ambulance',
        domain=[('status', '=', 'available')]
    )

    assigned_driver_id = fields.Many2one(
        'healing_hms.emergency_driver',
        string='Assigned Driver',
        domain="[('ambulance_id', '=', assigned_ambulance_id), ('status', '=', 'available')]"
    )

    status = fields.Selection([
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending')

    notes = fields.Text(string='Notes')

    #==== Onchange ====#
    @api.onchange('assigned_ambulance_id')
    def _onchange_ambulance(self):
        """لما تختار سيارة: نجيب سائقها المتاح ونضبط الحالة."""
        if self.assigned_ambulance_id:
            driver = self.env['healing_hms.emergency_driver'].search([
                ('ambulance_id', '=', self.assigned_ambulance_id.id),
                ('status', '=', 'available')
            ], limit=1)
            if driver:
                self.assigned_driver_id = driver
                self.status = 'assigned'
            else:
                self.assigned_driver_id = False
                self.status = 'pending'
        else:
            self.assigned_driver_id = False
            self.status = 'pending'

        return {
            'domain': {
                'assigned_driver_id': [
                    ('ambulance_id', '=', self.assigned_ambulance_id.id if self.assigned_ambulance_id else False),
                    ('status', '=', 'available')
                ]
            }
        }

    @api.onchange('assigned_driver_id')
    def _onchange_driver(self):
        """لو اخترت سائق مخالف لسيارة الإسعاف، نفرغه وننبه."""
        if self.assigned_driver_id and self.assigned_ambulance_id:
            if self.assigned_driver_id.ambulance_id != self.assigned_ambulance_id:
                self.assigned_driver_id = False
                return {
                    'warning': {
                        'title': _('Driver mismatch'),
                        'message': _('Please choose a driver that belongs to the selected ambulance.')
                    }
                }

        if self.assigned_driver_id and self.assigned_ambulance_id:
            self.status = 'assigned'
        elif not self.assigned_driver_id or not self.assigned_ambulance_id:
            self.status = 'pending'

    #==== Default ====#
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        ambulance = self.env['healing_hms.ambulance'].search([('status', '=', 'available')], limit=1)
        if ambulance:
            res['assigned_ambulance_id'] = ambulance.id
            driver = self.env['healing_hms.emergency_driver'].search([
                ('ambulance_id', '=', ambulance.id),
                ('status', '=', 'available')
            ], limit=1)
            if driver:
                res['assigned_driver_id'] = driver.id
                res['status'] = 'assigned'
            else:
                res['status'] = 'pending'
        else:
            res['status'] = 'pending'

        return res

    #==== Constraint ====#
    @api.constrains('assigned_ambulance_id', 'assigned_driver_id')
    def _check_driver_belongs_to_ambulance(self):
        for rec in self:
            if rec.assigned_driver_id and rec.assigned_ambulance_id:
                if rec.assigned_driver_id.ambulance_id != rec.assigned_ambulance_id:
                    raise ValidationError(_('Selected driver does not belong to the selected ambulance.'))

    #==== Create / Write ====#
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.status == 'assigned':
                if rec.assigned_ambulance_id and rec.assigned_ambulance_id.status == 'available':
                    rec.assigned_ambulance_id.status = 'busy'
                if rec.assigned_driver_id and rec.assigned_driver_id.status == 'available':
                    rec.assigned_driver_id.status = 'on_duty'
        return records

    def write(self, vals):
        before = {
            rec.id: {
                'ambulance': rec.assigned_ambulance_id,
                'driver': rec.assigned_driver_id,
                'status': rec.status,
            } for rec in self
        }

        res = super().write(vals)

        for rec in self:
            old = before[rec.id]
            old_amb = old['ambulance']
            old_drv = old['driver']
            old_status = old['status']

            # حرر الموارد القديمة إذا تغيرت
            if old_amb and old_amb != rec.assigned_ambulance_id and old_status == 'assigned':
                old_amb.status = 'available'
            if old_drv and old_drv != rec.assigned_driver_id and old_status == 'assigned':
                old_drv.status = 'available'

            # ثبّت الموارد الجديدة
            if rec.status == 'assigned':
                if rec.assigned_ambulance_id and rec.assigned_ambulance_id.status != 'busy':
                    rec.assigned_ambulance_id.status = 'busy'
                if rec.assigned_driver_id and rec.assigned_driver_id.status != 'on_duty':
                    rec.assigned_driver_id.status = 'on_duty'

            # إذا خلص/اتلغى → رجّع الموارد
            if old_status == 'assigned' and rec.status in ('completed', 'cancelled'):
                if rec.assigned_ambulance_id:
                    rec.assigned_ambulance_id.status = 'available'
                if rec.assigned_driver_id:
                    rec.assigned_driver_id.status = 'available'

        return res

    #==== Actions ====#
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
