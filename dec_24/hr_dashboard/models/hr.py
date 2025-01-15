from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    joining_date = fields.Date()


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    joining_date = fields.Date()