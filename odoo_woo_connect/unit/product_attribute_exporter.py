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


class WpProductAttributeExport(WpImportExport):

    def get_api_method(self, method, args):
        """ get api for attribute and values"""
        api_method = None
        if method == 'attribute':
            if not args[0]:
                api_method = 'products/attributes'
            else:
                api_method = 'products/attributes/' + str(args[0])
        elif method == 'attribute_value':
            if not args[0]:
                api_method = 'products/attributes/' + \
                    str(args[2].woo_id) + '/terms'
            else:
                api_method = 'products/attributes/' + \
                    str(args[2].woo_id) + '/terms/' + str(args[0])
        return api_method

    def export_product_attribute(self, method, arguments):
        """ Export product attribute data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        if arguments[1].create_variant:
            if arguments[1].create_variant=='always':
            # if arguments[1].create_variant == True:
                create_variant=True
            else:
                create_variant=False    

        result_dict = {"name": arguments[1].name,
                       "type": "select",
                       "order_by": "menu_order",
                       "has_archives": True,
                       "variation":create_variant
                       }
        r = self.export(method, result_dict, arguments)
        return {'status': r.status_code, 'data': r.json()}

    def export_product_attribute_value(self, method, arguments):
        """ Export product attribute value data"""
        _logger.debug("Start calling Woocommerce api %s", method)

        result_dict = {"name": arguments[1].name}
        r = self.export(method, result_dict, arguments)
        return {'status': r.status_code, 'data': r.json()}
