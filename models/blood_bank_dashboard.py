# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

# ================== Blood Bank Dashboard ==================
class BloodBankDashboard(models.Model):
    _name = 'blood.bank.dashboard'
    _description = 'Blood Bank Dashboard'
    _rec_name = 'name'
    _order = 'name'

    # ===== Basic Info =====
    name = fields.Char(string='Dashboard', default='Blood Bank Overview', readonly=True)

    # ===== KPIs =====
    month = fields.Char(string='Month', compute='_compute_kpis')
    total_bags = fields.Integer(string='Total Bags', compute='_compute_kpis', store=True)
    available_bags = fields.Integer(string='Available Bags', compute='_compute_kpis', store=True)
    used_bags = fields.Integer(string='Used Bags', compute='_compute_kpis', store=True)
    expired_bags = fields.Integer(string='Expired Bags', compute='_compute_kpis', store=True)
    most_needed_blood_type = fields.Char(string='Most Needed Blood Type', compute='_compute_kpis', store=True)

    # ===== Blood Type Percentages =====
    percent_A_pos = fields.Float(string='A+', compute='_compute_blood_type_percent', store=True)
    percent_A_neg = fields.Float(string='A-', compute='_compute_blood_type_percent', store=True)
    percent_B_pos = fields.Float(string='B+', compute='_compute_blood_type_percent', store=True)
    percent_B_neg = fields.Float(string='B-', compute='_compute_blood_type_percent', store=True)
    percent_AB_pos = fields.Float(string='AB+', compute='_compute_blood_type_percent', store=True)
    percent_AB_neg = fields.Float(string='AB-', compute='_compute_blood_type_percent', store=True)
    percent_O_pos = fields.Float(string='O+', compute='_compute_blood_type_percent', store=True)
    percent_O_neg = fields.Float(string='O-', compute='_compute_blood_type_percent', store=True)

    # ================== Compute Blood Type Percentages ==================
    def _compute_blood_type_percent(self):
        Bag = self.env['blood.bank.bag']
        bags = Bag.search([])
        total = len(bags)
        counts = {bt: 0 for bt in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']}

        for b in bags:
            key = (b.blood_type or '') + (b.rh or '')
            if key in counts:
                counts[key] += 1

        for rec in self:
            rec.percent_A_pos = counts['A+'] / total * 100 if total else 0
            rec.percent_A_neg = counts['A-'] / total * 100 if total else 0
            rec.percent_B_pos = counts['B+'] / total * 100 if total else 0
            rec.percent_B_neg = counts['B-'] / total * 100 if total else 0
            rec.percent_AB_pos = counts['AB+'] / total * 100 if total else 0
            rec.percent_AB_neg = counts['AB-'] / total * 100 if total else 0
            rec.percent_O_pos = counts['O+'] / total * 100 if total else 0
            rec.percent_O_neg = counts['O-'] / total * 100 if total else 0


    # ================== Compute KPIs ==================
    def _compute_kpis(self):
        Bag = self.env['blood.bank.bag']
        Transfusion = self.env['blood.bank.transfusion']
        today_month = datetime.today().strftime("%B %Y")
        bags = Bag.search([])

        for rec in self:
            rec.total_bags = len(bags)
            rec.available_bags = len([b for b in bags if b.status == 'available'])
            rec.used_bags = len([b for b in bags if b.status == 'used'])
            rec.expired_bags = len([b for b in bags if b.status == 'expired'])
            rec.month = today_month

            # أكثر نوع دم مطلوب
            transfusions = Transfusion.read_group(
                [('request_status', '=', 'waiting')],
                ['blood_type'],
                ['blood_type']
            )
            if transfusions:
                transfusions.sort(key=lambda x: x['blood_type_count'], reverse=True)
                rec.most_needed_blood_type = transfusions[0]['blood_type'] or 'N/A'
            else:
                rec.most_needed_blood_type = 'N/A'

    # ================== Compute Blood Type Percentages ==================
    def _compute_blood_type_percent(self):
        Bag = self.env['blood.bank.bag']
        bags = Bag.search([])
        total = len(bags)
        counts = {bt: 0 for bt in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']}

        for b in bags:
            key = (b.blood_type or '') + (b.rh or '')
            if key in counts:
                counts[key] += 1

        for rec in self:
            # إذا اختار زمرة معينة اعرضها بس، وإذا ما اختار اعرض الكل
            selected = [rec.selected_blood_types] if rec.selected_blood_types else counts.keys()

            rec.percent_A_pos = counts['A+'] / total * 100 if 'A+' in selected and total else 0
            rec.percent_A_neg = counts['A-'] / total * 100 if 'A-' in selected and total else 0
            rec.percent_B_pos = counts['B+'] / total * 100 if 'B+' in selected and total else 0
            rec.percent_B_neg = counts['B-'] / total * 100 if 'B-' in selected and total else 0
            rec.percent_AB_pos = counts['AB+'] / total * 100 if 'AB+' in selected and total else 0
            rec.percent_AB_neg = counts['AB-'] / total * 100 if 'AB-' in selected and total else 0
            rec.percent_O_pos = counts['O+'] / total * 100 if 'O+' in selected and total else 0
            rec.percent_O_neg = counts['O-'] / total * 100 if 'O-' in selected and total else 0

    # ================== Get or Create Dashboard ==================
    @api.model
    def get_or_create_dashboard(self):
        dashboard = self.env['blood.bank.dashboard'].sudo().search([], limit=1)
        if not dashboard:
            dashboard = self.env['blood.bank.dashboard'].sudo().create({'name': 'Blood Bank Overview'})
        return dashboard

    # ================== Update Dashboard ==================
    def _update_dashboard(self):
        dashboard = self.get_or_create_dashboard()
        dashboard._compute_kpis()
        dashboard._compute_blood_type_percent()

    # ================== Reload Dashboard Action ==================
    def action_reload_dashboard(self):
        dashboard = self.get_or_create_dashboard()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Blood Bank Dashboard',
            'res_model': 'blood.bank.dashboard',
            'view_mode': 'kanban,graph,list,form',
            'res_id': dashboard.id,
            'target': 'current',
            'context': {'create': False},
        }
