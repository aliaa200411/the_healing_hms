# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class BloodDonor(models.Model):
    _name = 'blood.bank.donor'
    _description = 'Blood Donor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner', string="Donor's Name", required=True, ondelete='cascade', tracking=True
    )
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female')],
        string='Gender', required=True
    ) 
    blood_type = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('AB', 'AB'), ('O', 'O')],
        string='Blood Type', required=True
    )
    rh = fields.Selection(
        [('+', '+'), ('-', '-')], string='Rh Factor', required=True
    )
    hemoglobin_level = fields.Float(string='Hemoglobin (g/dL)')
    weight = fields.Float(string='Weight (kg)', required=True)
    is_pregnant = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Pregnant', default='no'
    )
    is_breastfeeding = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], string='Breastfeeding', default='no'
    )
    last_donation_date = fields.Date(string='Last Donation Date')
    yearly_donation_count = fields.Integer(string='Donations This Year', compute='_compute_stats', store=True)
    bag_ids = fields.One2many('blood.bank.bag', 'donor_id', string='Donation History')
    medical_notes = fields.Text(string='Medical Notes')
    show_female_fields = fields.Boolean(
        string="Show Female Fields", compute='_compute_show_female_fields'
    )

    @api.depends('gender')
    def _compute_show_female_fields(self):
        for rec in self:
            rec.show_female_fields = (rec.gender == 'female')

    @api.depends('bag_ids.donation_date', 'last_donation_date')
    def _compute_stats(self):
        current_year = fields.Date.context_today(self).year
        for rec in self:
            dates = [d.donation_date for d in rec.bag_ids if d.donation_date and d.donation_date.year == current_year]
            if rec.last_donation_date and rec.last_donation_date.year == current_year and rec.last_donation_date not in dates:
                dates.append(rec.last_donation_date)
            rec.yearly_donation_count = len(dates)

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

            current_year = fields.Date.context_today(self).year
            yearly_count = len([bag for bag in donor.bag_ids if bag.donation_date and bag.donation_date.year == current_year])
            if donor.last_donation_date and donor.last_donation_date.year == current_year:
                if donor.last_donation_date not in [b.donation_date for b in donor.bag_ids]:
                    yearly_count += 1
            if donor.gender == 'female' and yearly_count > 3:
                raise ValidationError(_("Female donors are limited to 3 donations per year."))
            if donor.gender == 'male' and yearly_count > 4:
                raise ValidationError(_("Male donors are limited to 4 donations per year."))

    def action_view_donations(self):
        self.ensure_one()
        current_year = fields.Date.context_today(self).year
        action = {
            'name': _('Donations This Year'),
            'type': 'ir.actions.act_window',
            'res_model': 'blood.bank.bag',
            'view_mode': 'tree,form',
            'domain': [
                ('donor_id', '=', self.id),
                ('donation_date', '>=', date(current_year, 1, 1)),
                ('donation_date', '<=', date(current_year, 12, 31))
            ],
            'context': {'default_donor_id': self.id},
            'views': [
                (self.env.ref('the_healing_hms.view_blood_bag_list').id, 'tree'),
                (self.env.ref('the_healing_hms.view_blood_bag_form').id, 'form'),
            ]
        }
        return action

    def name_get(self):
        result = []
        for rec in self:
            name = rec.partner_id.name or _("Unnamed Donor")
            if rec.blood_type and rec.rh:
                name = f"{name} ({rec.blood_type}{rec.rh})"
            result.append((rec.id, name))
        return result

