from odoo import models, fields, api

class PaymentLine(models.Model):
    _name = 'appointment.payment.line'
    _description = 'Payment Line for Appointment'
    
    appointment_id = fields.Many2one('appointment.appointment', string='Appointment', required=True)
    treatment = fields.Many2one('product.product', string='Treatment')
    description = fields.Text(string='Description')
    actual_amount = fields.Float(string='Actual Amount')
    discount_percent = fields.Float(string='Discount (%)')
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount', store=True)
    after_discount_amount = fields.Float(string='After Discount Amount', compute='_compute_after_discount', store=True)
    need_approval = fields.Boolean(string='Need Approval')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending')

    @api.depends('actual_amount', 'discount_percent')
    def _compute_discount(self):
        for line in self:
            line.discount_amount = (line.actual_amount * line.discount_percent) / 100

    @api.depends('actual_amount', 'discount_amount')
    def _compute_after_discount(self):
        for line in self:
            line.after_discount_amount = line.actual_amount - line.discount_amount
