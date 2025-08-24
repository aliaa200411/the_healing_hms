from odoo import models, fields, api

class Staff(models.Model):
    _name = "hospital.staff"
    _description = "Hospital Staff"

    staff_id = fields.Char(
        string="Staff ID",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('hospital.staff') or 'NEW'
    )
    user_id = fields.Many2one("res.users", string="User")
    department_id = fields.Many2one("hospital.department", string="Department")
    position = fields.Char(string="Position")
    hire_date = fields.Date(string="Hire Date")
    salary = fields.Float(string="Salary")
    is_active = fields.Boolean(string="Active", default=True)

    patient_ids = fields.Many2many("hospital.patient", string="Patients")
