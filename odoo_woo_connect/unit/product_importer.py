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
import re
import requests
import logging
from ..model.api import API
from datetime import datetime
from datetime import timedelta
from PIL import Image
import requests
from io import BytesIO
import io
import base64
from ..unit.backend_adapter import WpImportExport

_logger = logging.getLogger(__name__)


class WpProductImport(WpImportExport):
    """ Models for woocommerce product ixport """

    def get_api_method(self, method, args, count=None, date=None):
        """ get api for product"""
        api_method = None
        if method == 'product_import':
            if not args[0]:
                api_method = 'products?per_page=1&page=' + str(count)
            elif args[0] and isinstance(args[0], int):
                api_method = 'products/' + str(args[0])
            else:
                api_method = 'products/' + str(args[0]['id'])

        print(api_method)
        return api_method

    def import_product(self, method, arguments, count=None, date=None):
        """Import product data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        result = {}
        res = self.importer(method, arguments, count)
        try:
            if 'false' or 'true' or 'null' in res.content:
                result = res.content.decode('utf-8')
                result = result.replace(
                    'false', 'False')
                result = result.replace('true', 'True')
                result = result.replace('null', 'False')
                result = eval(result)
            else:
                result = eval(res.content)
        except:
            _logger.error("api.call(%s, %s) failed", method, arguments)
            raise
        else:
            _logger.debug("api.call(%s, %s) returned %s ",
                          method, arguments, result)
        print(result,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
        
        return {'status': res.status_code, 'data': result or {}}

    def create_product(self, backend, mapper, res, status=True):
        
        if (res['status'] == 200 or res['status'] == 201):
            bkend_id = mapper.backend_id.search([('id', '=', backend.id)])

            if res['data']['tags']:
                wp_tags = res['data']['tags']
                wp_tag_ids = self.get_tags(wp_tags, mapper, bkend_id)
            else:
                wp_tag_ids = []

            if res['data']['images']:
                img = res['data']['images'][0]['src'].replace("\\", "")
                # response = requests.get(img)

                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(img, headers=headers)

                image = Image.open(BytesIO(response.content))
                imgByteArr = io.BytesIO()
                image.save(imgByteArr, format='PNG')
                imgByteArr = imgByteArr.getvalue()
                images = base64.b64encode(imgByteArr)
            else:
                images = None

            try:

                # if 'categories' in res['data'].keys():
                if res['data']['categories']:
                    woo_category = res['data']['categories'][0]['name']
                    woo_slug = res['data']['categories'][0]['slug']
                    categ_id = mapper.env['product.category'].search(
                        [('name', '=', woo_category), ('backend_id', '=', backend.id), ('slug', '=', woo_slug)],
                        limit=1).id
                    # categ_id = mapper.env['product.category'].search([('name', '=', woo_category) and ('slug', '=', woo_slug)]).id
                if not categ_id:
                    vals = {
                        "name": res['data']['categories'][0]['name'],
                        "slug": res['data']['categories'][0]['slug'],
                        "backend_id": bkend_id.id,
                        "woo_id": res['data']['categories'][0]['id']

                    }
                    create_categ_id = mapper.env['product.category'].create(vals)
                if res['data']['categories']:
                    woo_category = res['data']['categories'][0]['name']
                    woo_slug = res['data']['categories'][0]['slug']
                    categ_id = mapper.env['product.category'].search(
                        [('name', '=', woo_category), ('backend_id', '=', backend.id), ('slug', '=', woo_slug)],
                        limit=1).id
                    # categ_id = mapper.env['product.category'].search(
                    #     [('name', '=', woo_category) and ('slug', '=', woo_slug)]).id


            except:
                pass

            if res['data']['attributes']:
                attributes_value = []
                for attribute in res['data']['attributes']:
                    attribute_id = mapper.env['product.attribute'].search([('name', '=', attribute['name'])]).id
                    attribute_value_ids = []
                    if not attribute_id:
                        # create attribute_id
                        # self.env['product.attribute'].create({'name': 'Memory', 'sequence': 1})
                        attribute_create = mapper.env['product.attribute'].create({'name': attribute['name']})
                        attribute_id = attribute_create.id

                    for attribute_val in attribute['options']:
                        attribute_value_id = ''
                        # attribute_value_id = mapper.env['product.attribute.value'].search([('name','=', attribute_val)]).id

                        # attribute_value_id = mapper.env['product.attribute.value'].search([('name','=', attribute_val) and ('attribute_id','=', attribute_id)]).id

                        product_attribute_value_ids = mapper.env['product.attribute.value'].search(
                            [('name', '=', attribute_val)])
                        for product_attribute_value_id in product_attribute_value_ids:
                            if product_attribute_value_id.attribute_id.id == attribute_id:
                                attribute_value_id = product_attribute_value_id.id

                        if not attribute_value_id:
                            # create attribute_value
                            attribute_value_create = mapper.env['product.attribute.value'].create(
                                {'name': attribute_val, 'attribute_id': attribute_id, 'sequence': 1})
                            # attribute_value_create = mapper.env['product.attribute.value'].create({'name': attribute_val, 'attribute_id': attribute_id})
                            attribute_value_id = attribute_value_create.id
                        attribute_value_ids.append(attribute_value_id)

                    attributes_value.append((0, 0, {'attribute_id': attribute_id, 'value_ids': [(6, 0, attribute_value_ids)]}))
            else:
                attributes_value = []

            if res['data']['type'] == 'variable':

                vals = {

                    'list_price': 0.0,
                    'type': 'product',
                    'name': res['data']['name'],
                    'categ_id': categ_id,
                    # 'qty_available' : res['data']['stock_quantity'],
                    'backend_id': bkend_id.id,
                    'tag_ids': [[6, 0, wp_tag_ids]],
                    'attribute_line_ids': attributes_value,
                    'image_medium': images,
                    'website_size_x': res['data']['dimensions']['length'],
                    'website_size_y': res['data']['dimensions']['width'],
                    'website_size_z': res['data']['dimensions']['height'],
                    'weight': res['data']['weight'],
                    'default_code': res['data']['sku'],
                    'short_description': re.sub(re.compile('<.*?>'), '', res['data']['short_description']),
                    'description': re.sub(re.compile('<.*?>'), '', res['data']['description']),

                }

            else:
                vals = {
                    'sale_price': res['data']['price'],
                    'regular_price': res['data']['regular_price'],
                    'list_price': res['data']['price'],
                    'type': 'product',
                    'name': res['data']['name'],
                    'categ_id': categ_id,
                    # 'qty_available' : res['data']['stock_quantity'],
                    'backend_id': bkend_id.id,
                    'tag_ids': [[6, 0, wp_tag_ids]],
                    'attribute_line_ids': attributes_value,
                    'image_medium': images,
                    'website_size_x': res['data']['dimensions']['length'],
                    'website_size_y': res['data']['dimensions']['width'],
                    'website_size_z': res['data']['dimensions']['height'],
                    'weight': res['data']['weight'],
                    'default_code': res['data']['sku'],
                    'short_description': re.sub(re.compile('<.*?>'), '', res['data']['short_description']),
                    'description': re.sub(re.compile('<.*?>'), '', res['data']['description']),

                }




            product = mapper.product_id.create(vals)

            skip_image = 0
            image1 = []
            # if res['data']['images']:
            #     for mult_img in res['data']['images']:
            #         if skip_image != 0:
            #             img = mult_img['src'].replace("\\", "")
            #             headers = {'User-Agent': 'Mozilla/5.0'}
            #             response = requests.get(img, headers=headers)
            #             image = Image.open(BytesIO(response.content))
            #             imgByteArr = io.BytesIO()
            #             image.save(imgByteArr, format='PNG')
            #             imgByteArr = imgByteArr.getvalue()
            #             images = base64.b64encode(imgByteArr)

            #             product_image = product.env['product.image'].sudo().create({
            #                 'name': img,
            #                 'image': images,
            #                 'product_tmpl_id': product.id
            #             })
            #             product.mult_prod_id.create({
            #                 'product_img_id': str(product_image.id),
            #                 'woo_mult_image_id': mult_img['id'],
            #                 'woo_id': res['data']['id']
            #             })
            #         skip_image = skip_image + 1

            # added product variant data when variations id is available
            if res['data']['variations']:

                product_templ_mapper = product.backend_mapping.search(
                    [('backend_id', '=', self.backend.id), ('product_id', '=', product.id)], limit=1)

                if product_templ_mapper and product:
                    vals = {
                        'woo_id': res['data']['id'],
                        'backend_id': self.backend.id,
                        'product_id': product_templ_mapper.product_id.id,
                    }
                    product.backend_mapping.write(vals)
                elif product:
                    vals = {
                        'woo_id': res['data']['id'],
                        'backend_id': self.backend.id,
                        'product_id': product.id,
                    }
                    product.backend_mapping.create(vals)

                product_templ_mapper_2 = product.backend_mapping.search(
                    [('backend_id', '=', self.backend.id), ('product_id', '=', product.id)], limit=1)

                for record in res['data']['variations']:
                    version = "wc/v2"
                    wcapi = API(url=self.backend.location, consumer_key=self.backend.consumer_key,
                                consumer_secret=self.backend.consumer_secret, version=version, wp_api=True)

                    # product_templ_mapper = product.backend_mapping.search([('backend_id', '=', self.backend.id), ('product_id', '=', product.id)], limit=1)

                    # if product_templ_mapper and product:
                    # 	vals={
                    # 		'woo_id' : res['data']['id'],
                    # 		'backend_id' : self.backend.id,
                    # 		'product_id' : product_templ_mapper.product_id.id,
                    # 	}
                    # 	product.backend_mapping.write(vals)
                    # elif product:
                    # 	vals={
                    # 		'woo_id' : res['data']['id'],
                    # 		'backend_id' : self.backend.id,
                    # 		'product_id' : product.id,
                    # 	}
                    # 	product.backend_mapping.create(vals)

                    # product_templ_mapper_2 = product.backend_mapping.search([('backend_id', '=', self.backend.id), ('product_id', '=', product.id)], limit=1)

                    # record_data = wcapi.get("products/{}/variations/{}".format(product.id,record)).json()
                    record_data = wcapi.get(
                        "products/{}/variations/{}".format(product_templ_mapper_2.woo_id, record)).json()



                    record_attr_lst = []
                    for record_attr in record_data['attributes']:
                        record_attr_lst.append(record_attr['option'])

                    for variant_id in product.product_variant_ids:
                        variant_attr_lst = []

                        for product_template_attribute_value_id in variant_id.product_template_attribute_value_ids:
                            variant_attr_lst.append(product_template_attribute_value_id.name)

                        print("variant_attr_lst", variant_attr_lst)
                        print("record_attr_lst", record_attr_lst)

                        if set(variant_attr_lst) == set(record_attr_lst):

                            variant_mapper = variant_id.backend_mapping.search(
                                [('backend_id', '=', backend.id), ('product_id', '=', variant_id.id)])

                            if res['data']['type'] == 'variable':

                                if variant_mapper:
                                    variant_mapper.write({'product_id': variant_id.id, 'backend_id': backend.id,
                                                          'woo_id': record_data['id'],
                                                          'image_id': record_data['image']['id']})

                                    variant_id.woo_id = record_data['id']
                                    variant_id.default_code = record_data['sku']
                                    woo_varient_price.woo_varient_price = record_data['sale_price']

                                    variant_id.weight = record_data['weight']
                                    # variant_id.image_1920 = record_image
                                    variant_id._compute_product_price_extra()

                                    # on_hand_qty added
                                    warehouse = mapper.env['stock.warehouse'].search(
                                        [('company_id', '=',
                                          mapper.env['res.company']._company_default_get('product.template').id)], limit=1
                                    )

                                    if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                        record_data['stock_quantity'] = 0
                                    else:
                                        record_data['stock_quantity'] = record_data['stock_quantity']
                                    update_stock_id = mapper.env['stock.change.product.qty'].create(
                                        {'product_tmpl_id': variant_id.product_tmpl_id,
                                         'lot_id': False,
                                         'product_id': variant_id.id,
                                         'new_quantity': record_data['stock_quantity'],
                                         'location_id': warehouse.lot_stock_id.id,
                                         'product_variant_count': variant_id.product_variant_count})
                                    update_stock_id.change_product_qty()


                                    try:

                                        if record_data['image']['src']:
                                            img = record_data['image']['src'].replace("\\", "")
                                            # response = requests.get(img)

                                            headers = {'User-Agent': 'Mozilla/5.0'}
                                            response = requests.get(img, headers=headers)

                                            image = Image.open(BytesIO(response.content))
                                            imgByteArr = io.BytesIO()
                                            image.save(imgByteArr, format='PNG')
                                            imgByteArr = imgByteArr.getvalue()
                                            variant_images = base64.b64encode(imgByteArr)
                                        else:
                                            variant_images = None

                                        variant_id.image_medium = variant_images
                                        variant_id.env.cr.commit()
                                    except:
                                        pass
                                    break




                                else:
                                    variant_mapper.create({'product_id': variant_id.id, 'backend_id': backend.id,
                                                           'woo_id': record_data['id'],
                                                           'image_id': record_data['image']['id']})

                                    variant_id.woo_id = record_data['id']
                                    variant_id.default_code = record_data['sku']
                                    # variant_id.regular_price = record_data['regular_price']
                                    # variant_id.sale_price = record_data['sale_price']

                                    variant_id.woo_varient_price=record_data['sale_price']
                                    variant_id.weight = record_data['weight']
                                    variant_id._compute_product_price_extra()
                                    # variant_id.image_1920 = record_image

                                    # on_hand_qty added
                                    warehouse = mapper.env['stock.warehouse'].search(
                                        [('company_id', '=',
                                          mapper.env['res.company']._company_default_get('product.template').id)], limit=1
                                    )

                                    if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                        record_data['stock_quantity'] = 0
                                    else:
                                        record_data['stock_quantity'] = record_data['stock_quantity']
                                    update_stock_id = mapper.env['stock.change.product.qty'].create(
                                        {'product_tmpl_id': variant_id.product_tmpl_id,
                                         'lot_id': False,
                                         'product_id': variant_id.id,
                                         'new_quantity': record_data['stock_quantity'],
                                         'location_id': warehouse.lot_stock_id.id,
                                         'product_variant_count': variant_id.product_variant_count})
                                    update_stock_id.change_product_qty()




                                    try:

                                        if record_data['image']['src']:
                                            img = record_data['image']['src'].replace("\\", "")
                                            # response = requests.get(img)

                                            headers = {'User-Agent': 'Mozilla/5.0'}
                                            response = requests.get(img, headers=headers)

                                            image = Image.open(BytesIO(response.content))
                                            imgByteArr = io.BytesIO()
                                            image.save(imgByteArr, format='PNG')
                                            imgByteArr = imgByteArr.getvalue()
                                            variant_images = base64.b64encode(imgByteArr)
                                        else:
                                            variant_images = None

                                        variant_id.image_medium = variant_images
                                        variant_id.env.cr.commit()
                                    except:
                                        pass

                            else:
                                if variant_mapper:
                                    variant_mapper.write({'product_id': variant_id.id, 'backend_id': backend.id,
                                                          'woo_id': record_data['id'],
                                                          'image_id': record_data['image']['id']})

                                    variant_id.woo_id = record_data['id']
                                    variant_id.default_code = record_data['sku']
                                    variant_id.regular_price = record_data['regular_price']
                                    variant_id.sale_price = record_data['sale_price']
                                    variant_id.weight = record_data['weight']
                                    # variant_id.image_1920 = record_image

                                    # on_hand_qty added
                                    warehouse = mapper.env['stock.warehouse'].search(
                                        [('company_id', '=',
                                          mapper.env['res.company']._company_default_get('product.template').id)],
                                        limit=1
                                    )

                                    if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                        record_data['stock_quantity'] = 0
                                    else:
                                        record_data['stock_quantity'] = record_data['stock_quantity']
                                    update_stock_id = mapper.env['stock.change.product.qty'].create(
                                        {'product_tmpl_id': variant_id.product_tmpl_id,
                                         'lot_id': False,
                                         'product_id': variant_id.id,
                                         'new_quantity': record_data['stock_quantity'],
                                         'location_id': warehouse.lot_stock_id.id,
                                         'product_variant_count': variant_id.product_variant_count})
                                    update_stock_id.change_product_qty()
                                    break

                                else:
                                    variant_mapper.create({'product_id': variant_id.id, 'backend_id': backend.id,
                                                           'woo_id': record_data['id'],
                                                           'image_id': record_data['image']['id']})

                                    variant_id.woo_id = record_data['id']
                                    variant_id.default_code = record_data['sku']
                                    variant_id.regular_price = record_data['regular_price']
                                    variant_id.sale_price = record_data['sale_price']
                                    variant_id.weight = record_data['weight']
                                    # variant_id.image_1920 = record_image

                                    # on_hand_qty added
                                    warehouse = mapper.env['stock.warehouse'].search(
                                        [('company_id', '=',
                                          mapper.env['res.company']._company_default_get('product.template').id)],
                                        limit=1
                                    )

                                    if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                        record_data['stock_quantity'] = 0
                                    else:
                                        record_data['stock_quantity'] = record_data['stock_quantity']
                                    update_stock_id = mapper.env['stock.change.product.qty'].create(
                                        {'product_tmpl_id': variant_id.product_tmpl_id,
                                         'lot_id': False,
                                         'product_id': variant_id.id,
                                         'new_quantity': record_data['stock_quantity'],
                                         'location_id': warehouse.lot_stock_id.id,
                                         'product_variant_count': variant_id.product_variant_count})
                                    update_stock_id.change_product_qty()

                                    try:

                                        if record_data['image']['src']:
                                            img = record_data['image']['src'].replace("\\", "")
                                            # response = requests.get(img)

                                            headers = {'User-Agent': 'Mozilla/5.0'}
                                            response = requests.get(img, headers=headers)

                                            image = Image.open(BytesIO(response.content))
                                            imgByteArr = io.BytesIO()
                                            image.save(imgByteArr, format='PNG')
                                            imgByteArr = imgByteArr.getvalue()
                                            variant_images = base64.b64encode(imgByteArr)
                                        else:
                                            variant_images = None

                                        variant_id.image_medium = variant_images
                                    except:
                                        pass

                                break
                        else:
                            variant_attr_lst.clear()

                    if record_attr_lst:
                        record_attr_lst.clear()

            # when no variant_id and variants created(because of attributes) in odoo but not available in wp
            elif product.product_variant_count > 1:
                for variant_id in product.product_variant_ids:
                    variant_id.weight = res['data']['weight']
                    variant_id.default_code = res['data']['sku']

                # on_hand_qty added
                warehouse = mapper.env['stock.warehouse'].search(
                    [('company_id', '=', mapper.env['res.company']._company_default_get('product.template').id)],
                    limit=1
                )

                mapper_product = product
                if mapper_product:
                    if mapper_product.product_variant_ids:
                        for variant_id in mapper_product.product_variant_ids:

                            if not res['data']['stock_quantity'] or res['data']['stock_quantity'] < 0:
                                res['data']['stock_quantity'] = 0
                            else:
                                res['data']['stock_quantity'] = res['data']['stock_quantity']
                            update_stock_id = mapper.env['stock.change.product.qty'].create(
                                {'product_tmpl_id': variant_id.product_tmpl_id,
                                 'lot_id': False,
                                 'product_id': variant_id.id,
                                 'new_quantity': res['data']['stock_quantity'],
                                 'location_id': warehouse.lot_stock_id.id,
                                 'product_variant_count': variant_id.product_variant_count})
                            update_stock_id.change_product_qty()

            else:
                # when no variants id and no attributes
                # on_hand_qty added
                warehouse = mapper.env['stock.warehouse'].search(
                    [('company_id', '=', mapper.env['res.company']._company_default_get('product.template').id)],
                    limit=1
                )

                mapper_product = product
                if mapper_product:
                    if mapper_product.product_variant_ids:
                        for variant_id in mapper_product.product_variant_ids:

                            if not res['data']['stock_quantity'] or res['data']['stock_quantity'] < 0:
                                res['data']['stock_quantity'] = 0
                            else:
                                res['data']['stock_quantity'] = res['data']['stock_quantity']
                            update_stock_id = mapper.env['stock.change.product.qty'].create(
                                {'product_tmpl_id': variant_id.product_tmpl_id,
                                 'lot_id': False,
                                 'product_id': variant_id.id,
                                 'new_quantity': res['data']['stock_quantity'],
                                 'location_id': warehouse.lot_stock_id.id,
                                 'product_variant_count': variant_id.product_variant_count})
                            update_stock_id.change_product_qty()

            return product

    def get_tags(self, wp_tags, mapper, bkend_id):
        """ get all tags of product from wp"""
        tag_list = []
        for wp_tag in wp_tags:
            product_tag = mapper.env['product.product.tag'].search([('backend_id', '=', bkend_id.id),
                                                                    ('name', '=', wp_tag['name'])])
            if product_tag:
                tag_list.append(product_tag.id)
                product_tag.write({'slug': wp_tag['slug']})
            else:
                vals = {
                    'name': wp_tag['name'],
                    'slug': wp_tag['slug'],
                    "backend_id": bkend_id.id,
                }
                product_tag = mapper.env['product.product.tag'].create(vals)
                tag_list.append(product_tag.id)
            if product_tag:
                tag_mapper = product_tag.backend_mapping.search(
                    [('backend_id', '=', bkend_id.id), ('product_tag_id', '=', product_tag.id)], limit=1)

            if tag_mapper:
                tag_mapper.write({'product_tag_id': product_tag.id, 'backend_id': bkend_id.id, 'woo_id': wp_tag['id']})
            else:
                product_tag.backend_mapping.create(
                    {'product_tag_id': product_tag.id, 'backend_id': bkend_id.id, 'woo_id': wp_tag['id']})

        return tag_list

    def write_product(self, backend, mapper, res):
        bkend_id = mapper.backend_id.search([('id', '=', backend.id)])

        if res['data']['tags']:
            wp_tags = res['data']['tags']
            wp_tag_ids = self.get_tags(wp_tags, mapper, bkend_id)
        else:
            wp_tag_ids = []

        if res['data']['images']:
            img = res['data']['images'][0]['src'].replace("\\", "")
            # response = requests.get(img)

            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(img, headers=headers)

            image = Image.open(BytesIO(response.content))
            imgByteArr = io.BytesIO()
            image.save(imgByteArr, format='PNG')
            imgByteArr = imgByteArr.getvalue()
            images = base64.b64encode(imgByteArr)
        else:
            images = None
        try:

            if res['data']['categories']:
                woo_category = res['data']['categories'][0]['name']

                # if "&amp;" in woo_category:
                # 	woo_category = woo_category.replace('&amp;','&')

                woo_slug = res['data']['categories'][0]['slug']
                categ_id = mapper.env['product.category'].search([('name', '=', woo_category), ('backend_id', '=', backend.id), ('slug', '=', woo_slug)], limit=1).id
                # categ_id = mapper.env['product.category'].search(
                #     [('name', '=', woo_category) and ('slug', '=', woo_slug)]).id
            if not categ_id:
                vals = {
                    "name": res['data']['categories'][0]['name'],
                    "slug": res['data']['categories'][0]['slug'],
                    "backend_id": bkend_id.id,
                    "woo_id": res['data']['categories'][0]['id']

                }
                create_categ_id = mapper.env['product.category'].create(vals)
            if res['data']['categories']:
                woo_category = res['data']['categories'][0]['name']
                woo_slug = res['data']['categories'][0]['slug']
                categ_id = mapper.env['product.category'].search([('name', '=', woo_category), ('backend_id', '=', backend.id), ('slug', '=', woo_slug)], limit=1).id
                # categ_id = mapper.env['product.category'].search(
                #     [('name', '=', woo_category) and ('slug', '=', woo_slug)]).id

        except:
            pass

        if res['data']['attributes']:
            mapper.product_id.attribute_line_ids.unlink()
            attributes_value = []
            for attribute in res['data']['attributes']:
                attribute_id = mapper.env['product.attribute'].search([('name', '=', attribute['name'])]).id
                attribute_value_ids = []

                if not attribute_id:
                    # create attribute_id
                    attribute_create = mapper.env['product.attribute'].create({'name': attribute['name']})
                    attribute_id = attribute_create.id

                for attribute_val in attribute['options']:
                    attribute_value_id = ''
                    # attribute_value_id = mapper.env['product.attribute.value'].search([('name','=', attribute_val)]).id

                    # attribute_value_id = mapper.env['product.attribute.value'].search([('name','=', attribute_val) and ('attribute_id','=', attribute_id)]).id

                    product_attribute_value_ids = mapper.env['product.attribute.value'].search(
                        [('name', '=', attribute_val)])
                    for product_attribute_value_id in product_attribute_value_ids:
                        if product_attribute_value_id.attribute_id.id == attribute_id:
                            attribute_value_id = product_attribute_value_id.id
                            break
                        else:
                            attribute_value_id = False

                    if not attribute_value_id:
                        # create attribute_value
                        attribute_value_create = mapper.env['product.attribute.value'].create(
                            {'name': attribute_val, 'attribute_id': attribute_id, 'sequence': 1})
                        attribute_value_id = attribute_value_create.id
                    attribute_value_ids.append(attribute_value_id)
                attributes_value.append(
                    (0, 0, {'attribute_id': attribute_id, 'value_ids': [(6, 0, attribute_value_ids)]}))


        else:
            attributes_value = []

        if res['data']['type'] == 'variable':
            vals = {

                'list_price': 0.0,
                'type': 'product',
                'name': res['data']['name'],
                'categ_id': categ_id,
                # 'qty_available' : res['data']['stock_quantity'],
                'backend_id': bkend_id.id,
                'tag_ids': [[6, 0, wp_tag_ids]],
                'attribute_line_ids': attributes_value,
                'image_medium': images,
                'website_size_x': res['data']['dimensions']['length'],
                'website_size_y': res['data']['dimensions']['width'],
                'website_size_z': res['data']['dimensions']['height'],
                'weight': res['data']['weight'],
                'default_code': res['data']['sku'],
                'short_description': re.sub(re.compile('<.*?>'), '', res['data']['short_description']),
                'description': re.sub(re.compile('<.*?>'), '', res['data']['description']),

            }
        else:

            vals = {
                'sale_price': res['data']['price'],
                'regular_price': res['data']['regular_price'],
                'list_price': res['data']['price'],
                'type': 'product',
                'name': res['data']['name'],
                'categ_id': categ_id,
                # 'qty_available' : res['data']['stock_quantity'],
                'attribute_line_ids': attributes_value,
                'backend_id': bkend_id.id,
                'tag_ids': [[6, 0, wp_tag_ids]],
                'image_medium': images,
                'website_size_x': res['data']['dimensions']['length'],
                'website_size_y': res['data']['dimensions']['width'],
                'website_size_z': res['data']['dimensions']['height'],
                'short_description': re.sub(re.compile('<.*?>'), '', res['data']['short_description']),
                'description': re.sub(re.compile('<.*?>'), '', res['data']['description']),

            }

        mapper.product_id.write(vals)
        # added product variant data when variations id is available
        if res['data']['variations']:
            
            for record in res['data']['variations']:
                version = "wc/v2"
                wcapi = API(url=self.backend.location, consumer_key=self.backend.consumer_key,
                            consumer_secret=self.backend.consumer_secret, version=version, wp_api=True)

                # record_data = wcapi.get("products/{}/variations/{}".format(mapper.product_id.id,record)).json()
                record_data = wcapi.get("products/{}/variations/{}".format(mapper.woo_id, record)).json()


                record_attr_lst = []
                for record_attr in record_data['attributes']:
                    record_attr_lst.append(record_attr['option'])

                for variant_id in mapper.product_id.product_variant_ids:
                    variant_attr_lst = []

                    for product_template_attribute_value_id in variant_id.product_template_attribute_value_ids:
                        variant_attr_lst.append(product_template_attribute_value_id.name)

                    if set(variant_attr_lst) == set(record_attr_lst):

                        variant_mapper = variant_id.backend_mapping.search(
                            [('backend_id', '=', backend.id), ('product_id', '=', variant_id.id)])

                        if res['data']['type'] == 'variable':
                            if variant_mapper:
                                variant_mapper.write({'product_id': variant_id.id, 'backend_id': backend.id,
                                                      'woo_id': record_data['id'], 'image_id': record_data['image']['id']})

                                variant_id.woo_id = record_data['id']
                                variant_id.default_code = record_data['sku']
                                # variant_id.regular_price = record_data['regular_price']
                                # variant_id.sale_price = record_data['sale_price']
                                variant_id.woo_varient_price = record_data['sale_price']
                                variant_id._compute_product_price_extra()
                                variant_id.weight = record_data['weight']
                                # variant_id.image_1920 = record_image

                                # on_hand_qty added
                                warehouse = mapper.env['stock.warehouse'].search(
                                    [('company_id', '=',
                                      mapper.env['res.company']._company_default_get('product.template').id)], limit=1
                                )


                                if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                    record_data['stock_quantity'] = 0
                                else:
                                    record_data['stock_quantity'] = record_data['stock_quantity']
                                update_stock_id = mapper.env['stock.change.product.qty'].create(
                                    {'product_tmpl_id': variant_id.product_tmpl_id,
                                     'lot_id': False,
                                     'product_id': variant_id.id,
                                     'new_quantity': record_data['stock_quantity'],
                                     'location_id': warehouse.lot_stock_id.id,
                                     'product_variant_count': variant_id.product_variant_count})
                                update_stock_id.change_product_qty()


                                try:

                                    if record_data['image']['src']:
                                        img = record_data['image']['src'].replace("\\", "")
                                        # response = requests.get(img)

                                        headers = {'User-Agent': 'Mozilla/5.0'}
                                        response = requests.get(img, headers=headers)

                                        image = Image.open(BytesIO(response.content))
                                        imgByteArr = io.BytesIO()
                                        image.save(imgByteArr, format='PNG')
                                        imgByteArr = imgByteArr.getvalue()
                                        variant_images = base64.b64encode(imgByteArr)
                                    else:
                                        variant_images = None

                                    variant_id.image_medium = variant_images
                                except:
                                    pass

                                break

                            else:
                                variant_mapper.create({'product_id': variant_id.id, 'backend_id': backend.id,
                                                       'woo_id': record_data['id'], 'image_id': record_data['image']['id']})

                                variant_id.woo_id = record_data['id']
                                variant_id.default_code = record_data['sku']
                                variant_id.regular_price = record_data['regular_price']
                                # variant_id.sale_price = record_data['sale_price']
                                # variant_id.weight = record_data['weight']
                                # variant_id.image_1920 = record_image

                                variant_id.woo_varient_price = record_data['sale_price']
                                variant_id._compute_product_price_extra()

                                # on_hand_qty added
                                warehouse = mapper.env['stock.warehouse'].search(
                                    [('company_id', '=',
                                      mapper.env['res.company']._company_default_get('product.template').id)], limit=1
                                )


                                if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                    record_data['stock_quantity'] = 0
                                else:
                                    record_data['stock_quantity'] = record_data['stock_quantity']
                                update_stock_id = mapper.env['stock.change.product.qty'].create(
                                    {'product_tmpl_id': variant_id.product_tmpl_id,
                                     'lot_id': False,
                                     'product_id': variant_id.id,
                                     'new_quantity': record_data['stock_quantity'],
                                     'location_id': warehouse.lot_stock_id.id,
                                     'product_variant_count': variant_id.product_variant_count})
                                update_stock_id.change_product_qty()


                                try:

                                    if record_data['image']['src']:
                                        img = record_data['image']['src'].replace("\\", "")
                                        # response = requests.get(img)

                                        headers = {'User-Agent': 'Mozilla/5.0'}
                                        response = requests.get(img, headers=headers)

                                        image = Image.open(BytesIO(response.content))
                                        imgByteArr = io.BytesIO()
                                        image.save(imgByteArr, format='PNG')
                                        imgByteArr = imgByteArr.getvalue()
                                        variant_images = base64.b64encode(imgByteArr)
                                    else:
                                        variant_images = None

                                    variant_id.image_medium = images
                                except:
                                    pass

                                break
                        else:
                            if variant_mapper:
                                variant_mapper.write({'product_id': variant_id.id, 'backend_id': backend.id,
                                                      'woo_id': record_data['id'],
                                                      'image_id': record_data['image']['id']})

                                variant_id.woo_id = record_data['id']
                                variant_id.default_code = record_data['sku']
                                variant_id.regular_price = record_data['regular_price']
                                variant_id.sale_price = record_data['sale_price']
                                variant_id.weight = record_data['weight']
                                # variant_id.image_1920 = record_image

                                # on_hand_qty added
                                warehouse = mapper.env['stock.warehouse'].search(
                                    [('company_id', '=',
                                      mapper.env['res.company']._company_default_get('product.template').id)], limit=1
                                )

                                if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                    record_data['stock_quantity'] = 0
                                else:
                                    record_data['stock_quantity'] = record_data['stock_quantity']
                                update_stock_id = mapper.env['stock.change.product.qty'].create(
                                    {'product_tmpl_id': variant_id.product_tmpl_id,
                                     'lot_id': False,
                                     'product_id': variant_id.id,
                                     'new_quantity': record_data['stock_quantity'],
                                     'location_id': warehouse.lot_stock_id.id,
                                     'product_variant_count': variant_id.product_variant_count})
                                update_stock_id.change_product_qty()
                                break

                            else:
                                variant_mapper.create({'product_id': variant_id.id, 'backend_id': backend.id,
                                                       'woo_id': record_data['id'],
                                                       'image_id': record_data['image']['id']})

                                variant_id.woo_id = record_data['id']
                                variant_id.default_code = record_data['sku']
                                variant_id.regular_price = record_data['regular_price']
                                variant_id.sale_price = record_data['sale_price']
                                variant_id.weight = record_data['weight']
                                # variant_id.image_1920 = record_image

                                # on_hand_qty added
                                warehouse = mapper.env['stock.warehouse'].search(
                                    [('company_id', '=',
                                      mapper.env['res.company']._company_default_get('product.template').id)], limit=1
                                )

                                if not record_data['stock_quantity'] or record_data['stock_quantity'] < 0:
                                    record_data['stock_quantity'] = 0
                                else:
                                    record_data['stock_quantity'] = record_data['stock_quantity']
                                update_stock_id = mapper.env['stock.change.product.qty'].create(
                                    {'product_tmpl_id': variant_id.product_tmpl_id,
                                     'lot_id': False,
                                     'product_id': variant_id.id,
                                     'new_quantity': record_data['stock_quantity'],
                                     'location_id': warehouse.lot_stock_id.id,
                                     'product_variant_count': variant_id.product_variant_count})
                                update_stock_id.change_product_qty()

                                try:

                                    if record_data['image']['src']:
                                        img = res['data']['images'][0]['src'].replace("\\", "")
                                        # response = requests.get(img)

                                        headers = {'User-Agent': 'Mozilla/5.0'}
                                        response = requests.get(img, headers=headers)

                                        image = Image.open(BytesIO(response.content))
                                        imgByteArr = io.BytesIO()
                                        image.save(imgByteArr, format='PNG')
                                        imgByteArr = imgByteArr.getvalue()
                                        variant_images = base64.b64encode(imgByteArr)
                                    else:
                                        variant_images = None

                                    variant_id.image_1920 = images
                                except:
                                    pass

                                break
                    else:
                        variant_attr_lst.clear()

                if record_attr_lst:
                    record_attr_lst.clear()

        # when no variant_id and variants created(because of attributes) in odoo but not available in wp
        elif mapper.product_id.product_variant_count > 1:
            for variant_id in mapper.product_id.product_variant_ids:
                variant_id.weight = res['data']['weight']
                variant_id.default_code = res['data']['sku']

            # on_hand_qty added
            warehouse = mapper.env['stock.warehouse'].search(
                [('company_id', '=', mapper.env['res.company']._company_default_get('product.template').id)], limit=1
            )
            
            # stock_quant = mapper.env['stock.quant']
            # mapper_product = mapper.product_id
            # if mapper_product:
            #     if mapper_product.product_variant_ids:
            #         for variant_id in mapper_product.product_variant_ids:
            #             stock_quant.with_context(inventory_mode=True).create({
            #                 'product_id': variant_id.id,
            #                 'location_id': warehouse.lot_stock_id.id,
            #                 'quantity': res['data']['stock_quantity'],
            #             })
            mapper_product = mapper.product_id
            if mapper_product:
                if mapper_product.product_variant_ids:
                    for variant_id in mapper_product.product_variant_ids:
                        # result = {
                        #     'product_qty': res['data']['stock_quantity'],
                        #     'location_id': warehouse.lot_stock_id.id,
                        #     'product_id': variant_id.id,
                        #     'product_uom_id': variant_id.uom_id.id,
                        #     'theoretical_qty': res['data']['stock_quantity'],
                        # }
                        # Inventory = mapper.env['stock.inventory']
                        # inventory = Inventory.create({
                        #     # 'name': _('INV: %s') % tools.ustr(wizard.product_id.display_name),
                        #     'name': variant_id.name,
                        #     'filter': 'product',
                        #     'product_id': variant_id.id,
                        #     'location_id': warehouse.lot_stock_id.id,
                        #     'line_ids': [(0, 0, result)],
                        # })
                        if not res['data']['stock_quantity'] or res['data']['stock_quantity'] < 0:
                            res['data']['stock_quantity'] = 0
                        else:
                            res['data']['stock_quantity'] = res['data']['stock_quantity']
                        update_stock_id = mapper.env['stock.change.product.qty'].create(
                            {'product_tmpl_id': variant_id.product_tmpl_id,
                             'lot_id': False,
                             'product_id': variant_id.id,
                             'new_quantity': res['data']['stock_quantity'],
                             'location_id': warehouse.lot_stock_id.id,
                             'product_variant_count': variant_id.product_variant_count})
                        update_stock_id.change_product_qty()

        else:
            # when no variants id and no attributes
            mapper.product_id.weight = res['data']['weight']
            mapper.product_id.default_code = res['data']['sku']
            # on_hand_qty added
            warehouse = mapper.env['stock.warehouse'].search(
                [('company_id', '=', mapper.env['res.company']._company_default_get('product.template').id)], limit=1
            )
            
            # stock_quant = mapper.env['stock.quant']
            # mapper_product = mapper.product_id
            # if mapper_product:
            #     if mapper_product.product_variant_ids:
            #         for variant_id in mapper_product.product_variant_ids:
            #             stock_quant.with_context(inventory_mode=True).sudo().create({
            #                 'product_id': variant_id.id,
            #                 'location_id': warehouse.lot_stock_id.id,
            #                 'quantity': res['data']['stock_quantity'],
            #             })
            mapper_product = mapper.product_id
            if mapper_product:
                if mapper_product.product_variant_ids:
                    for variant_id in mapper_product.product_variant_ids:
                        # result = {
                        #     'product_qty': res['data']['stock_quantity'],
                        #     'location_id': warehouse.lot_stock_id.id,
                        #     'product_id': variant_id.id,
                        #     'product_uom_id': variant_id.uom_id.id,
                        #     'theoretical_qty': res['data']['stock_quantity'],
                        # }
                        # Inventory = mapper.env['stock.inventory']
                        # inventory = Inventory.create({
                        #     # 'name': _('INV: %s') % tools.ustr(wizard.product_id.display_name),
                        #     'name': variant_id.name,
                        #     'filter': 'product',
                        #     'product_id': variant_id.id,
                        #     'location_id': warehouse.lot_stock_id.id,
                        #     'line_ids': [(0, 0, result)],
                        # })
                        if not res['data']['stock_quantity'] or res['data']['stock_quantity'] < 0:
                            res['data']['stock_quantity'] = 0
                        else:
                            res['data']['stock_quantity'] = res['data']['stock_quantity']
                        update_stock_id = mapper.env['stock.change.product.qty'].create(
                            {'product_tmpl_id': variant_id.product_tmpl_id,
                             'lot_id': False,
                             'product_id': variant_id.id,
                             'new_quantity': res['data']['stock_quantity'],
                             'location_id': warehouse.lot_stock_id.id,
                             'product_variant_count': variant_id.product_variant_count})
                        update_stock_id.change_product_qty()
