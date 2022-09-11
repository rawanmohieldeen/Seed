from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ReceptionOrder(models.Model):
    _name = 'reception.order'
    _description = 'Reception Orders'
    _inherits = {'sale.order': 'sale_order_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    sale_order_id = fields.Many2one(comodel_name='sale.order',
                                    string='Related Sale Order',
                                    required=True, readonly=True, ondelete='cascade', tracking=True)
    treatment_state = fields.Selection([
        ('draft', 'Draft'),
        ('sale', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    product_choice_id = fields.Many2one('product.product', string='Product',
                                        change_default=True, readonly=False, invisible=True,
                                        states={'draft': [('invisible', False)]},
                                        domain="[('reception_ok', '=', True)]")
    reception_order_line = fields.One2many('reception.order.line', 'reception_order_id', string='Order Lines',
                                           states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
                                           copy=True, auto_join=True)

    @api.onchange('product_choice_id')
    def _onchange_product_choice_id(self):
        product = self.product_choice_id
        if product:
            self.reception_order_line = [(0, 0, {'product_id': product.id,
                                                 'name': product.name,
                                                 'product_uom_qty': 1,
                                                 'product_uom': product.uom_id.id,
                                                 'price_unit': 1,
                                                 'display_type': False})]
            for line in self.reception_order_line:
                if self.pricelist_id and self.partner_id:
                    product1 = product.with_context(
                        lang=self.partner_id.lang,
                        partner=self.partner_id,
                        quantity=line.product_uom_qty,
                        date=self.date_order,
                        pricelist=self.pricelist_id.id,
                        uom=line.product_uom.id,
                        fiscal_position=self.env.context.get('fiscal_position')
                    )
                    line.price_unit = product1._get_tax_included_unit_price(
                        self.company_id,
                        self.currency_id,
                        self.date_order,
                        'sale',
                        fiscal_position=self.fiscal_position_id,
                        product_price_unit=line._get_display_price(product1),
                        product_currency=self.currency_id
                    )

    def _set_reception_order_line(self):
        move_finished_ids = self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id)
        self.move_finished_ids = move_finished_ids | self.move_byproduct_ids

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.sale_order_id.onchange_partner_id()

    # @api.constrains('order_line')
    # def _check_order_line(self):
    #     for order in self:
    #         if len(order.reception_order_line) < 1:
    #             pass
    #             raise ValidationError(_('A reception order must have at least one product.'))

    @api.onchange('country')
    def _onchange_country_id(self):
        if self.country and self.country != self.state.country_id:
            self.state = False

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        res = super(ReceptionOrder, self).create(vals)
        # res._check_order_line()
        for order in res:
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        for line in res.reception_order_line:
            line.order_id = res.sale_order_id.id
        return res

    def write(self, vals):
        res = super(ReceptionOrder, self).write(vals)
        self._check_order_line()
        return res

    def action_confirm(self):
        for order in self:
            order.sale_order_id.action_confirm()
            order.treatment_state = 'sale'
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
            template_id = self.env.ref('nm_health_wellness_reception_sales.reception_order_confirmation')
            order.with_context(force_send=True).message_post_with_template(template_id.id)

    def action_cancel(self):
        for order in self:
            order.sale_order_id.action_cancel()
            order.treatment_state = 'cancel'

    def action_draft(self):
        for order in self:
            order.sale_order_id.action_draft()
            order.treatment_state = 'draft'

    def preview_sale_order(self):
        for order in self:
            return order.sale_order_id.preview_sale_order()

    def action_view_invoice(self):
        for order in self:
            return order.sale_order_id.action_view_invoice()

    def action_view_project_ids(self):
        for order in self:
            return order.sale_order_id.action_view_project_ids()

    def action_view_task(self):
        for order in self:
            return order.sale_order_id.action_view_task()


class ReceptionOrderLine(models.Model):
    _name = 'reception.order.line'
    _description = 'Reception Order Lines'
    _inherits = {'sale.order.line': 'sale_order_line_id'}

    sale_order_line_id = fields.Many2one(comodel_name='sale.order.line',
                                         string='Related Sale Order Line',
                                         required=True, readonly=True, ondelete='cascade', tracking=True)
    reception_order_id = fields.Many2one('reception.order', string='Order Reference', required=True, ondelete='cascade',
                                         index=True, copy=False)

    @api.model
    def create(self, vals):
        res = super(ReceptionOrderLine, self).create(vals)
        return res

    def _get_display_price(self, product):
        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        no_variant_attributes_price_extra = [
            ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
                lambda ptav:
                ptav.price_extra and
                ptav not in product.product_template_attribute_value_ids
            )
        ]
        if no_variant_attributes_price_extra:
            product = product.with_context(
                no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
            )

        if self.reception_order_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.reception_order_id.pricelist_id.id,
                                        uom=self.product_uom.id).price
        product_context = dict(self.env.context, partner_id=self.reception_order_id.partner_id.id,
                               date=self.reception_order_id.date_order, uom=self.product_uom.id)

        final_price, rule_id = self.reception_order_id.pricelist_id.with_context(
            product_context).get_product_price_rule(product or self.product_id, self.product_uom_qty or 1.0,
                                                    self.reception_order_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           self.product_uom_qty,
                                                                                           self.product_uom,
                                                                                           self.reception_order_id.pricelist_id.id)
        if currency != self.reception_order_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.reception_order_id.pricelist_id.currency_id,
                self.reception_order_id.company_id or self.env.company,
                self.reception_order_id.date_order or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.onchange('product_id')
    def product_id_change(self):
        if self.reception_order_id.pricelist_id and self.reception_order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.reception_order_id.partner_id.lang,
                partner=self.reception_order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.reception_order_id.date_order,
                pricelist=self.reception_order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = product._get_tax_included_unit_price(
                self.company_id or self.reception_order_id.company_id,
                self.reception_order_id.currency_id,
                self.reception_order_id.date_order,
                'sale',
                fiscal_position=self.reception_order_id.fiscal_position_id,
                product_price_unit=self._get_display_price(product),
                product_currency=self.reception_order_id.currency_id
            )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_id = fields.Many2one('sale.order', string='Order Reference', required=False, ondelete='cascade', index=True, copy=False)
