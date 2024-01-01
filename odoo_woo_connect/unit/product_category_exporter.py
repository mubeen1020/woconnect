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
from ..model.api import API
from datetime import datetime
from datetime import timedelta
from . backend_adapter import WpImportExport
_logger = logging.getLogger(__name__)


class WpCategoryExport(WpImportExport):

    def get_api_method(self, method, args):
        """ get api for category and values"""
        api_method = None
        if method == 'category':
            if not args[0]:
                api_method = 'products/categories'
            else:
                api_method = 'products/categories/' + str(args[0])
        return api_method

    def export_product_category(self, method, arguments):
        """ Export product category data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        if arguments[1].parent_id:
            mapper = arguments[1].parent_id.backend_mapping.search(
                [('backend_id', '=', self.backend.id), ('category_id', '=', arguments[1].parent_id.id)])
            parent = mapper.woo_id or None
            if not parent:
                result_dict = {
                    'name': arguments[1].parent_id.name,
                }
                res = self.export(
                    method, result_dict,[None, arguments[1].parent_id])
                if res.status_code == 201 or res.status_code == 200:
                    data=res.json()
                    arguments[1].parent_id.write({'slug': data['slug']})
                    arguments[1].parent_id.write({'woo_id': data['id']})
                    if mapper:
                        mapper.write({'category_id': arguments[1].parent_id.id, 'backend_id': self.backend.id, 'woo_id': data['id']})
                    else :
                        mapper.create({'category_id': arguments[
                                      1].parent_id.id, 'backend_id': self.backend.id, 'woo_id': data['id']})

                    parent =  arguments[1].parent_id.woo_id
        else:
            parent = 0
            
        result_dict = {
            'name': arguments[1].name,
        }
        if parent != 0:
        
            result_dict.update({'parent': parent, })

        if arguments[1].slug:
            result_dict.update({'slug': arguments[1].slug or None})
        res = self.export(method, result_dict, arguments)
        return {'status': res.status_code, 'data': res.json()}
