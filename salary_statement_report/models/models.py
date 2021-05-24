# -*- coding: utf-8 -*-

from odoo import models, fields, api

class salary_statementsales(models.TransientModel):
    _name = "salary.statement.report"
    _description = "Salary Statement Report"



    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    date_from = fields.Date(string='Start Date',required=True,default=fields.Date.today,)
    date_to = fields.Date(string='End Date',required=True,default=fields.Date.today,)
    target_move = fields.Boolean(default=False,string="Consultancy")


    def export_xls(self):

        # self.ensure_one()
        #
        # active_record = self._context['active_id']
        # record = self.env['sale.order'].browse(active_record)
        #
        # datas = {
        #     'ids': self.ids,
        #     'model': self._name,
        #     'record': record.id,
        # }
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'hr.payslip'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        return self.env.ref('salary_statement_report.salary_statement_xls').report_action(self, data=datas)
