# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class BloodDonor(models.Model):
    _name = 'blood.bank.donor'
    _description = 'Blood Donor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id'

    partner_id = fields.Many2one('res.partner', string="Donor's Name", required=True, ondelete='cascade', tracking=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender', required=True)
    blood_type = fields.Selection([('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')], string='Blood Type', required=True)
    rh = fields.Selection([('+', '+'), ('-', '-')], string='Rh Factor', required=True)
    hemoglobin_level = fields.Float(string='Hemoglobin (g/dL)')
    weight = fields.Float(string='Weight (kg)', required=True)
    is_pregnant = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Pregnant', default='no')
    is_breastfeeding = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Breastfeeding', default='no')
    medical_notes = fields.Text(string='Medical Notes')

    show_female_fields = fields.Boolean(compute='_compute_show_female_fields', store=False)

    @api.depends('gender')
    def _compute_show_female_fields(self):
        for rec in self:
            rec.show_female_fields = rec.gender == 'female'

    @api.onchange('gender')
    def _onchange_gender(self):
        for rec in self:
            if rec.gender == 'male':
                rec.is_pregnant = 'no'
                rec.is_breastfeeding = 'no'

    @api.constrains('hemoglobin_level', 'weight', 'is_pregnant', 'is_breastfeeding')
    def _check_requirements(self):
        for donor in self:
            if donor.gender == 'male' and donor.hemoglobin_level and donor.hemoglobin_level < 13:
                raise ValidationError(_("Male donors must have at least 13 g/dL hemoglobin."))
            if donor.gender == 'female' and donor.hemoglobin_level and donor.hemoglobin_level < 12.5:
                raise ValidationError(_("Female donors must have at least 12.5 g/dL hemoglobin."))
            if donor.weight and donor.weight < 50:
                raise ValidationError(_("Donor must weigh at least 50 kg."))
            if donor.gender == 'female' and donor.is_pregnant == 'yes':
                raise ValidationError(_("Pregnant donors are not eligible to donate."))
            if donor.gender == 'female' and donor.is_breastfeeding == 'yes':
                raise ValidationError(_("Breastfeeding donors are not eligible to donate."))

    def button_donate(self):
        self.ensure_one()
        self.env['blood.bank.bag'].create({
            'donor_id': self.partner_id.id,
            'blood_type': self.blood_type,
            'rh': self.rh,
            'status': 'available',
            'donation_date': date.today(),
        })
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def name_get(self):
        result = []
        for rec in self:
            name = rec.partner_id.name or _("Unnamed Donor")
            if rec.blood_type and rec.rh:
                name = f"{name} ({rec.blood_type}{rec.rh})"
            result.append((rec.id, name))
        return result
