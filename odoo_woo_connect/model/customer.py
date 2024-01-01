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

import logging

from collections import defaultdict
import base64
from odoo import models, fields, api, _
from ..unit.customer_exporter import WpCustomerExport
from ..unit.customer_importer import WpCustomerImport
from odoo.exceptions import Warning


_logger = logging.getLogger(__name__)


class Customer(models.Model):

    """ Models for woocommerce res partner """
    _inherit = 'res.partner'

    first_name = fields.Char(string='First Name')
    last_name = fields.Char(string='Last Name')
    username = fields.Char(string='WP User Name')
    company = fields.Char(string='WP Company Name')
    password = fields.Char(string='WP password')

    shipping_ids = fields.One2many(comodel_name='res.partner.shipping.address',
                                   inverse_name='partner_id',
                                   string='Multi Shipping',
                                   required=False,)
    default_address = fields.Boolean('Default Address')
    work_phone = fields.Char(string='Work Phone',help="Enter work phone no.")
    other_phone = fields.Char(string='Other Phone',help="Enter Other phone no.")
    tax_resale_number = fields.Char(string='Tax Resale Number',help="Enter Tax resale number.")
    parts_tax_cat_desc = fields.Char(string='Parts Tax Cat Desc',help="Enter Parts Tax Cat Desc.")
    supplier_code=fields.Char("Supplier code for import purpose")

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                  string='backend',
                                  store=True,
                                  readonly=False,
                                  required=False,
                                  )

    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.res.partner',
                                      string='Customer mapping',
                                      inverse_name='customer_id',
                                      readonly=False,
                                      required=False,
                                      )
    prefer_email = fields.Char('email')
    in_store_deals = fields.Boolean('In-Store Deals')
    alerts = fields.Boolean('Alerts')
    latest_news = fields.Boolean('Latest news')
    events = fields.Boolean('Events')
    do_not_send_mail = fields.Boolean('Do Not Send Email')

    phone_notification = fields.Char('phone')
    phone_in_store_deals = fields.Boolean('In-Store Deals1')
    phone_alerts = fields.Boolean('alerts')
    phone_latest_news = fields.Boolean('Latest News')
    phone_events = fields.Boolean('Event')
    phone_do_not_send_mail = fields.Boolean('Do not Send Email')

    primary_store = fields.Selection([
        ('BMW MC of Seattle', 'BMW MC of Seattle'),
        ('Ducati Seattle', 'Ducati Seattle'),
        ('Ducati Redmond', 'Ducati Redmond'),
        ('Hindshaws', 'Hindshaws'),
        ('Indian Motorcycles of Auburn', 'Indian')])



    @api.model
    def create(self, vals):
        """ Override create method """
        customer_id = super(Customer, self).create(vals)
        return customer_id

    # @api.multi
    def write(self, vals):
        """ Override write method to export customers when any details is changed """
        customer = super(Customer, self).write(vals)
        return customer

    # @api.multi
    def sync_customer(self):
        for backend in self.backend_id:
            self.export(backend)
        return

    def importer(self, backend):        
        """ import and create or update backend mapper """
        if len(self.ids)>1:
            for obj in self:
                obj.single_importer(backend)
            return

        method = 'customer_import'
        arguments = [None,self]
        importer = WpCustomerImport(backend)

        count = backend.start_record_num
        end = backend.end_record_num

        if not (count and end):
            raise Warning(_("Enter Valid Start And End  Record Number"))
        
        data = True
        customer_ids = []
        while(data):                      
            res = importer.import_customer(method, arguments, count)['data']
            # if(res):
            if(res) and count <= end:
                customer_ids.extend(res)
            else:
                data = False                
            count += 1
            
        for customer_id in customer_ids:
            print (" sssssssssssssssssssssssssss")
            print(customer_id['email'],"customer_idmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
            self.single_importer(backend, customer_id)


       
    def single_importer(self,backend,customer_id,status=True,woo_id=None):
        # method = 'customer_import'
        # try:
        #     customer_id = customer_id['id']
        # except:
        #     customer_id = customer_id

        #new code added
        gust_customer = customer_id
        method = 'customer_import'
        try:
            customer_id = customer_id['id']
        except:
            customer_id = customer_id

        # mapper = self.backend_mapping.search(
        #     [('backend_id', '=', backend.id), ('woo_id', '=', customer_id)], limit=1)
        # arguments = [customer_id or None,mapper.customer_id or self]

        ####new code added
        if customer_id == 0:
            mapper = self.backend_mapping.search(
                [('backend_id', '=', backend.id), ('woo_email', '=', gust_customer["billing"]["email"])], limit=1)
        else:
            mapper = self.backend_mapping.search(
                [('backend_id', '=', backend.id), ('woo_id', '=', customer_id)], limit=1)

        ############################

        importer = WpCustomerImport(backend)
        arguments = [customer_id or None, mapper.customer_id or self]
        # res = importer.import_customer(method, arguments)

        #new code added
        if customer_id != 0:
            res = importer.import_customer(method, arguments)

            record = res['data']

            if mapper:
                importer.write_customer(backend, mapper, res)

            else:
                res_partner = importer.create_customer(backend, mapper, res, status)
                if ((res['status'] == 200 or res['status'] == 201) and res_partner):
                    vals = {
                        'woo_id': res['data']['id'],
                        'backend_id': backend.id,
                        'customer_id': res_partner.id,
                        'woo_email': gust_customer["billing"]["email"],
                        'email': gust_customer["billing"]["email"]

                    }
                    self.backend_mapping.create(vals)

            if mapper and (res['status'] == 200 or res['status'] == 201):
                vals = {
                    'woo_id': res['data']['id'],
                    'backend_id': backend.id,
                    'customer_id': mapper.customer_id.id,
                }
                self.backend_mapping.write(vals)
        else:

            res = {'status': 200, 'data': gust_customer}
            if mapper:
                importer.write_customer(backend, mapper, res)

            else:
                res_partner = importer.create_customer(backend, mapper, res, status)
                if (res['status'] == 200 or res['status'] == 201):
                    vals = {
                        'woo_id': res['data']['id'],
                        'backend_id': backend.id,
                        'customer_id': res_partner.id,
                        'woo_email': gust_customer["billing"]["email"],
                        'email': gust_customer["billing"]["email"]

                    }
                    self.backend_mapping.create(vals)




    # @api.multi
    # @job
    def export(self, backend):
        """ export customer details, save username and create or update backend mapper """
        if len(self.ids)>1:
            for obj in self:
                obj.export(backend)
            return
        # if not self.customer_rank > 0:
        #     return
        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('customer_id', '=', self.id)], limit=1)
        method = 'customer'
        arguments = [mapper.woo_id or None, self]
        export = WpCustomerExport(backend)
        res = export.export_customer(method, arguments)
        print("ppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp")
        if mapper and (res['status'] == 200 or res['status'] == 201):
            self.write({'username': res['data']['username']})
            mapper.write(
                {'customer_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})
        elif (res['status'] == 200 or res['status'] == 201):
            self.write({'username': res['data']['username']})
            self.backend_mapping.create(
                {'customer_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})
        elif (res['status'] == 400 and res['data']['code'] == 'registration-error-email-exists'):
            if 'resource_id' in res['data']['data'].keys():
                self.backend_mapping.create(
                    {'customer_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['data']['resource_id']})


class CustomerMapping(models.Model):

    """ Model to store woocommerce id for particular customer"""
    _name = 'wordpress.odoo.res.partner'
    _description="wordpress.odoo.res.partner"
    _rec_name = 'customer_id'

    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        ondelete='cascade',
        readonly=False,
        required=True,
    )

    backend_id = fields.Many2one(
        comodel_name='wordpress.configure',
        string='Website',
        ondelete='set null',
        store=True,
        readonly=False,
        required=False,
    )

    woo_id = fields.Char(string='Woo id')
    address_type = fields.Char(string='Address Type')
    internal_name = fields.Char(string='Internal Name')
    child_id = fields.Char(string='Child_id')
    woo_email = fields.Char(string='Woo email')
    email = fields.Char(string='Email',required=True)


def import_record(cr, uid, ids, context=None):
    """ Import a record from woocommerce """
    importer.run(woo_id)
