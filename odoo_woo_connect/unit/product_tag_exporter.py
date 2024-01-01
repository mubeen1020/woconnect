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


class WpProductTagExport(WpImportExport):

    def get_api_method(self, method, args):
        """ get api for tag and values"""
        api_method = None
        if method == 'tag':
            if not args[0]:
                api_method = 'products/tags'
            else:
                api_method = 'products/tags/' + str(args[0])
        return api_method

    def export_product_tag(self, method, arguments):
        """ Export product tag data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        slug = arguments[1].slug or None
        result_dict = {"name": arguments[1].name or None}
        if slug != None:
            result_dict["slug"] = arguments[1].slug
        if arguments[1].desc:
            result_dict['description'] = arguments[1].desc or None

        r = self.export(method, result_dict, arguments)


        return {'status': r.status_code, 'data': r.json()}
