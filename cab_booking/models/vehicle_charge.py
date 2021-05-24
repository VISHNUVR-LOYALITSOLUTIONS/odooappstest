# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    hr_rent = fields.Integer(string="Hourly billing rate")
    product_id = fields.Many2one('product.product', string="Product", domain=[('sale_ok', '=', True)])
