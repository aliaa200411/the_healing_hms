# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError

class HospitalPrescription(models.Model):
    _name = "hospital.prescription"
    _description = "Medical Prescription"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Prescription Ref",
        readonly=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.prescription') or _('New')
    )
    patient_id = fields.Many2one('hospital.patient', string="Patient", required=True, tracking=True)
    doctor_id = fields.Many2one(
        'hospital.staff',
        string="Doctor",
        required=True,
        domain=[('job_title','=','doctor')],
        tracking=True,
        default=lambda self: self.env['hospital.staff'].search([
            ('job_title','=','doctor'), 
            ('user_id','=',self.env.user.id)
        ], limit=1).id
    )

    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    line_ids = fields.One2many('hospital.prescription.line', 'prescription_id', string="Medicines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], default='draft', tracking=True)
    note = fields.Text(string="Notes")

    @api.depends('state')
    def _compute_show_confirm(self):
        for rec in self:
            rec.show_confirm_button = rec.state == 'draft'

    def action_confirm(self):
        """تأكيد الوصفة بعد التأكد من وجود خطوط الأدوية"""
        for rec in self:
            if not rec.line_ids:
                raise UserError(_("Add at least one medicine line before confirming the prescription."))
            rec.state = 'confirmed'

    def print_prescription_report(self):
        return self.env.ref('the_healing_hms.action_report_prescription').report_action(self)

    @api.model
    def create(self, vals):
        # التأكد أن الدكتور هو الذي يسجل الوصفة
        if 'doctor_id' not in vals:
            doctor = self.env['hospital.staff'].search([
                ('job_title','=','doctor'), 
                ('user_id','=',self.env.user.id)
            ], limit=1)
            if doctor:
                vals['doctor_id'] = doctor.id
            else:
                raise AccessError("You must be a doctor to create a prescription.")
        return super().create(vals)
         
    def write(self, vals):
        for rec in self:
            if rec.doctor_id.user_id != self.env.user:
                raise AccessError("You can only edit prescriptions you created.")
        return super().write(vals)


class HospitalPrescriptionLine(models.Model):
    _name = "hospital.prescription.line"
    _description = "Prescription Line"

    prescription_id = fields.Many2one('hospital.prescription', string="Prescription", required=True, ondelete='cascade')
    medicine_id = fields.Many2one('hospital.medicine', string="Medicine", required=True)

    medicine_form = fields.Selection([
        ('tablet', 'Tablet / Capsule'),
        ('syrup', 'Syrup / Liquid'),
        ('injection', 'Injection'),
    ], string="Medicine Form", default='tablet', required=True)

    dosage = fields.Float(string="Dosage", default=1.0, help="Dosage per intake")
    times_per_day = fields.Selection([
        ('1', 'Once a day'),
        ('2', 'Twice a day'),
        ('3', 'Three times a day'),
        ('4', 'Four times a day'),
    ], string="Times per Day", default='1')

    duration = fields.Char(
        string="Duration",
        help="Duration of treatment. Example: 5 days, 2 weeks, 3 times/week"
    )

    dosage_unit = fields.Char(string="Dosage Unit", compute='_compute_dosage_unit', store=True)

    @api.depends('medicine_form')
    def _compute_dosage_unit(self):
        for rec in self:
            if rec.medicine_form == 'tablet':
                rec.dosage_unit = 'Pill(s)'
            elif rec.medicine_form == 'syrup':
                rec.dosage_unit = 'ml'
            elif rec.medicine_form == 'injection':
                rec.dosage_unit = 'Injection(s)'
            else:
                rec.dosage_unit = ''
