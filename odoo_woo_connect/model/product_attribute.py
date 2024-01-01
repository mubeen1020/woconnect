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

import logging
from collections import defaultdict
import base64
from odoo import models, fields, api, _
from ..unit.product_attribute_exporter import WpProductAttributeExport
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class ProductAttribute(models.Model):

    """ Models for woocommerce product attributes """
    _inherit = 'product.attribute'

    slug = fields.Char('Slug')

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                  string='Backend',
                                  store=True,
                                  readonly=False,
                                  required=False,
                                  )

    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.attribute',
                                      string='Attribute mapping',
                                      inverse_name='attribute_id',
                                      readonly=False,
                                      required=False,
                                      )

    @api.model
    def create(self, vals):
        """ Override create method """
        attribute_id = super(ProductAttribute, self).create(vals)
        return attribute_id

    # @api.multi
    def write(self, vals):
        """ Override write method to export when any details is changed """
        attribute = super(ProductAttribute, self).write(vals)
        return attribute

    # @api.multi
    def sync_attribute(self):
        for backend in self.backend_id:
            self.export_product_attribute(backend)
        """ Sync Attribute Value"""
        attribute_value = self.env['product.attribute.value'].search([('attribute_id','=',self.id)])
        for att_val in attribute_value : 
            ProductAttributeValue.sync_attribute_value(att_val)
        return

    # @api.multi
    def export_product_attribute(self, backend):
        """ export product attributes, save slug and create or update backend mapper """
        method = 'attribute'
        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('attribute_id', '=', self.id)])
        export = WpProductAttributeExport(backend)
        arguments = [mapper.woo_id or None, self]
        print("In export attr%s" % arguments)
        res = export.export_product_attribute(method, arguments)

        if mapper and (res['status'] == 200 or res['status'] == 201):
            self.write({'slug': res['data']['slug']})
            mapper.write(
                {'attribute_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})
        elif (res['status'] == 200 or res['status'] == 201):
            self.write({'slug': res['data']['slug']})
            self.backend_mapping.create(
                {'attribute_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})


def import_record(cr, uid, ids, context=None):
    """ Import a record from woocommerce """
    importer.run(woo_id)


class ProductAttributeMapping(models.Model):

    """ Model to store woocommerce id for particular product attribute """
    _name = 'wordpress.odoo.attribute'
    _description = 'wordpress.odoo.attribute'
    _rec_name = 'attribute_id'

    attribute_id = fields.Many2one(comodel_name='product.attribute',
                                   string='Product Attribute',
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

    woo_id = fields.Char(string='woo_id')


class ProductAttributeValue(models.Model):

    """ Models for woocommerce product attribute value """
    _inherit = 'product.attribute.value'

    slug = fields.Char('Slug')
    backend_id = fields.Many2many(comodel_name='wordpress.configure',
                                  string='Backend',
                                  store=True,
                                  readonly=False,
                                  required=False,
                                  )
    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.attribute.value',
                                      string='Attribute value mapping',
                                      inverse_name='attribute_value_id',
                                      readonly=False,
                                      required=False,
                                      )

    @api.model
    def create(self, vals):
        """ Override create method """
        attribute_value = super(ProductAttributeValue, self).create(vals)
        return attribute_value

    # @api.multi
    def write(self, vals):
        """ Override write method to export when any details is changed """
        attribute_value = super(ProductAttributeValue, self).write(vals)
        return attribute_value

    # @api.multi
    def sync_attribute_value(self):
        for backend in self.backend_id:
            self.export_product_attribute_value(backend)
        return

    # @api.multi
    def export_product_attribute_value(self, backend):
        """ export product attribute value details, and create or update backend mapper """
        method = 'attribute_value'
        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('attribute_value_id', '=', self.id)])
        attr_mapper = self.attribute_id.backend_mapping.search(
            [('backend_id', '=', backend.id), ('attribute_id', '=', self.attribute_id.id)])
        export = WpProductAttributeExport(backend)
        arguments = [mapper.woo_id or None, self, attr_mapper]
        res = export.export_product_attribute_value(method, arguments)
        if mapper and (res['status'] == 200 or res['status'] == 201):
            self.write({'slug': res['data']['slug']})
            mapper.write({'attribute_value_id': self.id,
                          'backend_id': backend.id, 'woo_id': res['data']['id']})
        elif (res['status'] == 200 or res['status'] == 201):
            self.write({'slug': res['data']['slug']})
            self.backend_mapping.create(
                {'attribute_value_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})


class ProductAttributeValueMapping(models.Model):

    """ Model to store woocommerce id for particular product attribute value"""
    _name = 'wordpress.odoo.attribute.value'
    _description = 'wordpress.odoo.attribute.value'

    attribute_value_id = fields.Many2one(comodel_name='product.attribute.value',
                                         string='Product Attribute Value',
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

    woo_id = fields.Char(string='woo_id')