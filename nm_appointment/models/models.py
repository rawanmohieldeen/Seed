# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar as cal
import random
import pytz
from datetime import datetime, timedelta, time
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from babel.dates import format_datetime
from werkzeug.urls import url_join

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang



class CalendarAppointmentType(models.Model):
    _inherit = "calendar.appointment.type"

    product_id = fields.Many2one('product.product',domain="[('reception_ok','=',True)]")

class ReceptionOrder(models.Model):
    _inherit = 'reception.order'

    event = fields.Many2one('calendar.event')
    appointment_type = fields.Many2one('calendar.appointment.type',ondelete='cascade',)
