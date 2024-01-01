# -*- coding: utf-8 -*-
#
#
#    Techspawn Solutions Pvt. Ltd.
#    Copyright (C) 2016-TODAY Techspawn(<http://www.Techspawn.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import requests
import logging
from ..model.api import API
from datetime import datetime
from datetime import timedelta
# from . backend_adapter import WpImportExport
from ..unit.backend_adapter import WpImportExport

_logger = logging.getLogger(__name__)


class WpSaleOrderExport(WpImportExport):

    def get_api_method(self, method, args):
        """ get api for sale order and values"""
        
        api_method = None
        if method == 'sales_order':
            if not args[0]:
                api_method = 'orders'
            else:
                api_method = 'orders/' + str(args[0])
        elif method == 'account_invoice':
            if not args[0]:
                api_method = 'orders/' + \
                    str(args[2].woo_id) + '/refunds'
            else:
                api_method = 'orders/' + \
                    str(args[2].woo_id) + '/refunds/' + str(args[0])
        return api_method

    def get_order_lines(self, order_lines):
        """ get all order lines """
        
        lines = []
        if order_lines:
            for order_line in order_lines:
                product_id = order_line.product_id.product_tmpl_id.backend_mapping.search(
                    [('backend_id', '=', self.backend.id), ('product_id', '=', order_line.product_id.product_tmpl_id.id)])
                variation_id = order_line.product_id.backend_mapping.search(
                    [('backend_id', '=', self.backend.id), ('product_id', '=', order_line.product_id.id)])
                if product_id:
                    lines.append({"product_id": int(product_id.woo_id) or '',
                                #   "variation_id": int(variation_id.woo_id) or None,
                                  "quantity": int(order_line.product_uom_qty) or '',
                                  "price": str(order_line.price_unit),
                                  "total": str(order_line.price_subtotal) or '',
                                # "subtotal_tax": 'order_line.price_tax' or '',
                                # "taxes":    tax_id,
                                # 'id':order_line.backend                                                                                        

                                  })
                    if order_line.backend:
                        lines[-1]['id']=order_line.backend
        return lines

    def export_sales_order(self, method, arguments):
        """ Export sale order data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        print(arguments[1].name)
        status = ''
        if arguments[1].state == 'done':
            status = 'completed'
        elif arguments[1].state == 'draft':
            status = 'processing'
        elif arguments[1].state == 'sale':
            status = 'on-hold'
        elif arguments[1].state == 'cancel':
            status = 'cancelled'

        customer_woo_id = arguments[1].partner_id.backend_mapping.search([('backend_id', '=', self.backend.id), ('customer_id', '=', arguments[1].partner_id.id)], limit=1)
        
        
        result_dict = {
            "status": status,
            "customer_id":int(customer_woo_id.woo_id) if customer_woo_id else 0,


            "billing": {"first_name": arguments[1].partner_id.name or '',
                        "last_name": arguments[1].partner_id.last_name or '',
                        "company": arguments[1].partner_id.company or '',
                        "address_1": arguments[1].partner_id.street or '',
                        "address_2": arguments[1].partner_id.street2 or '',
                        "city": arguments[1].partner_id.city or '',
                        "state": arguments[1].partner_id.state_id.code or '',
                        "postcode": arguments[1].partner_id.zip or '',
                        "country": arguments[1].partner_id.country_id.code or '',
                        "email": arguments[1].partner_id.email or '',
                        "phone": arguments[1].partner_id.phone or '',
                        },
            "shipping": {"first_name": arguments[1].partner_id.name or '',
                         "last_name": arguments[1].partner_id.last_name or '',
                         "address_1": arguments[1].partner_id.street or '',
                         "address_2": arguments[1].partner_id.street2 or '',
                         "city": arguments[1].partner_id.city or '',
                         "state": arguments[1].partner_id.state_id.code or '',
                         "postcode": arguments[1].partner_id.zip or '',
                         "country": arguments[1].partner_id.country_id.code or '',
                         "email": arguments[1].partner_id.email or '',
                         "phone": arguments[1].partner_id.phone or '',
                         },
            "line_items": self.get_order_lines(arguments[1].order_line),
            "tax_lines": [],
        }
            
        # print("result_dict",result_dict)

        r = self.export(method, result_dict, arguments)

        arguments[1].wp_payment_method = r.json()['payment_method_title']          
        arguments[1].wp_payment_transaction_id = r.json()['transaction_id']
        arguments[1].wp_payment_date_paid = r.json()['date_paid']
        arguments[1].wp_sale_order_number = r.json()['number']
        
        return {'status': r.status_code, 'data': r.json()}

    def export_invoice_refund(self, method, arguments):
        """ Export refund invoice data"""
        
        _logger.debug("Start calling Woocommerce api %s", method)

        line_items = []
        for line_item in arguments[1].invoice_line_ids:
            line_items.append({
                # "id": arguments[1].invoice_line_ids.id,
                "name": line_item.product_id.name or '',
                # "sku": "12345",
                # "product_id": line_item.product_id.id or '',
                "product_id":line_item.product_id.product_tmpl_id.backend_mapping.woo_id or '',
                # "variation_id": line_item.product_id.variation_id or 0,
                "quantity": line_item.quantity or '',
                # "tax_class": "",
                "price": line_item.price_unit or 0.0,
            })

        result_dict = {
            "order_refund": {
                "amount": str(arguments[1].amount_total),
                "reason": str(arguments[1].name.split(',')[-1])
                }
            
            }       
        
        
        r = self.export(method, result_dict, arguments)

        
        if r.status_code == 200 or r.status_code == 201:
            version = "wc/v3"
            wcapi = API(url=self.backend.location, consumer_key=self.backend.consumer_key,
            consumer_secret=self.backend.consumer_secret, version=version, wp_api=True)
            res = wcapi.get("orders/{0}/refunds".format(int(arguments[2].woo_id)))

            return {'status': res.status_code, 'data': res.json()}        


        return {'status': r.status_code, 'data': r.json()}
