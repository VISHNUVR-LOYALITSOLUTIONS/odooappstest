# -*- coding: utf-8 -*-
# from odoo import http


# class OwnProductSalesreport(http.Controller):
#     @http.route('/salary_statement_report/salary_statement_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/salary_statement_report/salary_statement_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('salary_statement_report.listing', {
#             'root': '/salary_statement_report/salary_statement_report',
#             'objects': http.request.env['salary_statement_report.salary_statement_report'].search([]),
#         })

#     @http.route('/salary_statement_report/salary_statement_report/objects/<model("salary_statement_report.salary_statement_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('salary_statement_report.object', {
#             'object': obj
#         })
