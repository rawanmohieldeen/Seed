# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from babel.dates import format_datetime, format_date
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import pytz

from werkzeug.exceptions import NotFound
from werkzeug.urls import url_encode

from odoo import http, _, fields
from odoo.http import request
from odoo.osv import expression
from odoo.tools import html2plaintext, is_html_empty, plaintext2html, DEFAULT_SERVER_DATETIME_FORMAT as dtf
from odoo.tools.misc import get_lang

from odoo.addons.base.models.ir_ui_view import keep_query
from odoo.addons.http_routing.models.ir_http import slug

from odoo.addons.appointment.controllers.main import Appointment
from odoo.addons.web.controllers.main import  Home

class WebAppointment(Appointment):


 
    @http.route(['/calendar/<model("calendar.appointment.type"):appointment_type>/submit'], type='http', auth="public", website=True, methods=["POST"])
    def calendar_appointment_submit(self, appointment_type, datetime_str, duration_str, employee_id, name, phone, email, **kwargs):
        """
        Create the event for the appointment and redirect on the validation page with a summary of the appointment.

        :param appointment_type: the appointment type related
        :param datetime_str: the string representing the datetime
        :param employee_id: the employee selected for the appointment
        :param name: the name of the user sets in the form
        :param phone: the phone of the user sets in the form
        :param email: the email of the user sets in the form
        """
        timezone = request.session['timezone'] or appointment_type.appointment_tz
        tz_session = pytz.timezone(timezone)
        date_start = tz_session.localize(fields.Datetime.from_string(datetime_str)).astimezone(pytz.utc)
        duration = float(duration_str)
        date_end = date_start + relativedelta(hours=duration)

        # check availability of the employee again (in case someone else booked while the client was entering the form)
        employee = request.env['hr.employee'].sudo().browse(int(employee_id)).exists()
        if employee not in appointment_type.sudo().employee_ids:
            raise NotFound()
        if employee.user_id and employee.user_id.partner_id:
            if not employee.user_id.partner_id.calendar_verify_availability(date_start, date_end):
                return request.redirect('/calendar/%s/appointment?state=failed-employee' % slug(appointment_type))

        Partner = self._get_customer_partner() or request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)
        if Partner:
            if not Partner.calendar_verify_availability(date_start, date_end):
                return request.redirect('/calendar/%s/appointment?state=failed-partner' % appointment_type.id)
            if not Partner.mobile:
                Partner.write({'mobile': phone})
            if not Partner.email:
                Partner.write({'email': email})
        else:
            Partner = Partner.create({
                'name': name,
                'mobile': Partner._phone_format(phone, country=self._get_customer_country()),
                'email': email,
            })

        description_bits = []
        description = ''
        rec_partner = request.env['reception.customer'].sudo().search([('partner_id','=',Partner.id)], limit=1)
        if not rec_partner:
            rec_partner = request.env['reception.customer'].sudo().create({'name':Partner.name,'partner_id':Partner.id,'email':email})
        if phone:
            description_bits.append(_('Mobile: %s', phone))
        if email:
            description_bits.append(_('Email: %s', email))

        for question in appointment_type.question_ids:
            key = 'question_' + str(question.id)
            if question.question_type == 'checkbox':
                answers = question.answer_ids.filtered(lambda x: (key + '_answer_' + str(x.id)) in kwargs)
                if answers:
                    description_bits.append('%s: %s' % (question.name, ', '.join(answers.mapped('name'))))
            elif question.question_type == 'text' and kwargs.get(key):
                answers = [line for line in kwargs[key].split('\n') if line.strip()]
                description_bits.append('%s:<br/>%s' % (question.name, plaintext2html(kwargs.get(key).strip())))
            elif kwargs.get(key):
                description_bits.append('%s: %s' % (question.name, kwargs.get(key).strip()))
        if description_bits:
            description = '<ul>' + ''.join(['<li>%s</li>' % bit for bit in description_bits]) + '</ul>'

        categ_id = request.env.ref('appointment.calendar_event_type_data_online_appointment')
        alarm_ids = appointment_type.reminder_ids and [(6, 0, appointment_type.reminder_ids.ids)] or []
        partner_ids = list(set([employee.user_id.partner_id.id] + [Partner.id]))
        # FIXME AWA/TDE double check this and/or write some tests to ensure behavior
        # The 'mail_notify_author' is only placed here and not in 'calendar.attendee#_send_mail_to_attendees'
        # Because we only want to notify the author in the context of Online Appointments
        # When creating a meeting from your own calendar in the backend, there is no need to notify yourself
        event = request.env['calendar.event'].with_context(
            mail_notify_author=True,
            allowed_company_ids=employee.user_id.company_ids.ids,
        ).sudo().create({
            'name': _('%s with %s', appointment_type.name, name),
            'start': date_start.strftime(dtf),
            # FIXME master
            # we override here start_date(time) value because they are not properly
            # recomputed due to ugly overrides in event.calendar (reccurrencies suck!)
            #     (fixing them in stable is a pita as it requires a good rewrite of the
            #      calendar engine)
            'start_date': date_start.strftime(dtf),
            'stop': date_end.strftime(dtf),
            'allday': False,
            'duration': duration,
            'description': description,
            'alarm_ids': alarm_ids,
            'location': appointment_type.location,
            'partner_ids': [(4, pid, False) for pid in partner_ids],
            'categ_ids': [(4, categ_id.id, False)],
            'appointment_type_id': appointment_type.id,
            'user_id': employee.user_id.id,
        })
        event.attendee_ids.write({'state': 'accepted'})
        product = appointment_type.product_id
        if product:
            reception_order = request.env['reception.order'].sudo().create({
                'note': _('%s with %s', appointment_type.name, name),
                'partner_id':Partner.id,
                'event':event.id,
                'appointment_type':appointment_type.id,
                'reception_order_line': [(0, 0, {'product_id': product.id,
                                                     'name': product.name,
                                                     'product_uom_qty': 1,
                                                     'product_uom': product.uom_id.id,
                                                     'price_unit': product.list_price,
                                                     'display_type': False})]
                
            })
        return request.redirect('/calendar/view/%s?partner_id=%s&%s' % (event.access_token, Partner.id, keep_query('*', state='new')))

    @http.route([
        '/calendar/cancel/<string:access_token>',
        '/calendar/<string:access_token>/cancel'
    ], type='http', auth="public", website=True)
    def calendar_appointment_cancel(self, access_token, partner_id, **kwargs):
        
        event = request.env['calendar.event'].sudo().search([('access_token', '=', access_token)], limit=1)
        appointment_type = event.appointment_type_id
        Partner = self._get_customer_partner() or request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)
        reception_order = request.env['reception.order'].sudo().search([('appointment_type','=',appointment_type.id),('partner_id','=',Partner.id)])
        if not event:
            return request.not_found()
        if reception_order:
            reception_order.action_cancel()
        res = super().calendar_appointment_cancel( access_token, partner_id, **kwargs)
        return res

    @http.route(['/calendar/<model("calendar.appointment.type"):appointment_type>/info'], type='http', auth="public", website=True, sitemap=True)
    def calendar_appointment_form(self, appointment_type, employee_id, date_time, duration, **kwargs):
        if request.env.user.id == request.env.ref('base.public_user').id:
            return request.render('web.login', {})
        else:
            return super().calendar_appointment_form( appointment_type, employee_id, date_time, duration, **kwargs)



class AuthSignupHome(Home):


    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        res = super().web_auth_signup(*args, **kw)
        user = request.env.user
        customer = request.env['reception.customer'].sudo().create({
                'name': user.name,
                })
        return res