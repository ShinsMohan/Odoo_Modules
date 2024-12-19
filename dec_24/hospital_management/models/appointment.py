from odoo import models, fields

class Appointment(models.Model):
    _name = 'appointment.appointment'
    _description = 'Appointment Management'

    patients_id = fields.Char(string='Patients ID')
    patient_name = fields.Many2one('res.partner', string='Patient Name')
    appointment_id = fields.Char(string='Appointment ID')
    token = fields.Char(string='Token')
    qid = fields.Char(string='QID')
    qid_expiry_date = fields.Date(string='QID Expiry Date')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    patient_phone = fields.Char(string='Patient Phone')
    sms_by_whatsapp = fields.Boolean(string='SMS By Whatsapp')
    nationality = fields.Many2one('res.country', string='Nationality')
    passport_number = fields.Char(string='Passport Number')
    date_of_birth = fields.Date(string='Date of Birth')
    age = fields.Char(string='Age')
    email = fields.Char(string='Email')
    primary_diagnosis = fields.Char(string='Primary Diagnosis')
    vehicle_no = fields.Char(string='Vehicle No')
    billing_type = fields.Selection([
        ('cash', 'Cash OR Card'),
        ('corporate', 'Corporate'),
        ('insurance', 'Insurance')
    ], string='Billing Type')
    department = fields.Char(string='Department')
    doctor = fields.Many2one('hr.employee', string='Doctor')
    appointment_date = fields.Date(string='Appointment Date')
    appointment_start = fields.Datetime(string='Appointment Start')
    appointment_type = fields.Selection([
        ('walk_in', 'Walk In'),
        ('appointment', 'Come with Appointment')
    ], string='Appointment Type')
    patient_status = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Patient Status')
    note = fields.Text(string='Note')
    slot = fields.Char(string='Slot')
    company = fields.Many2one('res.company', string='Company')
    operating_unit = fields.Char(string='Operating Unit')
    payment_line_ids = fields.One2many('appointment.payment.line', 'appointment_id', string='Payment Lines')
    status = fields.Selection([
        ('booked', 'Booked'),
        ('confirmed', 'Confirmed'),
        ('token_generated', 'Token Generated'),
        ('checked_in', 'Checked In'),
        ('billed', 'Billed'),
        ('in_chair', 'In Chair'),
        ('consulted', 'Consulted'),
        ('completed', 'Completed'),
        ('visit_closed', 'Visit Closed')
    ], string='Appointment Status', default='booked')

    def action_change_status(self):
        state_transition = {
            'booked': 'confirmed',
            'confirmed': 'token_generated',
            'token_generated': 'checked_in',
            'checked_in': 'billed',
            'billed': 'in_chair',
            'in_chair': 'consulted',
            'consulted': 'completed',
            'completed': 'visit_closed',
            'visit_closed': 'booked'
        }

    def action_confirm(self):
        for record in self:
            if record.status == 'booked':
                record.status = 'confirmed'

    def action_token_generated(self):
        for record in self:
            if record.status == 'confirmed':
                record.status = 'token_generated'

    def action_checked_in(self):
        for record in self:
            if record.status == 'token_generated':
                record.status = 'checked_in'

    def action_billed(self):
        for record in self:
            if record.status == 'checked_in':
                record.status = 'billed'

    def action_in_chair(self):
        for record in self:
            if record.status == 'billed':
                record.status = 'in_chair'

    def action_consulted(self):
        for record in self:
            if record.status == 'in_chair':
                record.status = 'consulted'

    def action_completed(self):
        for record in self:
            if record.status == 'consulted':
                record.status = 'completed'

    def action_visit_closed(self):
        for record in self:
            if record.status == 'completed':
                record.status = 'visit_closed'

    def action_reset_to_draft(self):
        for record in self:
            if record.status == 'visit_closed':
                record.status = 'booked'