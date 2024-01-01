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

import logging
#import urllib2
#import xmlrpclib
from collections import defaultdict
import base64
from odoo import models, fields, api, _
from ..unit.tax_exporter import WpTaxExport
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class Tax(models.Model):

    """ Models for woocommerce res partner """
    _inherit = 'account.tax'

    slug = fields.Char('slug')
    state_id = fields.Many2one(
        "res.country.state", string='State', ondelete='restrict')
    count_id = fields.Many2one(
        "res.country", string='Country', ondelete='restrict')
    postcode = fields.Char('postcode')
    city = fields.Char('city')
    priority = fields.Integer('priority')
    compound = fields.Boolean('compound')
    shipping = fields.Boolean('shipping')
    order = fields.Integer('order')
    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                  string='WP Backend',
                                  store=True,
                                  readonly=False,
                                  required=False,
                                  )
    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.tax',
                                      string='Tax mapping',
                                      inverse_name='tax_id',
                                      readonly=False,
                                      required=False,
                                      )

    # @api.multi
    def sync_tax(self):
        for backend in self.backend_id:
            self.export_tax(backend, 'standard')
        return

    # @api.multi
    def export_tax(self, backend, tax_class):
        """ export tax details, save username and create or update backend mapper """
        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('tax_id', '=', self.id)])
        arguments = [mapper.woo_id or None, self]
        export = WpTaxExport(backend)
        if self.amount_type == 'group':
            res = export.export_tax_class('tax_class', arguments)
        else:
            res = export.export_tax('tax', arguments)
            for child_tax in self.children_tax_ids:
                for backend in child_tax.backend_id:
                    child_tax.export_tax(backend, self.slug)
        if mapper and (res['status'] == 200 or res['status'] == 201):
            if 'slug' in res['data'].keys():
                self.write({'slug': res['data']['slug']})
            mapper.write(
                {'tax_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})  # 'woo_id': res['data']['id']
        elif (res['status'] == 200 or res['status'] == 201):
            if 'slug' in res['data'].keys():
                self.write({'slug': res['data']['slug']})
            self.backend_mapping.create(
                {'tax_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})  # 'woo_id': res['data']['id']


class TaxMapping(models.Model):

    """ Model to store woocommerce id for particular tax"""
    _name = 'wordpress.odoo.tax'
    _description = 'wordpress.odoo.tax'
    _rec_name = 'tax_id'


    tax_id = fields.Many2one(comodel_name='account.tax',
                             string='Tax',
                             ondelete='cascade',
                             readonly=False,
                             required=True,
                             )

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                 string='Backend',
                                 ondelete='set null',
                                 store=True,
                                 readonly=False,
                                 required=False,
                                 )

    woo_id = fields.Char(string='Woo id')