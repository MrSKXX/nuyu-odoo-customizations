from odoo import models, fields, api

class CustomProduct(models.Model):
    _inherit = 'product.template'
    
    custom_field = fields.Char(string='Custom Field')
    
    @api.model
    def custom_method(self):
        return "This is my custom code!"