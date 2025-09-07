from odoo import models, fields, api

class LabResult(models.Model):
    _name = 'hospital.lab.result'
    _description = 'Laboratory Result'
    _order = 'id desc'

    request_id = fields.Many2one('hospital.lab.request', string='Lab Request', required=True)
    result_line_ids = fields.One2many('hospital.lab.result.line', 'result_id', string='Results')
    state = fields.Selection([
        ('waiting', 'Waiting for the result'),
        ('done', 'The result is done')
    ], string='Status', default='waiting', tracking=True)

    # Related fields لعرض معلومات الطلب فوق التيبل
    test_name = fields.Char(related='request_id.test_type_id.name', string='Lab Test', readonly=True)
    patient_name = fields.Char(related='request_id.patient_id.name', string='Patient', readonly=True)
    doctor_name = fields.Char(related='request_id.doctor_id.name', string='Doctor', readonly=True)
    request_date = fields.Datetime(related='request_id.request_date', string='Request Date', readonly=True)  # هذا الجديد

    def action_done(self):
        for rec in self:
            if rec.state == 'waiting':
                rec.state = 'done'
                rec.request_id.state = 'done'

    def action_print_results(self):
        return self.env.ref('the_healing_hms.action_report_lab_request_result').report_action(self.request_id)


class LabResultLine(models.Model):
    _name = 'hospital.lab.result.line'
    _description = 'Lab Result Line'

    result_id = fields.Many2one('hospital.lab.result', string='Lab Result', required=True, ondelete='cascade')
    test_name = fields.Char(string='Test', required=True)  # كتابة حرة بدل Many2one
    result_value = fields.Char(string='Result')
    unit = fields.Char(string='Unit')
    sequence = fields.Integer(string='Sequence', default=10)
