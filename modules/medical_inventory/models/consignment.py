from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ConsignmentInventory(models.Model):
    _name = 'medical.consignment'
    _description = 'Consignment Inventory Tracking'
    _order = 'date desc'
    
    name = fields.Char(string='Reference', required=True, default=lambda self: _('New'))
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    supplier_id = fields.Many2one('res.partner', string='Consignment Supplier', required=True)
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('settled', 'Settled'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    line_ids = fields.One2many('medical.consignment.line', 'consignment_id', string='Products')
    total_value = fields.Monetary(string='Total Value', compute='_compute_total_value', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.consignment') or _('New')
        return super().create(vals)
    
    @api.depends('line_ids.total_value')
    def _compute_total_value(self):
        for record in self:
            record.total_value = sum(line.total_value for line in record.line_ids)
    
    def action_activate(self):
        self.state = 'active'
        for line in self.line_ids:
            line._update_stock_quant()
    
    def action_settle(self):
        for line in self.line_ids:
            if line.quantity_used > 0:
                line._create_settlement_move()
        self.state = 'settled'

class ConsignmentLine(models.Model):
    _name = 'medical.consignment.line'
    _description = 'Consignment Inventory Line'
    
    consignment_id = fields.Many2one('medical.consignment', string='Consignment', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Batch')
    quantity_received = fields.Float(string='Qty Received', required=True)
    quantity_used = fields.Float(string='Qty Used', readonly=True)
    quantity_remaining = fields.Float(string='Qty Remaining', compute='_compute_remaining')
    unit_cost = fields.Monetary(string='Unit Cost', currency_field='currency_id')
    total_value = fields.Monetary(string='Total Value', compute='_compute_total', currency_field='currency_id')
    currency_id = fields.Many2one(related='consignment_id.currency_id')
    
    @api.depends('quantity_received', 'quantity_used')
    def _compute_remaining(self):
        for line in self:
            line.quantity_remaining = line.quantity_received - line.quantity_used
    
    @api.depends('quantity_received', 'unit_cost')
    def _compute_total(self):
        for line in self:
            line.total_value = line.quantity_received * line.unit_cost
    
    def _update_stock_quant(self):
        quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.consignment_id.location_id.id),
            ('lot_id', '=', self.lot_id.id if self.lot_id else False)
        ], limit=1)
        
        if quant:
            quant.is_consignment = True
            quant.consignment_line_id = self.id
        
    def _create_settlement_move(self):
        move_vals = {
            'name': f'Consignment Settlement: {self.product_id.name}',
            'product_id': self.product_id.id,
            'product_uom': self.product_id.uom_id.id,
            'product_uom_qty': self.quantity_used,
            'location_id': self.consignment_id.location_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'partner_id': self.consignment_id.supplier_id.id,
        }
        move = self.env['stock.move'].create(move_vals)
        move._action_confirm()
        move._action_done()