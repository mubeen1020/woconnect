
# -*- coding: utf-8 -*-
#
#
#    TechSpawn Solutions Pvt. Ltd.
#    Copyright (C) 2016-TODAY TechSpawn(<http://www.techspawn.com>).
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
#    authors : Vinay Bhawsar, Saumil Thaker, Samir Panda


from odoo import models, fields, tools, api


class Shipping_address(models.Model):

    """ Models for woocommerce shipping address """
    _name = 'res.partner.shipping.address'
    _description = 'shipping address'

    ship_first_name = fields.Char('First Name', readonly=False)
    ship_last_name = fields.Char('Last Name', readonly=False)
    ship_email = fields.Char('Shipping Email', readonly=False)
    ship_phone = fields.Char(string='Phone Number')
    ship_address1 = fields.Char('Address 1 ', readonly=False)
    ship_address2 = fields.Char('Address 2 ', readonly=False)
    ship_city = fields.Char('City ', readonly=False)
    ship_state = fields.Many2one(comodel_name='res.country.state',
                                 string='State',
                                 ondelete='restrict')
    ship_country = fields.Many2one(comodel_name='res.country',
                                   string='Country',
                                   ondelete='restrict')
    ship_zip = fields.Char('Zip', size=24, change_default=True)
    default = fields.Boolean(string='Default Address')
    partner_id = fields.Many2one(comodel_name='res.partner',
                                 ondelete='cascade',
                                 string='Owner')

    @api.model
    def create(self, vals):
        """
        This function will be executed on every create in woo.shipping
        """
        return super(Shipping_address, self).create(vals)

    # @api.multi
    def write(self, vals):
        """
        This function will be executed on every update made in woo.shipping
        """
        return super(Shipping_address, self).write(vals)

    # @api.multi
    def unlink(self):
        """
        This function will be executed whenever woo.shipping is deleted
        """
        return super(Shipping_address, self).unlink()
