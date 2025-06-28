from odoo import models, fields, api
from datetime import datetime, timedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    medical_category = fields.Selection([
        ('injectable', 'Injectable'),
        ('consumable', 'Medical Consumable'),
        ('retail', 'Retail Product'),
        ('device', 'Medical Device'),
    ], string='Medical Category')
    
    requires_expiry = fields.Boolean(string='Requires Expiry Tracking', default=True)
    requires_batch = fields.Boolean(string='Requires Batch/Lot Tracking', default=True)
    requires_refrigeration = fields.Boolean(string='Requires Refrigeration')
    refrigeration_temp_min = fields.Float(string='Min Temperature (°C)')
    refrigeration_temp_max = fields.Float(string='Max Temperature (°C)')
    
    is_consignment = fields.Boolean(string='Consignment Product')
    consignment_supplier_id = fields.Many2one('res.partner', string='Consignment Supplier')
    
    default_shelf_life_days = fields.Integer(string='Default Shelf Life (Days)', default=365)
    minimum_stock_days = fields.Integer(string='Minimum Stock Alert (Days)', default=30)
    
    @api.onchange('medical_category')
    def _onchange_medical_category(self):
        if self.medical_category == 'injectable':
            self.requires_expiry = True
            self.requires_batch = True
            self.requires_refrigeration = True
            self.refrigeration_temp_min = 2.0
            self.refrigeration_temp_max = 8.0
        elif self.medical_category == 'device':
            self.requires_expiry = False
            self.requires_batch = True
            self.requires_refrigeration = False
            
    @api.model
    def create(self, vals):
        if vals.get('medical_category'):
            vals['tracking'] = 'lot' if vals.get('requires_batch', True) else 'none'
        return super().create(vals)

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    def get_expiry_status(self):
        today = datetime.now().date()
        quants = self.env['stock.quant'].search([('product_id', '=', self.id), ('quantity', '>', 0)])
        
        statuses = {
            'expired': 0,
            'expiring_soon': 0,
            'good': 0
        }
        
        for quant in quants:
            if quant.lot_id and hasattr(quant.lot_id, 'expiration_date') and quant.lot_id.expiration_date:
                exp_date = quant.lot_id.expiration_date.date()
                days_to_expiry = (exp_date - today).days
                
                if days_to_expiry < 0:
                    statuses['expired'] += quant.quantity
                elif days_to_expiry <= self.minimum_stock_days:
                    statuses['expiring_soon'] += quant.quantity
                else:
                    statuses['good'] += quant.quantity
                    
        return statuses