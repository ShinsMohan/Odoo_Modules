from odoo import models, fields


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'
    _description = 'Task Stage' 

    is_done = fields.Boolean()