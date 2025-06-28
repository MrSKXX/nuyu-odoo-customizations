from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RoomTransfer(models.Model):
    _name = 'medical.room.transfer'
    _description = 'Room to Room Transfer'
    _order = 'date desc'
    
    name = fields.Char(string='Transfer Reference', required=True, default=lambda self: _('New'))
    date = fields.Datetime(string='Transfer Date', default=fields.Datetime.now, required=True)
    source_location_id = fields.Many2one('stock.location', string='From Location', required=True)
    dest_location_id = fields.Many2one('stock.location', string='To Location', required=True)
    responsible_user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')
    
    line_ids = fields.One2many('medical.room.transfer.line', 'transfer_id', string='Products')
    notes = fields.Text(string='Notes')
    
    stock_picking_id = fields.Many2one('stock.picking', string='Internal Transfer', readonly=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('medical.room.transfer') or _('New')
        return super().create(vals)
    
    @api.constrains('source_location_id', 'dest_location_id')
    def _check_locations(self):
        for record in self:
            if record.source_location_id == record.dest_location_id:
                raise ValidationError(_('Source and destination locations cannot be the same.'))
    
    def action_confirm(self):
        self._create_stock_picking()
        self.state = 'confirmed'
    
    def action_done(self):
        if self.stock_picking_id:
            self.stock_picking_id.action_confirm()
            self.stock_picking_id.action_done()
        self.state = 'done'
        
    def action_cancel(self):
        if self.stock_picking_id and self.stock_picking_id.state not in ['done', 'cancel']:
            self.stock_picking_id.action_cancel()
        self.state = 'cancelled'
    
    def _create_stock_picking(self):
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', '=', self.env.company.id)
        ], limit=1)
        
        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'origin': self.name,
            'move_ids_without_package': [(0, 0, {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.dest_location_id.id,
            }) for line in self.line_ids]
        }
        
        picking = self.env['stock.picking'].create(picking_vals)
        self.stock_picking_id = picking.id

class RoomTransferLine(models.Model):
    _name = 'medical.room.transfer.line'
    _description = 'Room Transfer Line'
    
    transfer_id = fields.Many2one('medical.room.transfer', string='Transfer', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Batch')
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    quantity_available = fields.Float(string='Available', compute='_compute_available')
    
    @api.depends('product_id', 'lot_id', 'transfer_id.source_location_id')
    def _compute_available(self):
        for line in self:
            if line.product_id and line.transfer_id.source_location_id:
                domain = [
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.transfer_id.source_location_id.id),
                ]
                if line.lot_id:
                    domain.append(('lot_id', '=', line.lot_id.id))
                
                quants = self.env['stock.quant'].search(domain)
                line.quantity_available = sum(quants.mapped('quantity'))
            else:
                line.quantity_available = 0.0
    
    @api.onchange('quantity', 'quantity_available')
    def _check_quantity(self):
        if self.quantity > self.quantity_available:
            return {
                'warning': {
                    'title': _('Insufficient Stock'),
                    'message': _('Requested quantity (%.2f) exceeds available stock (%.2f)') % 
                              (self.quantity, self.quantity_available)
                }
            }