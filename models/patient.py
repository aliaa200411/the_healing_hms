from odoo import models, fields, api, _

class Patient(models.Model):
    _name = "hospital.patient"
    _description = "Hospital Patient"

    patient_code = fields.Char(string="Patient Code", copy=False, readonly=True, index=True)
    first_name = fields.Char(string="First Name", required=True)
    last_name = fields.Char(string="Last Name", required=True)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    nationality = fields.Char(string="Nationality")
    dob = fields.Date(string="Date of Birth")
    age = fields.Integer(string="Age", compute="_compute_age", store=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    blood_type = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-')
    ], string="Blood Type")
    allergies = fields.Text(string="Allergies")
    address = fields.Char(string="Address")
    appointment_ids = fields.One2many("hospital.appointment", "patient_id", string="Appointments")
    diagnosis = fields.Text(string='Diagnosis')
    doctor_id = fields.Many2one('hospital.doctor', string='Doctor')
    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True)

    # حقل محسوب للاسم الكامل
    name = fields.Char(string="Full Name", compute="_compute_name", store=True)

    @api.depends('first_name', 'last_name')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.first_name or ''} {rec.last_name or ''}".strip()

    @api.depends('dob')
    def _compute_age(self):
        for rec in self:
            if rec.dob:
                today = fields.Date.today()
                rec.age = today.year - rec.dob.year - ((today.month, today.day) < (rec.dob.month, rec.dob.day))
            else:
                rec.age = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('patient_code'):
                vals['patient_code'] = self.env['ir.sequence'].next_by_code('hospital.patient') or _('New')
        return super(Patient, self).create(vals_list)

    # دالة طباعة التقرير
    def action_print_medical_record(self):
        return self.env.ref('hospital.action_report_medical_record').report_action(self)
