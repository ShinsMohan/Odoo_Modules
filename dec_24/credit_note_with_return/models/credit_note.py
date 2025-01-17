from datetime import datetime
from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError, ValidationError

class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'
    
    return_product = fields.Boolean()
    location_id = fields.Many2one('stock.location', domain="[('usage', '=', 'internal')]")

    def reverse_moves(self, is_modify=False):
        if self.return_product:
            for move in self.move_ids:
                move.return_product = True
                move.location_id = self.location_id if self.location_id else False
        return super().reverse_moves()
    
    @api.constrains('location_id', 'return_product')
    def location_constrain(self):
        if self.location_id and not self.return_product:
            raise UserError(_('Return Product should be checked if Location is selected.'))
    

class AccountMove(models.Model):
    _inherit = 'account.move'

    return_product = fields.Boolean()
    location_id = fields.Many2one('stock.location')

    def button_draft(self):
        if self.return_product and self.reversed_entry_id:
            raise ValidationError(_("You can't draft credit note with stock movement"))
        return super().button_draft()
        
    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.return_product:
            self._return_product(self.location_id if self.location_id else None)
        return res
    
    def _return_product(self, location_id = None):
        # Getting the Sale against invoice
        sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])
        if sale_order:
            # Getting the Pickings against Sale Order
            pickings = self.env['stock.picking'].search([('origin', '=', sale_order.name)])
            for picking in pickings:
                if picking.state != 'done':
                    raise UserError(_('You may only return Done pickings.'))
                move_lines = []
                # Check if location is passed. If not, fall back to original picking location
                if location_id:
                    location = location_id
                    location_warehouse = location_id.warehouse_id.id
                    picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', location_warehouse)])
                else:
                    location = picking.location_id
                    # picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id', '=', picking.picking_type_id.warehouse_id.id)])
                    picking_type = picking.picking_type_id.return_picking_type_id
                for each in self.invoice_line_ids.filtered(lambda x: x.product_id.detailed_type == 'product' and x.quantity > 0):
                    sale_line = each.sale_line_ids
                    # Get the stock moves related to the sale line in the original picking (if exists)
                    origin_stock_move = sale_line.mapped('move_ids').filtered(lambda x: x.picking_id == picking)
                    quantity_delivered = sum(sale_line.mapped('qty_delivered'))
                    if each.quantity > quantity_delivered:
                        raise UserError(_('You cannot return more than the quantity delivered.'))
                    move_values = {
                        'origin': sale_order.name,
                        'name': each.product_id.name,
                        'product_id': each.product_id.id,
                        'product_uom_qty': each.quantity,
                        'product_uom': each.product_id.uom_id.id,
                        'location_id': picking.location_dest_id.id,
                        'location_dest_id': location.id,
                        'procure_method': 'make_to_stock',
                        'origin_returned_move_id': origin_stock_move.id if origin_stock_move else False,
                        'sale_line_id': sale_line[0].id if sale_line else False,
                        'to_refund': True,
                        'warehouse_id': picking.picking_type_id.warehouse_id.id,
                        'move_orig_ids': [Command.link(origin_stock_move.id)],
                        'group_id': picking.group_id.id
                    }
                    move_lines.append((0, 0, move_values))
                # Creating return picking with move lines
                picking_values = {
                    'origin': f'Return of {picking.name}',
                    'scheduled_date': datetime.now(),
                    'date_done': datetime.now(),
                    'partner_id': picking.partner_id.id,
                    'picking_type_id': picking_type.id,
                    'location_id': picking.location_dest_id.id,
                    'location_dest_id': location.id,
                    'move_type': 'direct',
                    'move_ids': move_lines,
                    'return_id': picking.id,
                    'group_id': picking.group_id.id,
                    'sale_id': sale_order.id
                }
                return_picking = self.env['stock.picking'].create(picking_values)
                return_picking.write({'sale_id': sale_order.id, 'group_id': picking.group_id.id})
                return_picking.action_confirm()
                return_picking.action_assign()
                return_picking.button_validate()

        # Purchase Order
        purchase_order = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])
        if purchase_order:
            # Getting the Pickings against Purchase Order
            pickings = self.env['stock.picking'].search([('origin', '=', purchase_order.name)])
            for picking in pickings:
                if picking.state != 'done':
                    raise UserError(_('You may only return Done pickings.'))
                move_lines = []
                # Check if location is passed. If not, fall back to original picking location
                if location_id:
                    location = location_id
                    location_warehouse = location_id.warehouse_id.id
                    picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', location_warehouse)])
                else:
                    location = picking.location_dest_id
                    picking_type = picking.picking_type_id.return_picking_type_id
                for each in self.invoice_line_ids.filtered(lambda x: x.product_id.detailed_type == 'product' and x.quantity > 0):
                    purchase_line = each.purchase_line_id
                    # Get the stock moves related to the purchase line in the original picking (if exists)
                    origin_stock_move = purchase_line.mapped('move_ids').filtered(lambda x: x.picking_id == picking)
                    quantity_received = sum(purchase_line.mapped('qty_received'))
                    if each.quantity > quantity_received:
                        raise UserError(_('You cannot return more than the quantity received.'))
                    if each.product_id.with_context(location = location.id).free_qty < each.quantity:
                        raise UserError(_('Quantity is not available for this location'))
                    move_values = {
                        'origin': purchase_order.name,
                        'name': each.product_id.name,
                        'product_id': each.product_id.id,
                        'product_uom_qty': each.quantity,
                        'quantity': each.quantity,
                        'product_uom': each.product_id.uom_id.id,
                        'location_id': location.id,
                        'location_dest_id': picking.location_id.id,
                        'procure_method': 'make_to_stock',
                        'origin_returned_move_id': origin_stock_move.id if origin_stock_move else False,
                        'purchase_line_id': purchase_line.id if purchase_line else False,
                        'to_refund': True,
                        'warehouse_id': picking.picking_type_id.warehouse_id.id,
                        'move_orig_ids': [Command.link(origin_stock_move.id)],
                        'group_id': picking.group_id.id
                    }
                    move_lines.append((0, 0, move_values))
                # Creating return picking with move lines
                picking_values = {
                    'origin': f'Return of {picking.name}',
                    'scheduled_date': datetime.now(),
                    'date_done': datetime.now(),
                    'partner_id': picking.partner_id.id,
                    'picking_type_id': picking_type.id,
                    'location_id': location.id,
                    'location_dest_id': picking.location_id.id,
                    'move_type': 'direct',
                    'move_ids': move_lines,
                    'return_id': picking.id,
                    'group_id': picking.group_id.id,
                    'purchase_id': purchase_order.id
                }
                return_picking = self.env['stock.picking'].create(picking_values)
                return_picking.write({'purchase_id': purchase_order.id, 'group_id': picking.group_id.id})
                return_picking.action_confirm()
                return_picking.action_assign()
                return_picking.button_validate()



    # def _create_return_picking(self, picking, move_lines, picking_type, origin, partner_id, order_id, order_field):
    #     """Helper function to create return picking."""
    #     picking_values = {
    #         'origin': f'Return of {picking.name}',
    #         'scheduled_date': datetime.now(),
    #         'date_done': datetime.now(),
    #         'partner_id': partner_id,
    #         'picking_type_id': picking_type.id,
    #         'location_id': picking.location_dest_id.id,
    #         'location_dest_id': picking.location_id.id,
    #         'move_type': 'direct',
    #         'move_ids': move_lines,
    #         'return_id': picking.id,
    #         'group_id': picking.group_id.id,
    #         order_field: order_id,
    #     }
    #     return_picking = self.env['stock.picking'].create(picking_values)
    #     return_picking.write({order_field: order_id, 'group_id': picking.group_id.id})
    #     return_picking.action_confirm()
    #     return_picking.action_assign()
    #     return_picking.button_validate()
    #     return return_picking

    # def _prepare_move_lines(self, picking, order, line, location, origin_stock_move, move_type):
    #     """Helper function to prepare move lines for the return picking."""
    #     return_vals = {
    #         'origin': order.name,
    #         'name': line.product_id.name,
    #         'product_id': line.product_id.id,
    #         'product_uom_qty': line.quantity,
    #         'product_uom': line.product_id.uom_id.id,
    #         'location_id': picking.location_dest_id.id,
    #         'location_dest_id': location.id,
    #         'procure_method': 'make_to_stock',
    #         'origin_returned_move_id': origin_stock_move.id if origin_stock_move else False,
    #         'to_refund': True,
    #         'warehouse_id': picking.picking_type_id.warehouse_id.id,
    #         'move_orig_ids': [Command.link(origin_stock_move.id)] if origin_stock_move else [],
    #         'group_id': picking.group_id.id,
    #     }
    #     if move_type == 'purchase':
    #         return_vals.update({'purchase_line_id': line.purchase_line_id.id if line.purchase_line_id else False, 'partner_id': picking.partner_id.id})
    #     else:
    #         return_vals.update({'sale_line_id': line.sale_line_ids[0].id if line.sale_line_ids else False})
        
    #     return return_vals

    # def _process_return(self, order, picking, location_id, move_type):
    #     """Helper function to process the return for both sale and purchase orders."""
    #     move_lines = []
    #     location = location_id or (picking.location_id if move_type == 'sale' else picking.location_dest_id)
    #     warehouse_id = location.warehouse_id.id if location_id else picking.picking_type_id.warehouse_id.id
    #     picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming' if move_type == 'sale' else 'outgoing'), ('warehouse_id', '=', warehouse_id)], limit=1)

    #     for line in self.invoice_line_ids.filtered(lambda x: x.product_id.detailed_type == 'product' and x.quantity > 0):
    #         related_line = line.sale_line_ids if move_type == 'sale' else line.purchase_line_id
    #         # related_line = getattr(line, f'{move_type}_line_ids')
    #         origin_stock_move = related_line.mapped('move_ids').filtered(lambda x: x.picking_id == picking)
    #         delivered_or_received_qty = sum(related_line.mapped('qty_delivered') if move_type == 'sale' else related_line.mapped('qty_received'))

    #         if line.quantity > delivered_or_received_qty:
    #             raise UserError(_('You cannot return more than the quantity %s.') % ('delivered' if move_type == 'sale' else 'received'))

    #         if move_type == 'purchase' and line.product_id.with_context(location=location.id).free_qty < line.quantity:
    #             raise UserError(_('Quantity is not available for this location'))

    #         move_lines.append((0, 0, self._prepare_move_lines(picking, order, line, location, origin_stock_move, move_type)))

    #     return self._create_return_picking(picking, move_lines, picking_type, order.name, picking.partner_id.id, order.id, f'{move_type}_id')

    # def _return_product(self, location_id=None):
    #     """Main function to handle product returns for sale or purchase orders."""
    #     sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)], limit=1)
    #     if sale_order:
    #         pickings = self.env['stock.picking'].search([('origin', '=', sale_order.name)])
    #         for picking in pickings:
    #             if picking.state != 'done':
    #                 raise UserError(_('You may only return Done pickings.'))
    #             return self._process_return(sale_order, picking, location_id, 'sale')

    #     purchase_order = self.env['purchase.order'].search([('name', '=', self.invoice_origin)], limit=1)
    #     if purchase_order:
    #         pickings = self.env['stock.picking'].search([('origin', '=', purchase_order.name)])
    #         for picking in pickings:
    #             if picking.state != 'done':
    #                 raise UserError(_('You may only return Done pickings.'))
    #             return self._process_return(purchase_order, picking, location_id, 'purchase')


        

