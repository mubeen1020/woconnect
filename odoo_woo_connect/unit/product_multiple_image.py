import logging
import time
# import xmlrpclib
from collections import defaultdict
# from odoo.addons.queue_job.job import job
import base64
from odoo import models, fields, api, _
from ..unit.customer_exporter import WpCustomerExport
from ..unit.customer_importer import WpCustomerImport
from odoo.exceptions import Warning
from odoo.exceptions import Warning,UserError
_logger = logging.getLogger(__name__)

class Multiple_images(models.Model):
    _name='wordpress.odoo.multi.product.image'

    # woo_mult_prod_mapping = fields.One2many('product.template','mult_prod_id',string='Multiple Product ID',
    #                                       readonly=False,
    #                                       required=False)
    product_img_id = fields.Char('odoo Product image_id')
    woo_id = fields.Char('Woo Product id')

    woo_mult_image_id = fields.Char('Multiple Image id')