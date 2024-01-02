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
from odoo import models, api, fields, _
from . api import API
from odoo.exceptions import Warning
from ..unit.backend_adapter import WpImportExport


from . api import API
import logging

# import xmlrpclib
from collections import defaultdict
# from odoo.addons.queue_job.job import job
import base64
from odoo import models, fields, api, _
from ..unit.sale_order_exporter import WpSaleOrderExport
from ..unit.sale_order_importer import WpSaleOrderImport
from odoo.exceptions import Warning
from ..unit.customer_importer import WpCustomerImport

_logger = logging.getLogger(__name__)


class SalesOrder(models.Model):

    """ Models for woocommerce sales order """
    _inherit = 'sale.order'

    # fields for putting Wordpress payment info  by pravin    
    wp_payment_method = fields.Char(string = "Payment Method")
    wp_payment_status = fields.Char(string = "Payment Status")
    wp_payment_transaction_id = fields.Char(string = "Payment Transaction_Id")
    wp_payment_date_paid = fields.Char(string = "Payment Date Paid")
    wp_sale_order_number = fields.Char(string = "Sale Order Number")


    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                  string='backend',
                                  store=True,
                                  readonly=False,
                                  required=False,
                                  )
    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.sale.order',
                                      string='Sale order mapping',
                                      inverse_name='order_id',
                                      readonly=False,
                                      required=False,
                                      )


    @api.model
    def create(self, vals):
        """ Override create method to export"""
        _logger.info("create vals %s", vals)
        if 'partner_id' in vals.keys():
            vals['partner_id'] = int(vals['partner_id'])
        sales_order_id = super(SalesOrder, self).create(vals)
        return sales_order_id

    # @api.multi
    def write(self, vals):
        """ Override write method to export when any details is changed """
        _logger.info("write vals %s", vals)
        for sale_order in self:
            res = super(SalesOrder, sale_order).write(vals)
        return True

    # @api.multi
    def sync_sale_order(self):
        for backend in self.backend_id:
            self.export(backend)
        return

    # @api.multi
    def sales_line(self, vals):
        res = self.write({'order_line': [[0, 0, vals]]})
        return True

    # @api.multi
    # @job
    def importer(self, backend, date=None):
        """ import and create or update backend mapper """
        if len(self.ids) > 1:
            for obj in self:
                obj.single_importer(backend)
            return

        method = 'sales_order_import'
        arguments = [None, self]
        importer = WpSaleOrderImport(backend)

        # count = 1
        count = backend.start_record_num
        end = backend.end_record_num

        if not (count and end):
            raise Warning(_("Enter Valid Start And End  Record Number"))

        data = True
        sale_ids = []
        while data:
            
            res = importer.import_sales_order(method, arguments, count, date)['data']

            if res and count <= end:
                for single_res in res:
                    # if single_res['status'] == "completed":
                        print ("here  single_res")
                        sale_ids.append(single_res)
                        print (sale_ids)

            else:
                data = False
            count += 1

        for sale_id in sale_ids:
            self.single_importer(backend, sale_id)

    # @api.multi
    # @job
    def single_importer(self, backend, sale_id, woo_id=None):
        method = 'sales_order_import'
        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('woo_id', '=', sale_id['id'])], limit=1)
        arguments = [sale_id or None, mapper.order_id or self]

        importer = WpSaleOrderImport(backend)
        res = importer.import_sales_order(method, arguments)

        customer_obj = self.env['res.partner']

        if sale_id['customer_id'] == 0:
            trial = customer_obj.env['res.partner'].search([('first_name', '=', sale_id["billing"]["first_name"])])
            partner_id = self.env['wordpress.odoo.res.partner'].search(
                [('backend_id', '=', backend.id), ('woo_email', '=', sale_id['billing']['email'])], limit=1)
        else:
            partner_id = self.env['wordpress.odoo.res.partner'].search(
                [('backend_id', '=', backend.id), ('woo_id', '=', res['data']['customer_id'])])

        # if sale_id["shipping"]["address_1"] == "" and sale_id["shipping"]["address_2"] == "":
        #     _logger.info("Please provoide at last Address line 1 or Address line2 to shipping address of the order %s",
        #                  sale_id["id"])
        #     return True



        # if sale_id["billing"]["postcode"] == "" and sale_id["shipping"]["postcode"] == "":
        #
        #     raise UserError("Please provide zip code in order address  %s",sale_id["id"])
        #


        # if sale_id["billing"]["address_1"] == "" and sale_id["billing"]["address_2"] == "":
        #     _logger.info("Please provoide at last Address line 1 or Address line2 to shipping address of the order %s",
        #                  sale_id["id"])
        #     return True

        if not partner_id:
            customer_id = {
                "id": sale_id["customer_id"],
                "email": sale_id["billing"]["email"],
                "first_name": sale_id["billing"]["first_name"],
                "last_name": sale_id["billing"]["last_name"],
                "role": "guest_customer",
                "username": sale_id["billing"]["first_name"] + "(" + "Guest" + ")",
                'billing': {
                    "first_name": sale_id["billing"]["first_name"]
                    ,
                    "last_name": sale_id["billing"]["last_name"] + "(" + "Guest" + ")",
                    "company": sale_id["billing"]["company"],
                    "address_1": sale_id["shipping"]["address_1"],
                    "address_2": sale_id["shipping"]["address_2"],
                    "city": sale_id["billing"]["city"],
                    "postcode": sale_id["billing"]["postcode"],
                    "country": sale_id["billing"]["country"],
                    "state": sale_id["billing"]["state"],
                    "email": sale_id["billing"]["email"],
                    "phone": sale_id["billing"]["phone"]
                },
                'shipping': {'first_name': sale_id["billing"]["first_name"],
                             'last_name': sale_id["billing"]["last_name"] + "(" + "Guest" + ")",
                             'company': sale_id["billing"]["company"],
                             'address_1': sale_id["shipping"]["address_1"],
                             'address_2': sale_id["shipping"]["address_2"],
                             'city': sale_id["billing"]["city"], 'postcode': sale_id["billing"]["postcode"],
                             'country': sale_id["billing"]["country"],
                             'state': sale_id["billing"]["state"]
                             }
            }
            customer_obj = self.env['res.partner']
            create_customer = customer_obj.single_importer(backend, customer_id)


        #we are searching for partner after creating guest customer
        guest_customer = False
        if sale_id['customer_id'] == 0:
            print(sale_id)
            print(sale_id["billing"]["email"])

            for k in customer_obj.env['wordpress.odoo.res.partner'].search(
                    [('woo_email', "=", sale_id["billing"]["email"])]).customer_id:
                guest_customer = k

            # trial2 = customer_obj.env['res.partner'].search([('first_name', '=', sale_id["billing"]["first_name"])])[1]
            partner_id = self.env['wordpress.odoo.res.partner'].search(
                [('backend_id', '=', backend.id), ('woo_id', '=', sale_id['billing']['email'])])

        else:
            partner_id = self.env['wordpress.odoo.res.partner'].search(
                [('backend_id', '=', backend.id), ('woo_id', '=', res['data']['customer_id'])])



        record = res['data']      


        # #search and create tax if not available in odoo      
        if record['tax_lines']:
            for line in record['tax_lines']:
                tax_id = self.env['account.tax'].search([('name','=',line['label'])])

                if not tax_id:
                    version = "wc/v2"
                    wcapi = API(url=backend.location, consumer_key=backend.consumer_key,
                        consumer_secret=backend.consumer_secret, version=version, wp_api=True)
                    tax = wcapi.get("taxes/{0}".format(line['rate_id'])).json()

                    state_code = self.env['res.country.state'].search([('code','=',tax['state']),('country_id','=',tax['country'])])              


                    vals = {
                        # 'name':tax['name'],
                        'name':line['label'],
                        'amount':tax['rate'],
                        'backend_id':backend.id,
                        'state_id':state_code.id,
                        'count_id':state_code.country_id.id,
                        'postcode':tax['postcode'],
                        'city':tax['city'],
                        'priority':tax['priority'],
                        'compound':tax['compound'],
                        'shipping':tax['shipping'],
                        'order':tax['order'],               
                    }
                    tax_create_id = self.env['account.tax'].create(vals)

                    # tax is added in wordpress_odoo_tax
                    self.env['wordpress.odoo.tax'].create(
                        {'woo_id': tax['id'],
                        'backend_id': backend.id,
                        'tax_id': tax_create_id.id
                        })

        delivery = False
        # if len(sale_id['shipping_lines']) != 0:
        #     delivery = self.env['delivery.carrier'].search(
        #         [('name', '=', sale_id['shipping_lines'][0]['method_title'])])

        if delivery != False:
            # if
            prod_for_delivery = self.env['product.product'].create({
                'name': record['shipping_lines'][0]['method_title'],
                'taxes_id': False
            })
            # record['shipping_lines'][0]
            # delivery = self.env['delivery.carrier'].search([('name', '=', record['shipping_lines'][0]['method_title'])])
            # if delivery.id == False:
            delivery = self.env['delivery.carrier'].create({
                'name': record['shipping_lines'][0]['method_title'],
                'product_id': prod_for_delivery.id,
                'delivery_type': 'fixed'
            })


        #new code added on jun27 2023
        delivery = False
        # if len(sale_id['shipping_lines']) != 0:
        #     delivery = self.env['delivery.carrier'].search(
        #         [('name', '=', sale_id['shipping_lines'][0]['method_id'])])

        if delivery != False:
            # if
            prod_for_delivery = self.env['product.product'].create({
                'name': record['shipping_lines'][0]['method_id'],
                'taxes_id': False
            })
            # record['shipping_lines'][0]
            # delivery = self.env['delivery.carrier'].search([('name', '=', record['shipping_lines'][0]['method_title'])])
            # if delivery.id == False:
            delivery = self.env['delivery.carrier'].create({
                'name': record['shipping_lines'][0]['method_id'],
                'product_id': prod_for_delivery.id,
                'delivery_type': 'fixed'
            })

        if delivery != False:

            delivery.product_id.taxes_id = None
            fixed_price = 0.0

            if len(sale_id['shipping_lines']) != 0:
                if float(sale_id['shipping_lines'][0]['total_tax']) != 0.0:
                    fixed_price = float(sale_id['shipping_lines'][0]['total']) + float(
                        sale_id['shipping_lines'][0]['total_tax'])
                else:
                    fixed_price = float(sale_id['shipping_lines'][0]['total'])
                if sale_id['shipping_lines']:
                    delivery.update({
                        'fixed_price': fixed_price,
                    })

        #################



        #### code addeded on jun27 2023
        wcapi = WpCustomerImport(backend)
        customer = False
        if partner_id.id is False:
            customer = guest_customer
        else:
            customer = partner_id.customer_id



        delivery_address_mapping = False
        delivery_address_mapping = partner_id.env['res.partner'].search(
            [('type', '=', 'delivery'), ('parent_id', '=', customer.id),
             ('zip', '=', sale_id["shipping"]['postcode'])])

        if delivery_address_mapping.id is False:
            delivery_address_mapping = WpCustomerImport.add_shipping(self, sale_id, customer, backend)

        invoice_address_mapping = False
        invoice_address_mapping = partner_id.env['res.partner'].search(
            [('type', '=', 'invoice'), ('parent_id', '=', customer.id),
             ('zip', '=', sale_id["billing"]['postcode'])])

        if invoice_address_mapping.id is False:
            invoice_address_mapping = wcapi.add_billing(sale_id, customer, backend)


        #############
                    

        
        if partner_id or guest_customer:
            pass
        else:
            partner = self.env['res.partner']
            if res['data']['customer_id'] != 0:
                partner.single_importer(backend, res['data']['customer_id'], False)

                partner_id = self.env['wordpress.odoo.res.partner'].search(
                    [('backend_id', '=', backend.id), ('woo_id', '=', res['data']['customer_id'])])
            else:
                partner_id = self.env['wordpress.odoo.res.partner'].search(
                    [('backend_id', '=', backend.id), ('woo_email', '=', sale_id["billing"]["email"])])
            # partner = self.env['res.partner']
            # partner.single_importer(backend, res['data']['customer_id'],False)
            # partner_id = self.env['wordpress.odoo.res.partner'].search(
            #     [('backend_id', '=', backend.id), ('woo_id', '=', res['data']['customer_id'])])

        
        if mapper:
            # importer.write_sale_order(record, mapper, backend)
            # sale_order_id = mapper.order_id
            #code added on 27 jun 2023
            sale_order_id = mapper.order_id
            # sale_order_id.partner_invoice_id = invoice_address_mapping.id
            # sale_order_id.partner_shipping_id = delivery_address_mapping.id

            # adding wp payment info in sale_order write method
            sale_order_id.wp_payment_method = res['data']['payment_method_title']          
            sale_order_id.wp_payment_transaction_id = res['data']['transaction_id']
            sale_order_id.wp_payment_date_paid = res['data']['date_paid']
            sale_order_id.wp_sale_order_number = res['data']['number']
            sale_order_id.backend_id = backend.id

            if sale_order_id.wp_payment_date_paid:
                sale_order_id.wp_payment_status = "Paid"


            if 'line_items' in record:
                product_ids = []
                for lines in record['line_items']:
                    if 'product_id' in lines:
                        product_template_id = self.env['wordpress.odoo.product.template'].search(
                            [('backend_id', '=', backend.id),
                             ('woo_id', '=', lines['product_id'])])
                        if product_template_id:
                            pass
                        else:
                            product = self.env['product.template']
                            product.single_importer(backend, lines['product_id'],False)
                            product_template_id = self.env['wordpress.odoo.product.template'].search(
                                [('backend_id', '=', backend.id), ('woo_id', '=', lines['product_id'])])

                        product=product_template_id.product_id.product_variant_id

                        # addding tax in sale_order_line in write
                        tax_ids = []
                        if lines['taxes']:                                
                            for tax in lines['taxes']:
                                if tax['id'] and (tax['subtotal'] or tax['total']):
                                    for tax_line in res['data']['tax_lines']:
                                        if tax['id'] == tax_line['rate_id']:
                                            if tax_line['label']:
                                                tax_id = self.env['account.tax'].search([('name','=',tax_line['label'])])
                                                tax_ids.append(tax_id.id)


                        for prod in product:
                            if lines['subtotal_tax']:
                                original_unit_price = (float(lines['subtotal_tax']) + float(
                                    lines['subtotal'])) / float(lines['quantity'])
                            else:
                                original_unit_price = float(lines['subtotal']) / float(lines['quantity'])
                            if 'variation_id' in lines:
                                    for meta_lines in lines['meta_data']:
                                        if meta_lines['key'] == 'pa_color' or meta_lines['key'] == 'color' or meta_lines['key'] == 'pa_colorr':
                                            if meta_lines['value'][0:1:1].islower():
                                                color = meta_lines['value'][0:1:1].upper() + meta_lines['value'][1::1]
                                            else:
                                                color = meta_lines['value']
                                            multi_prod = self.env['product.product'].search([('name', '=', product.name)])
                                            for single_prod in multi_prod:
                                                if single_prod.product_template_attribute_value_ids[0].name == color:
                                                    prod = single_prod
                            result = {'product_id': prod.id,
                                      'price_unit': original_unit_price,
                                      'product_uom_qty': lines['quantity'],
                                      'product_uom': 1,
                                      'price_subtotal': lines['subtotal'],
                                      'name': lines['name'],
                                      'order_id': sale_order_id.id,
                                      'backend': lines['id'],
                                      'tax_id':[(6,0,tax_ids)],
                                      }
                            product_ids.append(result)
                
                for details in product_ids:
                    order = self.env['sale.order.line'].search(
                        [('backend', '=', details['backend'])])
                    if order:
                        order.write(details)
                

        else:
            # importer.create_sale_order(record, partner_id, backend)
                values = {}
                product_ids = []
                if record['date_created']:
                    date_created = record['date_created']
                else:
                    date_created = ''
                customer=0
                #code added on jun27 2023
                if partner_id.id:
                    values['partner_id'] = partner_id[0].customer_id.id
                    values['date_order'] = date_created.replace('T', ' ')
                if guest_customer:
                    values['partner_id'] = guest_customer.id
                    values['date_order'] = date_created.replace('T', ' ')

                sale_order = self.create(values)
                # sale_order.partner_invoice_id = invoice_address_mapping.id
                # sale_order.partner_shipping_id = delivery_address_mapping.id

                # adding wp payment info in sale_order create method
                sale_order.wp_payment_method = res['data']['payment_method_title']          
                sale_order.wp_payment_transaction_id = res['data']['transaction_id']
                sale_order.wp_payment_date_paid = res['data']['date_paid']
                sale_order.wp_sale_order_number = res['data']['number']
                sale_order.backend_id = backend.id
                
                if sale_order.wp_payment_date_paid:
                    sale_order.wp_payment_status = "Paid"


                if 'line_items' in record:
                    product_ids = []
                    for lines in record['line_items']:
                        if 'product_id' in lines:
                            product_template_id = self.env['wordpress.odoo.product.template'].search(
                                [('backend_id', '=', backend.id),
                                 ('woo_id', '=', lines['product_id'])])

                            if product_template_id:
                                pass
                            else:
                                product = self.env['product.template']
                                product.single_importer(backend, lines['product_id'],False)
                                product_template_id = self.env['wordpress.odoo.product.template'].search(
                                    [('backend_id', '=', backend.id), ('woo_id', '=', lines['product_id'])])

                            product=product_template_id.product_id.product_variant_id

                            # addding tax in sale_order_line in create
                            tax_ids = []
                            if lines['taxes']:                                
                                for tax in lines['taxes']:
                                    if tax['id'] and (tax['subtotal'] or tax['total']):
                                        for tax_line in res['data']['tax_lines']:
                                            if tax['id'] == tax_line['rate_id']:
                                                if tax_line['label']:
                                                    tax_id = self.env['account.tax'].search([('name','=',tax_line['label'])])
                                                    tax_ids.append(tax_id.id)
                                                   

                            for prod in product:
                                if lines['subtotal_tax']:
                                    original_unit_price = (float(lines['subtotal_tax']) + float(
                                        lines['subtotal'])) / float(lines['quantity'])
                                else:
                                    original_unit_price = float(lines['subtotal']) / float(lines['quantity'])
                                if 'variation_id' in lines:
                                    for meta_lines in lines['meta_data']:
                                        if meta_lines['key'] == 'pa_color' or meta_lines['key'] == 'color' or meta_lines['key'] == 'pa_colorr':
                                            if meta_lines['value'][0:1:1].islower():
                                                color = meta_lines['value'][0:1:1].upper() + meta_lines['value'][1::1]
                                            else:
                                                color = meta_lines['value']
                                            multi_prod = self.env['product.product'].search([('name', '=', product.name)])
                                            for single_prod in multi_prod:
                                                if single_prod.product_template_attribute_value_ids[0].name == color:
                                                    prod = single_prod
                                result = [0,0,{
                                    'product_id': prod.id,
                                    'price_unit': original_unit_price,
                                    'product_uom_qty': lines['quantity'],
                                    'product_uom': 1,
                                    'price_subtotal': lines['subtotal'],
                                    'name': lines['name'],
                                    'order_id': sale_order.id,
                                    'backend': lines['id'],                                    
                                    'tax_id':[(6,0,tax_ids)],
                                }]
                                
                                product_ids.append(result)
                   
                    sale_order.update({'order_line': product_ids})



                if delivery is not False and len(sale_id['shipping_lines']) != 0:
                    sale_order.carrier_id= delivery.id
                    sale_order.get_delivery_price()
                    sale_order.set_delivery_line()
                    # add_delivery = sale_order.env['choose.delivery.carrier'].create({
                    #     'carrier_id': delivery.id,
                    #     'order_id': sale_order.id,
                    #     'partner_id': partner_id.id,
                    #     'delivery_price': delivery.fixed_price
                    # })
                    # add_delivery.button_confirm()
                
        if mapper and (res['status'] == 200 or res['status'] == 201):
            vals = {
                'woo_id': res['data']['id'],
                'backend_id': backend.id,
                'order_id': mapper.order_id.id,
            }
            self.backend_mapping.write(vals)
        else:
            if(partner_id):
                vals = {
                    'woo_id': res['data']['id'],
                    'backend_id': backend.id,
                    'order_id': sale_order.id,
                }

                self.backend_mapping.create(vals)

    # @api.multi
    # @job
    def export(self, backend):
        """ export and create or update backend mapper """
        
        if len(self.ids) > 1:
            for obj in self:
                obj.export(backend)
            return
        mapper = self.backend_mapping.search([('backend_id', '=', backend.id), ('order_id', '=', self.id)], limit=1)
        method = 'sales_order'
        arguments = [mapper.woo_id or None, self]
        export = WpSaleOrderExport(backend)
        res = export.export_sales_order(method, arguments)
        if mapper and (res['status'] == 200 or res['status'] == 201):
            mapper.write(
                {'order_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})
        elif (res['status'] == 200 or res['status'] == 201):
            self.backend_mapping.create(
                {'order_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})

        # assign order_line_id of wp in odoo order_line of field name "backend"(means:wp_order_line_id)
        for index, value in enumerate(res['data']['line_items']):
            self.order_line[index].backend = value['id']

    # @api.multi
    def _prepare_invoice(self):
        invoice_id = super(SalesOrder, self)._prepare_invoice()
        invoice_id['backend_id'] = self.backend_id.id
        invoice_id['sale_order_id'] = self.id
        return invoice_id

class SalesOrderLine(models.Model):

    """ Models for woocommerce sales order line"""
    _inherit = 'sale.order.line'
    backend=fields.Integer("woo line id")


class SalesOrderMapping(models.Model):

    """ Model to store woocommerce id for particular Sale Order"""
    _name = 'wordpress.odoo.sale.order'
    _description ='wordpress.odoo.sale.order'
    _rec_name = 'order_id'

    order_id = fields.Many2one(comodel_name='sale.order',
                               string='Sale Order',
                               ondelete='cascade',
                               readonly=False,
                               required=True,
                               )

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                 string='Website',
                                 ondelete='set null',
                                 store=True,
                                 readonly=False,
                                 required=False,
                                 )
    woo_id = fields.Char(string='woo_id')


def import_record(cr, uid, ids, context=None):
    """ Import a record from woocommerce """
    importer.run(woo_id)
