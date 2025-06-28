from odoo import models, fields, api
from datetime import datetime, timedelta

class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    location_type = fields.Selection([
        ('warehouse', 'Main Warehouse'),
        ('room1', 'Treatment Room 1'),
        ('room2', 'Treatment Room 2'), 
        ('room3', 'Treatment Room 3'),
        ('doctor_private', 'Doctor Private Stock'),
        ('refrigerated', 'Refrigerated Storage'),
    ], string='Medical Location Type')
    
    has_refrigeration = fields.Boolean(string='Has Refrigeration')
    temperature_min = fields.Float(string='Min Temperature (°C)')
    temperature_max = fields.Float(string='Max Temperature (°C)')
    responsible_user_id = fields.Many2one('res.users', string='Responsible Person')

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    is_consignment = fields.Boolean(string='Consignment Stock', default=False)
    consignment_line_id = fields.Many2one('medical.consignment.line', string='Consignment Line')
    expiry_status = fields.Selection([
        ('good', 'Good'),
        ('expiring_soon', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string='Expiry Status', compute='_compute_expiry_status', store=True)
    
    days_to_expiry = fields.Integer(string='Days to Expiry', compute='_compute_expiry_status', store=True)
    
    @api.depends('lot_id.expiration_date')
    def _compute_expiry_status(self):
        today = datetime.now().date()
        for quant in self:
            if quant.lot_id and quant.lot_id.expiration_date:
                exp_date = quant.lot_id.expiration_date.date()
                days_diff = (exp_date - today).days
                quant.days_to_expiry = days_diff
                
                if days_diff < 0:
                    quant.expiry_status = 'expired'
                elif days_diff <= quant.product_id.minimum_stock_days:
                    quant.expiry_status = 'expiring_soon'
                else:
                    quant.expiry_status = 'good'
            else:
                quant.days_to_expiry = 0
                quant.expiry_status = 'good'

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    is_room_transfer = fields.Boolean(string='Room Transfer', default=False)
    transfer_reason = fields.Text(string='Transfer Reason')

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    is_room_transfer = fields.Boolean(string='Room Transfer', default=False)
    medical_notes = fields.Text(string='Medical Notes')
    
    def _get_room_transfer_data(self):
        return {
            'source_location': self.location_id.name,
            'dest_location': self.location_dest_id.name,
            'products': [(move.product_id.name, move.product_uom_qty) for move in self.move_ids_without_package]
        }

class StockLot(models.Model):
    _inherit = 'stock.lot'
    
    medical_batch_info = fields.Text(string='Medical Batch Information')
    supplier_batch_number = fields.Char(string='Supplier Batch Number')
    received_date = fields.Date(string='Received Date', default=fields.Date.context_today)
    storage_requirements = fields.Text(string='Storage Requirements')
    
    @api.model
    def get_expiring_lots(self, days=30):
        cutoff_date = datetime.now().date() + timedelta(days=days)
        return self.search([
            ('expiration_date', '<=', cutoff_date),
            ('expiration_date', '>=', datetime.now().date())
        ])