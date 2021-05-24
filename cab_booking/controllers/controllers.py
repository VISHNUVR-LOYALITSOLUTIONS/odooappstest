# -*- coding: utf-8 -*-
# from odoo import http


# class CabBooking(http.Controller):
#     @http.route('/cab_booking/cab_booking/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cab_booking/cab_booking/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cab_booking.listing', {
#             'root': '/cab_booking/cab_booking',
#             'objects': http.request.env['cab_booking.cab_booking'].search([]),
#         })

#     @http.route('/cab_booking/cab_booking/objects/<model("cab_booking.cab_booking"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cab_booking.object', {
#             'object': obj
#         })
