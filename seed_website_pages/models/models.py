# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = "res.company"

    arabic_logo = fields.Binary()

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    arabic_logo = fields.Binary(related="company_id.arabic_logo",readonly=False)
