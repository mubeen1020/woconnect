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

import logging
from ..model.api import API
from datetime import datetime
from datetime import timedelta
from . backend_adapter import WpImportExport

_logger = logging.getLogger(__name__)

class WpTaxExport(WpImportExport):

    def get_api_method(self, method, args):
        """ get api for tax and values"""
        api_method = None
        if method == 'tax':
            if not args[0]:
                api_method = 'taxes'
            else:
                api_method = 'taxes/' + str(args[0])
        elif method == 'tax_class':
            if not args[0]:
                api_method = 'taxes/classes'
            else:
                api_method = 'taxes/classes/' + str(args[0])
        return api_method

    def export_tax(self, method, arguments):
        """ Export product tax data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        result_dict = {"country": str(arguments[1].count_id.code),
                       "state": str(arguments[1].state_id.code),
                       "postcode": str(arguments[1].postcode),
                       "city": str(arguments[1].city),
                       "rate": str(arguments[1].amount),
                       "name": arguments[1].name,
                       "priority": arguments[1].priority,
                       "compound": arguments[1].compound,
                       "shipping": arguments[1].shipping,
                       "order": arguments[1].order,
                       "class": "standard",
                       }
        res = self.export(method, result_dict, arguments)
        return {'status': res.status_code, 'data': res.json()}

    def export_tax_class(self, method, arguments):
        """ Export product tax data"""
        _logger.debug("Start calling Woocommerce api %s", method)
        result_dict = {"name": arguments[1].name}
        if arguments[1].slug:
            result_dict.update({'slug': arguments[1].slug or None})
        res = self.export(method, result_dict, arguments)
        return {'status': res.status_code, 'data': res.json()}