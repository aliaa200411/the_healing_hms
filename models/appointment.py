from odoo import models, fields, api, exceptions, _

class Appointment(models.Model):
    _name = "hospital.appointment"
    _description = "Patient Appointment"

    patient_id = fields.Many2one(
        "hospital.patient",
        string="Patient",
        required=True,
        ondelete="cascade",
    )
    department_id = fields.Many2one("hospital.department", string="Department", required=True)
    doctor_id = fields.Many2one(
        "hospital.doctor",
        string="Doctor",
        required=True,
        domain="[('department_id', '=', department_id)]"
    )
    appointment_date = fields.Datetime(string="Appointment Date", required=True)
    reason = fields.Text(string="Reason for Visit")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', string="Status")

    # ----------- أزرار التحكم في الظهور -----------
    show_confirm = fields.Boolean(compute='_compute_show_buttons')
    show_done = fields.Boolean(compute='_compute_show_buttons')
    show_cancel = fields.Boolean(compute='_compute_show_buttons')
    show_draft = fields.Boolean(compute='_compute_show_buttons')

    @api.depends('state')
    def _compute_show_buttons(self):
        for rec in self:
            rec.show_confirm = rec.state == 'draft'
            rec.show_done = rec.state == 'confirmed'
            rec.show_cancel = rec.state == 'done'
            rec.show_draft = rec.state == 'cancelled'

    # ----------- Constraints ----------
    @api.constrains('doctor_id', 'appointment_date', 'state')
    def _check_doctor_availability(self):
        for record in self:
            if record.state in ['draft', 'confirmed']:
                conflict = self.search([
                    ('id', '!=', record.id),
                    ('doctor_id', '=', record.doctor_id.id),
                    ('appointment_date', '=', record.appointment_date),
                    ('state', 'in', ['draft', 'confirmed'])
                ], limit=1)
                if conflict:
                    raise exceptions.ValidationError(_(
                        "Doctor %s already has another appointment at this time."
                        % record.doctor_id.name
                    ))

    # ----------- Actions ----------
    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    # ----------- override create ----------
    @api.model
    def create(self, vals):
        rec = super(Appointment, self).create(vals)
        if rec.doctor_id and rec.patient_id:
            # إضافة المريض لقائمة الدكتور إذا مش موجود
            if rec.patient_id.id not in rec.doctor_id.patient_ids.ids:
                rec.doctor_id.write({
                    'patient_ids': [(4, rec.patient_id.id)]
                })
        return rec
