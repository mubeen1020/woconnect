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
from odoo.exceptions import Warning
from ..model.api import API
from ..unit.backend_adapter import WpImportExport
import json


import logging
from collections import defaultdict
import base64
from odoo import models, fields, api, _
from ..unit.product_exporter import WpProductExport
from ..unit.product_tag_exporter import WpProductTagExport
from ..unit.product_importer import WpProductImport

_logger = logging.getLogger(__name__)


class ProductTags(models.Model):

    """ Models for product tags """
    _name = "product.product.tag"
    _description = 'product.product.tag'
    _order = 'sequence, name'

    sequence = fields.Integer('Sequence', help="Determine the display order")
    name = fields.Char(string="Name")
    slug = fields.Char(string="Slug")
    desc = fields.Text(string="Description")
    product_id = fields.Many2one(comodel_name='product.template',
                                 string='Product')
    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.product.tag',
                                      string='Product tag mapping',
                                      inverse_name='product_tag_id',
                                      readonly=False,
                                      required=False,)
    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                  string='Woo Backend',
                                  store=True,
                                  readonly=False,
                                  required=False,
                                  )

    @api.model
    def create(self, vals):
        """ Override create method """
        tag_id = super(ProductTags, self).create(vals)
        return tag_id

    # @api.multi
    def sync_tag(self):
        for backend in self.backend_id:
            self.export_product_tag(backend)
        return

    # @api.multi
    def export_product_tag(self, backend):
        """ export product tags, save slug and create or update backend mapper """
        method = 'tag'
        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('product_tag_id', '=', self.id)])
        export = WpProductTagExport(backend)
        arguments = [mapper.woo_id or None, self]
        #directory: /unit/product_tag_export_py/export_product_tag(self, method, arguments)
        res = export.export_product_tag(method, arguments)
        if mapper and (res['status'] == 200 or res['status'] == 201):
            self.write({'slug': res['data']['slug']})
            mapper.write(
                {'product_tag_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})
        elif (res['status'] == 200 or res['status'] == 201):
            self.write({'slug': res['data']['slug']})
            self.backend_mapping.create(
                {'product_tag_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']})
        #tag_name already available in wp and newly same tag_name created in odoo and not sync
        elif not mapper and res['status'] == 400:
            if 'resource_id' in res['data']['data']:
                self.backend_mapping.create(
                    {'product_tag_id':self.id, 'backend_id':backend.id, 'woo_id':res['data']['data']['resource_id']}
                )


class ProductTagMapping(models.Model):

    """ Model to store woocommerce id for particular product"""
    _name = 'wordpress.odoo.product.tag'
    _description = 'wordpress.odoo.product.tag'
    _rec_name = 'product_tag_id'

    product_tag_id = fields.Many2one(comodel_name='product.product.tag',
                                     string='Product tag',
                                     ondelete='cascade',
                                     readonly=False,
                                     required=True,)

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                 string='Backend',
                                 ondelete='set null',
                                 store=True,
                                 readonly=False,
                                 required=False,)

    woo_id = fields.Char(string='Woo id')


class ProductMultiImages(models.Model):

    """ Models for product images """
    _name = "product.multi.image"
    _description = 'product.multi.image'

    image = fields.Binary(string="Image")
    sequence = fields.Char(string="Seq")
    name = fields.Char(string="Name")
    default = fields.Boolean(string="Main Product Image")
    woo_id = fields.Char(string="Woo id")
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    position = fields.Integer(string="Position")
    src = fields.Char(string="Source")
    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.product.image',
                                      string='Product Image mapping',
                                      inverse_name='product_image_id',
                                      readonly=False,
                                      required=False,)
    backend_id = fields.Many2many(comodel_name='wordpress.configure',
                                  string='Woo Backend',
                                  store=True,
                                  readonly=False,
                                  required=True,
                                  )


class ProductImageMapping(models.Model):

    """ Model to store woocommerce id for particular product"""
    _name = 'wordpress.odoo.product.image'
    _description = 'wordpress.odoo.product.image'
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product',
                                 ondelete='cascade',
                                 readonly=False,
                                 required=True,)
    product_image_id = fields.Many2one(comodel_name='product.multi.image',
                                       string='Product image',
                                       ondelete='cascade',
                                       readonly=False,
                                       required=True,)

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                 string='Backend',
                                 ondelete='set null',
                                 store=True,
                                 readonly=False,
                                 required=False,)

    woo_id = fields.Char(string='Woo id')


class ProductTemplate(models.Model):

    """ Models for woocommerce product template """
    _inherit = 'product.template'

    website_published = fields.Boolean()
    from_wp = fields.Boolean('from_wp')
    # categ_id = fields.Many2one(string='Pricing/Primary Category')
    categ_ids = fields.Many2many(comodel_name='product.category',
                                 relation='product_categ_rel',
                                 column1='product_id',
                                 column2='categ_id',
                                 string='Product Categories')
    image_ids = fields.One2many(related='product_variant_ids.image_ids',
                                string='Product Images')
    tag_ids = fields.Many2many(comodel_name='product.product.tag',
                               inverse_name='product_id',
                               string='Product Tags')
    short_description = fields.Text('Short Description')
    slug = fields.Char('Slug')
    list_price = fields.Float('Final Sale Price')
    regular_price = fields.Float('Regular Price')
    sale_price = fields.Float('Sale Price')
    standard_price = fields.Float('Purchase Price')
    wp_managing_stock = fields.Boolean('WP Managing Stock')

    

    #update for float import
    website_size_x = fields.Float('Length')
    website_size_y = fields.Float('Width')
    website_size_z = fields.Float('Height')


    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.product.template',
                                      string='Product mapping',
                                      inverse_name='product_id',
                                      readonly=False,
                                      required=False,
                                      )

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                  string='Woo Backend',
                                  store=True,
                                  readonly=False,
                                  required=False,
                                  )

    image_ids = fields.One2many(related='product_variant_ids.image_ids',
                                string='Product Images')

    mult_prod_id = fields.Many2one('wordpress.odoo.multi.product.image', 'Product img')

    @api.model
    def create(self, vals):
        """ Override create method to check price before creating and export """
        if not 'regular_price' in vals.keys():
            vals['regular_price'] = 0
        if not 'sale_price' in vals.keys():
            vals['sale_price'] = 0
        product_id = super(ProductTemplate, self).create(vals)
        return product_id

    # @api.multi
    def write(self, vals):
        """ Override write method to export when any details is changed """
        if (self.backend_id or 'backend_id' in vals.keys()) and not ('default_code' in vals.keys() or 'slug' in vals.keys()):
            if not 'regular_price' in vals.keys():
                vals['regular_price'] = self.regular_price
            if not 'sale_price' in vals.keys():
                vals['sale_price'] = self.sale_price
            product = super(ProductTemplate, self).write(vals)
            return product
        else:
            product = super(ProductTemplate, self).write(vals)
            return product

    # @api.multi
    def sync_product(self):
        for backend in self.backend_id:
            self.export_product(backend)
        return

    # @api.multi
    # @job
    def importer(self, backend):
        """ import and create or update backend mapper """
        if len(self.ids)>1:
            for obj in self:
                # obj.with_delay().single_importer(backend)
                obj.single_importer(backend)
            return

        method = 'product_import'
        arguments = [None,self]
        importer = WpProductImport(backend)

        # count = 1        
        count = backend.start_record_num
        end = backend.end_record_num

        if not (count and end):
            raise Warning(_("Enter Valid Start And End  Record Number"))
        
        data = True
        product_ids = []
        while(data):
            res = importer.import_product(method, arguments, count)['data']
            # if(res):
            if(res) and count <= end:
                product_ids.extend(res)
            else:
                data = False
            count += 1
        for pro_id in product_ids:
            # self.with_delay().single_importer(backend, customer_id)
            self.single_importer(backend, pro_id)

    # @api.multi
    # @job
    def single_importer(self,backend,product_id,status=True,woo_id=None):
        method = 'product_import'
        try:
            product_id = product_id['id']
        except:
            product_id = product_id

        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('woo_id', '=', product_id)], limit=1)
        arguments = [product_id or None,mapper.product_id or self]

        importer = WpProductImport(backend)
        res = importer.import_product(method, arguments)

        record = res['data']

        if mapper:
            importer.write_product(backend,mapper,res)
        else:
            product_template = importer.create_product(backend,mapper,res,status)
        
        #added because create_product fun
        mapper = self.backend_mapping.search([('backend_id', '=', backend.id), ('woo_id', '=', product_id)], limit=1)

        if mapper and (res['status'] == 200 or res['status'] == 201):
            vals = {
                'woo_id' : res['data']['id'],
                'backend_id' : backend.id,
                'product_id' : mapper.product_id.id,
            }
            # self.backend_mapping.write(vals)
            if res['data']['images']:
                vals['image_id'] = res['data']['images'][0]['id']
            mapper.product_id.backend_mapping.write(vals)
            if res['data']['categories']:
                self.category_mapper(mapper,res,backend)

        elif (res['status'] == 200 or res['status'] == 201):
            vals = {
                'woo_id' : res['data']['id'],
                'backend_id' : backend.id,
                'product_id' : product_template.id,
            }
            # self.backend_mapping.create(vals)
            if res['data']['images']:
                vals['image_id'] = res['data']['images'][0]['id']
            product_template.backend_mapping.create(vals)
            if res['data']['categories']:
                mapper = self.backend_mapping.search([('backend_id', '=', backend.id), ('woo_id', '=', product_id)],
                                                     limit=1)
                product_template.category_mapper(mapper, res, backend)

    def category_mapper(self, mapper, res, backend):
        """ create or update category mapper """
        if res['data']['categories']:
            category_id = mapper.product_id.categ_id
            categ_mapping = category_id.backend_mapping.search([('backend_id', '=', backend.id),
                                                                ('category_id', '=', category_id.id)])

            if categ_mapping:
                vals = {'category_id': category_id.id, 'backend_id': backend.id,
                        'woo_id': res['data']['categories'][0]['id']}
                categ_mapping.write(vals)
            else:
                vals = {'category_id': category_id.id, 'backend_id': backend.id,
                        'woo_id': res['data']['categories'][0]['id']}
                category_id.backend_mapping.create(vals)


    def export_product(self, backend):
        """ export product details, save default code & slug and create or update backend mapper """
        mapper = self.backend_mapping.search(
            [('backend_id', '=', backend.id), ('product_id', '=', self.id)], limit=1)
        arguments = []
        method = 'products'
        arguments = [mapper.woo_id or None, self]
        export = WpProductExport(backend)
        res = export.export_product(method, arguments)
        if mapper and (res['status'] == 200 or res['status'] == 201):
            self.write(
                {'default_code': res['data']['sku'], 'slug': res['data']['slug']})
            vals = {'product_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']}

            if res['data']['images']:
                vals['image_id'] = res['data']['images'][0]['id']
            mapper.write(vals)
            # self.map_product(res, backend)

        elif (res['status'] == 200 or res['status'] == 201):
            self.write(
                {'default_code': res['data']['sku'], 'slug': res['data']['slug']})
            # self.backend_mapping.create({'product_id': self.id, 'backend_id': backend.id, 'woo_id': res[
            #     'data']['id']})
            vals = {'product_id': self.id, 'backend_id': backend.id, 'woo_id': res['data']['id']}
            if res['data']['images']:
                vals['image_id'] = res['data']['images'][0]['id']
            self.backend_mapping.create(vals)
            # self.map_product(res, backend)

    def map_product(self, res, backend):
        """ map product variants with particular woo id and create or update backend mapper"""
        if res['data']['variations']:
            for record in res['data']['variations']:
                variant_id = self.get_variations(
                    self.product_variant_ids, record, backend)
                mapper = variant_id.backend_mapping.search(
                    [('backend_id', '=', backend.id), ('product_id', '=', variant_id.id)])
                variant_id.write(
                    {'default_code': res['data']['sku'], 'slug': res['data']['slug']})
                if mapper:
                    mapper.write({'product_id': variant_id.id, 'backend_id': backend.id, 'woo_id': record[
                        'id'], 'image_id': record['image'][0]['id']})
                else:
                    mapper.create({'product_id': variant_id.id, 'backend_id': backend.id, 'woo_id': record[
                        'id'], 'image_id': record['image'][0]['id']})

        return True


    def get_variations(self, variant_ids, record, backend):
        """ check and get the correct variant for particular woo id"""
        for variant_id in variant_ids:
            count = 0
            for attribute_value in variant_id.attribute_value_ids:
                for record_attr in record['attributes']:
                    if record_attr['option'] == attribute_value.name:
                        count += 1
                        if len(record['attributes']) == count:
                            return variant_id
                        else:
                            break
   

    def map_images(self, res, backend):
        """ map product images with particular woo id and create or update backend mapper"""
        if res['data']['images']:
            for image_data in res['data']['images']:
                if image_data['id'] != 0:
                    if image_data['position'] != 0:
                        image_id = self.get_image_id(
                            self.image_ids, image_data, backend)
                        if not image_id:
                            continue
                        mapper = image_id.backend_mapping.search([('backend_id', '=', backend.id),
                                                                  ('product_image_id',
                                                                   '=', image_id.id),
                                                                  ('woo_id', '=', int(image_data['id']))],
                                                                 limit=1)
                        if not mapper:
                            mapper.create({'product_image_id': image_id.id,
                                           'product_id': self.id,
                                           'backend_id': backend.id,
                                           'woo_id': int(image_data['id'])})
                        else:
                            mapper.write({'product_image_id': image_id.id,
                                          'product_id': self.id,
                                          'backend_id': backend.id,
                                          'woo_id': int(image_data['id'])})
        return True

    def get_image_id(self, image_ids, record, backend):
        """ check and get the correct variant for particular woo id"""
        for image_id in image_ids:
            if record['position'] == image_id.sequence:
                return image_id


class ProductMapping(models.Model):

    """ Model to store woocommerce id for particular product"""
    _name = 'wordpress.odoo.product.template'
    _description = 'wordpress.odoo.product.template'
    _rec_name = 'product_id'

    product_id = fields.Many2one(comodel_name='product.template',
                                 string='Product Template',
                                 ondelete='cascade',
                                 readonly=False,
                                 required=True,
                                 )

    image_id = fields.Char('Image id')

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                 string='Backend',
                                 ondelete='set null',
                                 store=True,
                                 readonly=False,
                                 required=False,
                                 )

    woo_id = fields.Char(string='Woo id')


class ProductProduct(models.Model):

    """ Models for woocommerce product variant """
    _inherit = 'product.product'

    woo_id = fields.Char(string='Woo id')
    image_ids = fields.One2many(comodel_name='product.multi.image',
                                inverse_name='product_id',
                                string='Product Images')
    regular_price = fields.Float('Regular Price')
    sale_price = fields.Float('Sale Price')
    lst_price = fields.Float('Final Sale price')
    website_size_x = fields.Integer('Length')
    website_size_y = fields.Integer('Width')
    website_size_z = fields.Integer('Height')
    wp_managing_stock = fields.Boolean('WP Managing Stock')

    backend_mapping = fields.One2many(comodel_name='wordpress.odoo.product.product',
                                      string='Product mapping',
                                      inverse_name='product_id',
                                      readonly=False,
                                      required=False,
                                      )

    woo_varient_price = fields.Char(string='shopify_varient_price')



    def _compute_product_price_extra(self):
        for product in self:
            if not product.woo_varient_price:
                product.price_extra = sum(product.product_template_attribute_value_ids.mapped('price_extra'))
            else:
                # for product in self:
                product.price_extra = float(product.woo_varient_price)

    @api.model
    def create(self, vals):
        """ Override create method """
        if 'image_ids' in vals.keys():
            for image in vals['image_ids'] :
                if image[2]!= False:
                    name=str(image[2]['name']).split(".")[0]
                    image[2]['name']=name
        return super(ProductProduct, self).create(vals)

    # @api.multi
    def write(self, vals):
        """ Override write method to export when any details is changed """
        if 'image_ids' in vals.keys():
            for image in vals['image_ids'] :
                if image[2]!= False:
                    name=str(image[2]['name']).split(".")[0]
                    image[2]['name']=name
        return super(ProductProduct, self).write(vals)

    # @api.multi
    def sync_product(self):
        for backend in self.product_tmpl_id.backend_id:
            self.product_tmpl_id.export_product(backend)
        return

    # @api.multi
    def export_product(self, backend):
        """ export product variant details, and create or update backend mapper """
        return self.product_tmpl_id.export_product(backend)

    # @api.multi
    def _website_price(self):
        try:
            res = super(ProductProduct, self)._website_price()
        except AttributeError:
            pass


class Website(models.Model):
    _inherit = "website"

    @api.model
    def get_current_website(self, fallback=True):
        try:
            res = super(Website, self).get_current_website()
        except RuntimeError:
            website_id = self._get_current_website_id('localhost')
            return self.browse(website_id)
        return res

    # @api.multi
    def get_current_pricelist(self):
        try:
            res = super(Website, self).get_current_pricelist()
        except RuntimeError:
            return
        return res

    # @api.multi
    def get_pricelist_available(self, show_visible=False):
        try:
            res = super(Website, self).get_pricelist_available()
        except RuntimeError:
            return self.env['product.pricelist'].search([('id', '=', 1)]).id
        return res


class ProductProductMapping(models.Model):

    """ Model to store woocommerce id for particular product variant"""
    _name = 'wordpress.odoo.product.product'
    _description = 'wordpress.odoo.product.product'
    _rec_name = 'product_id'

    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product',
                                 ondelete='cascade',
                                 readonly=False,
                                 required=True,
                                 )

    image_id = fields.Char('Image id')

    backend_id = fields.Many2one(comodel_name='wordpress.configure',
                                 string='Backend',
                                 ondelete='set null',
                                 store=True,
                                 readonly=False,
                                 required=False,
                                 )

    woo_id = fields.Char(string='Woo id')


class StockInventory(models.TransientModel):

    """ Models for woocommerce product qty change"""
    _inherit = "stock.change.product.qty"

    wp_state = fields.Char('wp state')

    # @api.multi
    def write(self, vals):
        """ Override write method to update the product qty"""
        if 'wp_state' in vals.keys():
            if vals['wp_state'] == 'done':
                self.change_product_qty()
        return super(StockInventory, self).write(vals)

    # @api.multi
    def update_stock(self, vals):
        """ Changes the Product Quantity by making a Physical Inventory. """
        update_stock_id = self.env['stock.change.product.qty'].create({'product_tmpl_id': vals['product_tmpl_id'],
                                                                       'lot_id': False,
                                                                       'product_id': vals['product_id'],
                                                                       'new_quantity': vals['new_quantity'],
                                                                       'location_id': vals['location_id'],
                                                                       'product_variant_count': vals['product_variant_count']})
        update_stock_id.change_product_qty()
        return True