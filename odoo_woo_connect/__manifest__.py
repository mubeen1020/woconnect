# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2016-Present Techspawn Solutions Pvt. Ltd.
# (<https://techspawn.com/>)
#
##########################################################################

{
    'name': 'Odoo Woocommerce Connect',
    'version': '12.0',
    'category': 'Sale',
    'sequence': 1,
    'price': 100.00,
    'license': 'OPL-1',
    'currency': 'USD',
    'author': 'Techspawn Solutions Pvt Ltd',
    'website': 'http://www.techspawn.com',
    'summary': """Woocommerce odoo connector woocommerce integration odoo Woocommerce connector is used to Import customers,products,saleorder from woocommerce to Odoo Manage your WooCommerce in Real Time and Bi-directional data exchange between WooCommerce store and Odoo""",
    'description': """

Odoo Woocommerce Connect
=========================

This Module will Connect Odoo with Wordpress WooCommerce and synchronise Data.
------------------------------------------------------------------------------


Some of the feature of the module:
--------------------------------------------

  1. Synchronise all the products.

  2. Synchronise all the products attributes.

  3. Synchronise all the categories.

  4. Synchronise all the customers.

  5. Synchronise all the sales orders.

  6. Synchronise all the taxes.



This module works very well with latest version of Wordpress v4.4 or later and WooCommerce v2.6.x or later
----------------------------------------------------------------------------------------------------------
    """,
    'demo_xml': [],
    'update_xml': [],
    'depends': ['base',
                'product',
                'website',
                'stock',
                'sale',
                'sale_management',
                'board',
                ],
    'data': [
              'security/bridge_security.xml',
              'security/ir.model.access.csv',
              'views/wp_bridge_view.xml',
              'views/product.xml',
              'views/customer.xml',
              'views/custom_field.xml',
              'views/sale_order.xml',
              'views/tax.xml',
              'views/product_mapping.xml',
              'views/product_tag_mapping.xml',
              'views/product_attribute_mapping.xml',
              'views/product_category_mapping.xml',
              'views/tax_mapping.xml',
              'views/customer_mapping.xml',
              'views/sale_order_mapping.xml',
              'views/jobs.xml',
              'views/cron.xml',
              'views/invoice_refund_view.xml',
              'views/sales_analysis.xml',
              'views/dashboard.xml',
              'views/message_wizard.xml'
             ],
    'images': ['static/description/ODOO_WooCommerce_New_Version_12.gif'],
    'js': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
