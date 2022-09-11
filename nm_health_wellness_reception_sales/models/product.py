# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    reception_ok = fields.Boolean('Available in Reception', default=False)

