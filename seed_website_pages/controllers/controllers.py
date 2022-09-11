# -*- coding: utf-8 -*-
import base64
import datetime
import json
import os
import logging
import pytz
import requests
import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers

from itertools import islice
from werkzeug import urls
from xml.etree import ElementTree as ET

import odoo
from odoo.http import content_disposition, Controller, request, route

from odoo import http, models, fields, _
from odoo.http import request
from odoo.tools import OrderedSet
from odoo.addons.http_routing.models.ir_http import slug, slugify, _guess_mimetype
from odoo.addons.web.controllers.main import Binary
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.portal.controllers.web import Home
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.appointment.controllers.main import Appointment


class Website(Home):

    @http.route(['/services'], type='http', auth="public", website=True, sitemap=False)
    def return_rule_data(self, **kwargs):
        return request.render('seed_website_pages.services_page')
    @http.route(['/about'], type='http', auth="public", website=True, sitemap=False)
    def terms_cond_data(self, **kwargs):
        return request.render('seed_website_pages.aboutus_page')

    @http.route(['/packages'], type='http', auth="public", website=True, sitemap=False)
    def return_rule_data(self, **kwargs):
        return request.render('seed_website_pages.packages_page')




class WebAppointment(Appointment):


    @http.route(['/calendar/<model("calendar.appointment.type"):appointment_type>/submit'], type='http', auth="public", website=True, methods=["POST"])
    def calendar_appointment_submit(self, appointment_type, datetime_str, duration_str, employee_id, name, phone, email, **kwargs):
        res = super().calendar_appointment_submit(appointment_type, datetime_str, duration_str, employee_id, name, phone, email, **kwargs)
        Partner = self._get_customer_partner() or request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)
        reception_order = request.env['reception.order'].sudo().create({
            'name': _('%s with %s', appointment_type.name, name),
            'partner_id':Partner.id,
            
        })
        return res