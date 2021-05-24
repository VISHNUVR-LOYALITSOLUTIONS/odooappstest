# -*- coding: utf-8 -*-
{
    'name': "Cab Booking Management System",

    'summary': """
        You can book cabs from list of cabs based on your time and location. """,

    'description': """
        You can book cabs from list of cabs based on your time and location. You can choose driver from list of drivers.
        CBMS allows you to create invoice for the trip based on the travel time.
        Settings :- Please choose a product and give hourly billing rate in Fleet -> Vehicles for invoice calculation.
    """,

    'author': "Loyal IT Solutions Pvt Ltd",
    'website': "http://www.loyalitsolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'fleet', 'mail', 'sale', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/cabbooking.xml',
        'views/vehicle_charge.xml',
        'security/cabbook_security.xml',
        'data/ir_sequence_data.xml',
        'report/report_cab_booking.xml',
        'wizard/cab_booking_report_wizard_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
