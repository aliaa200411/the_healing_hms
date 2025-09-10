from odoo import models, fields, api

class HospitalRoom(models.Model):
    _name = 'hospital.room'
    _description = 'Hospital Room'
    _order = 'department_id, room_number'

    room_number = fields.Char(string="Room Number", required=True)
    department_id = fields.Many2one('hospital.department', string="Department", ondelete='cascade')
    floor = fields.Char(string="Floor")
    wing = fields.Char(string="Wing")

    room_type = fields.Selection([
        ('single', 'Single (1 Bed)'),
        ('double', 'Double (2 Beds)'),
        ('ward', 'Ward (7 Beds)'),
    ], string="Room Type", default='single', required=True)

    capacity = fields.Integer(
        string="Number of Beds",
        compute="_compute_capacity",
        store=True,
        readonly=True
    )

    state = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('unavailable', 'Unavailable')
    ], string="Status", default='available')

    bed_ids = fields.One2many('hospital.bed', 'room_id', string="Beds")
    available_beds = fields.Integer(string="Available Beds", compute="_compute_available_beds", store=True)

    # ============= Capacity based on type =============
    @api.depends('room_type')
    def _compute_capacity(self):
        mapping = {'single': 1, 'double': 2, 'ward': 7}
        for room in self:
            room.capacity = mapping.get(room.room_type, 1)

    # ============= Compute available beds & state =============
    @api.depends('bed_ids.booking_ids.state')
    def _compute_available_beds(self):
        """
        Rules:
        - single: if any booking confirmed/invoiced -> unavailable
        - double: 1 bed booked -> occupied, 2 booked -> unavailable, 0 -> available
        - ward: 0 -> available, 1..capacity-1 -> occupied, capacity -> unavailable
        """
        occupied_states = ['confirmed', 'invoiced']
        for room in self:
            total_beds = len(room.bed_ids)
            booked_beds = 0
            for bed in room.bed_ids:
                if any(b.state in occupied_states for b in bed.booking_ids):
                    booked_beds += 1

            room.available_beds = total_beds - booked_beds

            if room.room_type == 'single':
                room.state = 'unavailable' if booked_beds >= 1 else 'available'
            elif room.room_type == 'double':
                if booked_beds == 0:
                    room.state = 'available'
                elif booked_beds == 1:
                    room.state = 'occupied'
                else:
                    room.state = 'unavailable'
            else:  # ward
                if booked_beds == 0:
                    room.state = 'available'
                elif booked_beds >= room.capacity:
                    room.state = 'unavailable'
                else:
                    room.state = 'occupied'

    # ============= Auto-fill floor & wing =============
    @api.onchange('department_id')
    def _onchange_department(self):
        if self.department_id:
            self.floor = self.department_id.floor
            self.wing = self.department_id.wing
        else:
            self.floor = False
            self.wing = False

    # ============= Smart button to view bookings =============
    def action_open_bookings(self):
        return {
            'name': 'Bookings',
            'type': 'ir.actions.act_window',
            'res_model': 'hospital.booking',
            'view_mode': 'tree,form',
            'domain': [('bed_id.room_id', '=', self.id)],
        }

    # ============= Auto-update dashboard =============
    def _update_dashboard(self):
        for rec in self:
            self.env['hospital.room.dashboard'].update_room_dashboard(rec.department_id)

    def create(self, vals):
        rec = super().create(vals)
        rec._update_dashboard()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self._update_dashboard()
        return res

    def unlink(self):
        self._update_dashboard()
        return super().unlink()


class HospitalBed(models.Model):
    _name = 'hospital.bed'
    _description = 'Hospital Bed'
    _order = 'name'

    name = fields.Char(string="Bed Name", required=True)
    room_id = fields.Many2one('hospital.room', string="Room", required=True, ondelete='cascade')
    booking_ids = fields.One2many('hospital.booking', 'bed_id', string="Bookings")
    is_occupied = fields.Boolean(string="Occupied", compute="_compute_is_occupied")

    @api.depends('booking_ids.state')
    def _compute_is_occupied(self):
        occupied_states = ['confirmed', 'invoiced']
        for bed in self:
            bed.is_occupied = any(b.state in occupied_states for b in bed.booking_ids)

    # ============= Auto-update dashboard =============
    def _update_dashboard(self):
        for rec in self:
            if rec.room_id and rec.room_id.department_id:
                self.env['hospital.room.dashboard'].update_room_dashboard(rec.room_id.department_id)

    def create(self, vals):
        rec = super().create(vals)
        rec._update_dashboard()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self._update_dashboard()
        return res

    def unlink(self):
        self._update_dashboard()
        return super().unlink()