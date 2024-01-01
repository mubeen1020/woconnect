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
from ..model.api import API
from datetime import datetime
from datetime import timedelta
from ..unit.backend_adapter import WpImportExport

_logger = logging.getLogger(__name__)


class WpProductVariationExport(WpImportExport):

    def get_api_method(self, method, args):
        """ get api for product and values"""
        api_method = None
        if method == 'variation':
            if not args[2]:
                api_method = 'products/' + str(args[0]) + '/variations/details'
            else:
                api_method = 'products/' + str(args[0]) + '/variations/details/' + str(args[2])

        return api_method

    def get_images(self, product):
        """ get all categories of product """
        product_mapper = product.backend_mapping.search([('backend_id', '=', self.backend.id),('product_id', '=', product.id)], limit=1)
        if product_mapper:
            product_image_id = product_mapper.image_id
        else:
            product_image_id = 0

        if product.image :
            images = [{"src": product.image or False,
                       "name": product.name or None,
                       "position": 0,
                       'id': product_image_id or 0}]
        else :
            images = []
            
        return images
    def get_attributes(self, product):
        """ get all attributes of product """
        attributes = []
        for attr in product.attribute_value_ids:
            attributes_value = []
            mapper = attr.attribute_id.backend_mapping.search(
                [('backend_id', '=', self.backend.id), ('attribute_id', '=', attr.attribute_id.id)], limit=1)
            if not mapper.woo_id:
                attr.attribute_id.export(self.backend)
                mapper = attr.attribute_id.backend_mapping.search(
                [('backend_id', '=', self.backend.id), ('attribute_id', '=', attr.attribute_id.id)], limit=1)
            val_mapper = attr.backend_mapping.search(
                [('backend_id', '=', self.backend.id), ('attribute_value_id', '=', attr.id)], limit=1)
            if not val_mapper.woo_id:
                attr.export(self.backend)
            attributes.append({
                "id": mapper.woo_id or None,
                "name": attr.attribute_id.name or None,
                'option': attr.name or None,
                "visible": attr.attribute_id.visible,
                "variation": attr.attribute_id.create_variant,
            })
        return attributes

    def export_product_variant(self, method, arguments):
        """ Export product data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        templ=arguments[1].env['product.template'].search([('id','=',arguments[1].product_tmpl_id.id)])
        sale_price = str(arguments[1].offer_price)
        if sale_price == '0.0':
            sale_price=None

        if templ.regular_price:
            regular_price = arguments[1].price_extra + templ.regular_price
        else:
            regular_price = ''
        
        start = None
        end = None
        if arguments[1].schedule_sale1:
            start = arguments[1].schedule_date_start1
            end = arguments[1].schedule_date_end1

        result_dict = {
            'sku': arguments[1].default_code or None,
            'weight': str(arguments[1].weight) or None,
            'managing_stock': True,
            'stock_quantity': arguments[1].qty_available or None,
            "attributes": self.get_attributes(arguments[1]),
            'images': self.get_images(arguments[1]),
            'dimensions': {'length': str(arguments[1].website_size_x) or "",
                           'width': str(arguments[1].website_size_y) or "",
                           'height': str(arguments[1].website_size_z) or "",
                           },
            'regular_price': str(regular_price) or None,  
            'price': str(regular_price) or None,
            'sale_price': sale_price or None,
            'date_on_sale_from': start or None,
            'date_on_sale_to': end or None,
        }
        _logger.info("Odoo Product Export Data: %s",result_dict)
        res = self.export(method, result_dict, arguments)
        if res:
            res_dict = res.json()
        else:
            res_dict = None
        return {'status': res.status_code, 'data': res_dict or {}}
