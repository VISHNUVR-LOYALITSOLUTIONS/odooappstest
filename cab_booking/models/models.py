# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class CabBooking(models.Model):
    _name = 'cab_booking.cab_booking'
    _inherit = 'mail.thread'
    _description = 'Cab Booking'

    name = fields.Char(string="Service Number", readonly=True, required=True, copy=False, default='New')
    customer = fields.Many2one('res.partner', string="Customer", required=True)
    date_start = fields.Datetime('Start Date', required=True, readonly=False, select=True,
                                 default=lambda self: fields.datetime.now())
    date_end = fields.Datetime('End Date', required=True, readonly=False, select=True)
    driver = fields.Many2one('res.users', string="Driver", required=True)
    location = fields.Char(string="Location")
    car = fields.Many2one('fleet.vehicle', string="Car", required=True)
    description = fields.Text()
    state = fields.Selection([('draft', 'Draft'), ('assigned', 'Assigned'), ('running', 'Running'), ('done', 'Done'),
                              ('invoiced', 'Invoiced'), ('cancel', 'Cancelled'), ], required=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    invoice_id = fields.Many2one("account.move", string='Invoice', readonly=True, copy=False)
    invoice_count = fields.Integer(string='Invoice Count', readonly=True)

    # Service number creation
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'cab_booking.cab_booking') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('cab_booking.cab_booking') or _('New')

        result = super(CabBooking, self).create(vals)
        return result

    # data checking
    # checking availability of car and driver on chosen date
    @api.constrains('date_end', 'date_start', 'driver', 'car')
    def date_to_error_message(self):
        if self.date_end <= self.date_start:
            raise ValidationError(_("End Date must be greater then Start Date"))
        if self.date_start < fields.Datetime.now():
            raise ValidationError(_("Start Date must be greater then Current Date"))
        driver_count = self.env['cab_booking.cab_booking'].search_count(
            [('state', 'in', ('draft', 'assigned', 'running')), ('driver', '=', self.driver.id),
             '|', '&', ('date_start', '<=', self.date_start), ('date_end', '>=', self.date_start),
             '|', '&', ('date_start', '<=', self.date_end), ('date_end', '>=', self.date_end),
             '|', '&', ('date_start', '=', self.date_start), ('date_end', '=', self.date_end),
             '&', ('date_start', '>', self.date_start), ('date_end', '<', self.date_end)
             ])

        if driver_count > 1:
            raise ValidationError(_("Driver is busy with another ride"))

        car_count = self.env['cab_booking.cab_booking'].search_count(
            [('state', 'in', ('draft', 'assigned', 'running')), ('car', '=', self.car.id),
             '|', '&', ('date_start', '<=', self.date_start), ('date_end', '>=', self.date_start),
             '|', '&', ('date_start', '<=', self.date_end), ('date_end', '>=', self.date_end),
             '|', '&', ('date_start', '=', self.date_start), ('date_end', '=', self.date_end),
             '&', ('date_start', '>', self.date_start), ('date_end', '<', self.date_end)
             ])

        if car_count > 1:
            raise ValidationError(_('Cab is not available, Pls choose another'))

    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You can only delete cab booking orders in state draft and cancel.'))
        return super(CabBooking, self).unlink()

    # State changes
    def button_assigned(self):
        for rec in self:
            rec.write({'state': 'assigned'})

    def button_running(self):
        for rec in self:
            rec.write({'state': 'running'})

    def button_done(self):
        for rec in self:
            rec.write({'state': 'done'})

    def button_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for cab booking.
        """
        self.ensure_one()
        company_id = self.company_id.id
        # ensure a correct context for the _get_default_journal method and company-dependent fields
        self = self.with_context(default_company_id=self.company_id.id, force_company=self.company_id.id)
        journal = self.env['account.move'].with_context(default_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))

        invoice_vals = {
            # 'ref': self.client_order_ref or '',
            'type': 'out_invoice',
            'narration': self.description,
            'currency_id': self.company_id.currency_id.id,
            # 'campaign_id': self.campaign_id.id,
            # 'medium_id': self.medium_id.id,
            # 'source_id': self.source_id.id,
            'invoice_user_id': self.driver and self.driver.id,
            # 'team_id': self.team_id.id,
            'partner_id': self.customer.id,
            # 'partner_shipping_id': self.customer.id,
            'invoice_partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'fiscal_position_id': self.customer.property_account_position_id.id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            # 'invoice_payment_term_id': self.payment_term_id.id,
            # 'invoice_payment_ref': self.reference,
            # 'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals

    def _get_invoice_line_name_from_product(self):
        """ Returns the automatic name to give to the invoice line depending on
        the product it is linked to.
        """
        self.ensure_one()
        if not self.car.product_id:
            return ''

        rslt = self.car.product_id.partner_ref
        if self.car.product_id.description_sale:
            rslt += '\n' + self.car.product_id.description_sale

        return rslt

    def _prepare_invoice_line(self, qty):
        """
        Prepare the dict of values to create the new invoice line for cab booking.

        """
        self.ensure_one()
        res = {}
        product = self.car.product_id.with_context(force_company=self.company_id.id)
        account = product.property_account_income_id or product.categ_id.property_account_income_categ_id

        # if not account and self.car.product_id:
        #     raise UserError(
        #         _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
        #         (self.car.product_id.name, self.car.product_id.id, self.car.product_id.categ_id.name))

        res = {
            'name': self._get_invoice_line_name_from_product(),
            # 'account_id': account.id,
            'price_unit': self.car.hr_rent or self.car.product_id.lst_price,
            'quantity': qty,
            'product_uom_id': self.car.product_id.uom_id.id,
            'product_id': self.car.product_id.id or False,
            'tax_ids': [(6, 0, self.car.product_id.taxes_id.ids)],
            # 'move_id': invoice_id
        }
        return res

    # To create invoice for the cab booking
    def button_invoiced(self):
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']
        if not self.car.product_id:
            raise UserError(_('Please choose product for this car'))
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for rec in self:

            invoice_vals = self._prepare_invoice()


            difference = rec.date_end - rec.date_start
            hour1 = difference.days * 24

            hour2 = difference.seconds / 3600
            total_hour = hour1 + hour2

            qty = total_hour
            invoice_vals['invoice_line_ids'].append((0, 0, self._prepare_invoice_line(qty)))
            invoice = self.env['account.move'].sudo().with_context(default_type='out_invoice').create(invoice_vals)

            # self.env['account.move.line'].create(self._prepare_invoice_line(qty, invoice.id))

            rec.write({'state': 'invoiced',
                       'invoice_id': invoice.id,
                       'invoice_count': rec.invoice_count + 1})

    # Function for view invoice
    def action_view_invoice(self):
        invoice = self.mapped('invoice_id')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoice) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoice.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def button_cancel(self):
        for rec in self:
            rec.write({'state': 'cancel'})
