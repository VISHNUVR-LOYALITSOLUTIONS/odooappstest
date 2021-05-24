# -*- coding: utf-8 -*-

from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class ReportPayment(models.AbstractModel):
    _name = 'report.cab_booking.report_cab_booking_template'

    def lines(self, car_id, driver_id, data):

        if car_id and driver_id:
            query = """select fv.name as cab,rp.name as driver,cb.state,
                cb.date_start as starting_date, cb.date_end as ending_date,
                am.amount_total as invoice_amount
                from cab_booking_cab_booking as cb
                left join fleet_vehicle as fv
                on cb.car=fv.id
                left join res_users as ru
                on cb.driver = ru.id
                left join res_partner as rp
                on ru.partner_id = rp.id
                left join account_move as am
                on cb.invoice_id = am.id where cb.car = %s and cb.driver = %s 
                and cb.date_end::date between date %s and date %s and cb.company_id = %s"""

            self._cr.execute(query, (car_id[0], driver_id[0], data['form']['date_from'], data['form']['date_to'], data['form']['company_id'][0]))
        elif car_id and driver_id == False:
            query = """select fv.name as cab,rp.name as driver,cb.state,
                cb.date_start as starting_date, cb.date_end as ending_date,
                am.amount_total as invoice_amount
                from cab_booking_cab_booking as cb
                left join fleet_vehicle as fv
                on cb.car=fv.id
                left join res_users as ru
                on cb.driver = ru.id
                left join res_partner as rp
                on ru.partner_id = rp.id
                left join account_move as am
                on cb.invoice_id = am.id where cb.car = %s 
                and cb.date_end::date between date %s and date %s and cb.company_id = %s"""

            self._cr.execute(query, (car_id[0],  data['form']['date_from'], data['form']['date_to'], data['form']['company_id'][0]))
        elif car_id == False and driver_id:
            query = """select fv.name as cab,rp.name as driver,cb.state,
                cb.date_start as starting_date, cb.date_end as ending_date,
                am.amount_total as invoice_amount
                from cab_booking_cab_booking as cb
                left join fleet_vehicle as fv
                on cb.car=fv.id
                left join res_users as ru
                on cb.driver = ru.id
                left join res_partner as rp
                on ru.partner_id = rp.id
                left join account_move as am
                on cb.invoice_id = am.id where cb.driver = %s and
                cb.date_end::date between date %s and date %s and cb.company_id = %s"""
            self._cr.execute(query, (driver_id[0],  data['form']['date_from'], data['form']['date_to'], data['form']['company_id'][0]))
        else:
            query = """select fv.name as cab,rp.name as driver,cb.state,
                cb.date_start as starting_date, cb.date_end as ending_date,
                am.amount_total as invoice_amount
                from cab_booking_cab_booking as cb
                left join fleet_vehicle as fv
                on cb.car=fv.id
                left join res_users as ru
                on cb.driver = ru.id
                left join res_partner as rp
                on ru.partner_id = rp.id
                left join account_move as am
                on cb.invoice_id = am.id where 
                cb.date_end::date between date %s and date %s and cb.company_id = %s"""
            self._cr.execute(query, (data['form']['date_from'], data['form']['date_to'], data['form']['company_id'][0]))

        record = self._cr.dictfetchall()
        return record


    @api.model
    def _get_report_values(self, docids, data=None):
        car_id = data['form']['car_id']
        driver_id = data['form']['driver_id']
        res = {}
        res = self.with_context(data['form'].get('used_context', {})).lines(car_id, driver_id, data)
        docargs = {
            'doc_model': self.env['cab_booking.cab_booking'],
            'data': data,
            'driver': driver_id[1] if driver_id else False,
            'cab': car_id[1] if car_id else False,
            'lines': res,
        }
        return docargs
