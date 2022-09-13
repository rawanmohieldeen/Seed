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
from odoo.addons.website.controllers.main import Website


class Website(Home):

    @http.route(['/services'], type='http', auth="public", website=True, sitemap=False)
    def return_rule_data(self, **kwargs):
        return request.render('nm_health_wellness_website.services_page')
    @http.route(['/about'], type='http', auth="public", website=True, sitemap=False)
    def terms_cond_data(self, **kwargs):
        return request.render('nm_health_wellness_website.aboutus_page')

    @http.route(['/packages'], type='http', auth="public", website=True, sitemap=False)
    def return_rule_data(self, **kwargs):
        return request.render('nm_health_wellness_website.packages_page')




# class Website(Website):

#     @http.route(auth='public')
#     def index(self, **kw):
#         super(Website, self).index()
#         print('-------***********************-')
#         return http.request.render('nm_health_wellness_website.homepage_seed', {})