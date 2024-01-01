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

from odoo import models, api, fields
import uuid
import logging
from io import StringIO
from odoo import models, api, fields

PENDING = 'pending'
ENQUEUED = 'enqueued'
DONE = 'done'
STARTED = 'started'
FAILED = 'failed'


STATES = [(PENDING, 'Pending'),
          (ENQUEUED, 'Enqueued'),
          (STARTED, 'Started'),
          (DONE, 'Done'),
          (FAILED, 'Failed')]

DEFAULT_PRIORITY = 10  # used by the PriorityQueue to sort the jobs
DEFAULT_MAX_RETRIES = 5
RETRY_INTERVAL = 10 * 60  # seconds

_logger = logging.getLogger(__name__)


class wp_jobs(models.Model):
    _name = "wordpress.jobs"
    _description = 'WooCommerce Backend Jobs'

    name = fields.Char(string='Name')
    state = fields.Selection(STATES,  string='State',
                             readonly=False,
                             required=True,
                             index=True)
    backend_id = fields.Integer(string='backend id', readonly=False)
    module = fields.Char(string='module', readonly=False)
    module_object_id = fields.Integer(string='module object id',
                                      readonly=False)
    api_data = fields.Char(string='API', readonly=False)
    request = fields.Text(string='Post data', readonly=False)
    response = fields.Text(string='Response', readonly=False)


    # @api.multi
    def resend_data(self):
        #check import export type
        #call respected methods
        backend = self.env['wordpress.configure'].search(
            [('id', '=', self.backend_id)])
        obj = self.env[str(self.module)].search(
            [('id', '=', self.module_object_id)])
        if 'Export' in self.name:
            obj.export(backend)
        elif 'Import' in self.name:
            obj.single_importer(backend,obj.id,False)