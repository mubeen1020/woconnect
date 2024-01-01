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

from ..model.api import API
import requests

from PIL import Image
import requests
from io import BytesIO
import io
import base64
import json
from odoo import models, fields, tools, api

from base64 import b64encode
from json import dumps


import logging
from ..model.api import API
from datetime import datetime
from datetime import timedelta
from . backend_adapter import WpImportExport
import base64
_logger = logging.getLogger(__name__)
from odoo import http, tools
import hashlib
import io
import os
from odoo.http import request
# from wordpress_xmlrpc import Client, WordPressPost
# from wordpress_xmlrpc.compat import xmlrpc_client
# from wordpress_xmlrpc.methods import media, posts

class WpProductExport(WpImportExport):

	def get_api_method(self, method, args):
		""" get api for product and values"""

		api_method = None
		if method == 'products':
			if not args[0]:
				api_method = 'products'
			else:
				api_method = 'products/' + str(args[0])
		return api_method

	def get_attributes(self, product):
		
		""" get all attributes of product """
		attributes = []
		for attr in product.attribute_line_ids:
			attributes_value = []
			mapper = attr.attribute_id.backend_mapping.search(
				[('backend_id', '=', self.backend.id), ('attribute_id', '=', attr.attribute_id.id)], limit=1)
			if not mapper.woo_id:
				attr.attribute_id.export_product_attribute(self.backend)
				mapper = attr.attribute_id.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('attribute_id', '=', attr.attribute_id.id)], limit=1)
			if attr.attribute_id.create_variant:
				if attr.attribute_id.create_variant=='always':
				# if attr.attribute_id.create_variant == True:
					create_variant=True
				else:
					create_variant=False  

			for value in attr.value_ids:
				val_mapper = value.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('attribute_value_id', '=', value.id)], limit=1)
				if not val_mapper.woo_id:
					value.export_product_attribute_value(self.backend)
				attributes_value.append(value.name)		
			attributes.append({
				"id": mapper.woo_id or 0,
				"name": attr.attribute_id.name or None,
				"visible": True,
				"variation": create_variant,
				"options": attributes_value,
			})
		return attributes
	


	def get_category(self, product):
		""" get all categories of product """
		categ_id = []
		if product.categ_id:
			for categ in product.categ_id:
				mapper = categ.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('category_id', '=', categ.id)], limit=1)
				if mapper.woo_id:
					categ_id.append({'id': mapper.woo_id or None})
				else:
					categ.export_product_category(self.backend)
					mapper = categ.backend_mapping.search(
						[('backend_id', '=', self.backend.id), ('category_id', '=', categ.id)], limit=1)
					categ_id.append({'id': mapper.woo_id or None})

				# if categ_id is none then get id 				
				if categ_id[0]['id'] == None:
					# version = "wc/v2"
					# wcapi = API(url=self.backend.location,consumer_key=self.backend.consumer_key,consumer_secret=self.backend.consumer_secret,version=version,wp_api=True)
					# woo_all_category = wcapi.get("products/categories").json()

					# for woo_category in woo_all_category:
					# 	if woo_category['name'] == categ.name:
					# 		categ_id[0]['id'] = woo_category['id']
					# 		break
					res = categ.export_product_category(self.backend)
					if res:
						categ_id[0]['id'] = res						


				categ_parent = categ.parent_id
				while categ_parent.parent_id:
					mapper_parent = categ.backend_mapping.search(
						[('backend_id', '=', self.backend.id), ('category_id', '=', categ_parent.id)], limit=1)
					if mapper_parent.woo_id:
						categ_id.append({'parent_id': mapper_parent.woo_id or None})
					else:
						categ_parent.export_product_category(self.backend)
						mapper_parent = categ.backend_mapping.search(
							[('backend_id', '=', self.backend.id), ('category_id', '=',  categ_parent.id)], limit=1)
						categ_id.append({'parent_id': mapper_parent.woo_id or None})
					categ_parent = categ_parent.parent_id
		return categ_id

	# def get_tag(self, product):
	# 	""" get all categories of product """
	# 	tag_id = []
	# 	if product.tag_ids:
	# 		for tag in product.tag_ids:
	# 			mapper = tag.backend_mapping.search(
	# 				[('backend_id', '=', self.backend.id), ('product_tag_id', '=', tag.id)])
	# 			tag_id.append({'id': mapper.woo_id or None})
	# 	return tag_id

	def get_tag(self, product):
		""" get all tags of product """
		tag_id = []
		if product.tag_ids:
			for tag in product.tag_ids:
				mapper = tag.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('product_tag_id', '=', tag.id)])
				
				if mapper:					
					tag_id.append({'id': mapper.woo_id or None})
				else:
					#directory: model/product_py/export_product_tag(self,backend)
					tag.export_product_tag(self.backend)
					mapper = tag.backend_mapping.search(
						[('backend_id', '=', self.backend.id), ('product_tag_id', '=', tag.id)])
					if mapper:
						tag_id.append({'id': mapper.woo_id or None})

		return tag_id


	def get_images(self, product):
		try:

			""" get all categories of product """
			count = 1
			product_mapper = product.backend_mapping.search(
				[('backend_id', '=', self.backend.id), ('product_id', '=', product.id)], limit=1)
			if product_mapper:
				product_image_id = product_mapper.image_id
				# product_image_id = int(product_mapper.image_id)
			else:
				product_image_id = 0
			if product.image:
				if not (self.backend.login_wp_username and self.backend.application_password_password):
					raise UserError("Please add login username or application password's password")

				file_path = os.path.dirname(os.path.realpath(__file__))[:-4] + 'static/images/' + product.name + '.jpeg'
				with open(os.path.expanduser(file_path), 'wb') as fout:
					fout.write(base64.decodestring(product.image))
					os.chmod(file_path, 0o777)

				path = file_path.split('/')
				fileName = os.path.basename(file_path)

				# version = "wc/v2"
				# wcapi = API(url=self.backend.location, consumer_key=self.backend.consumer_key,
				# 	consumer_secret=self.backend.consumer_secret, version=version, wp_api=True)

				# url='https://productdevs.techspawnmobiles.com/woo_qb_connector/wp-json/wp/v2/media'
				# fileName = os.path.basename(file_path)
				# username = "productdevstechs_quickbooks"
				# password = "XnLj Adat bRKS uyX7 AHGV 6xOs"
				# credentials = username + ':' + username
				# auth = base64.b64encode(credentials.encode())




				# headers = {
				# 	# 'post_content':'post_content',
				# 	# 'Content-Type': 'image/jpg',
				# 	# 'Content-Disposition' : 'attachment; filename=%s'% fileName,
				# 	# 'Authorization': 'Basic {}'.format(auth),
				# 	'Authorization': 'Basic ' + auth.decode('utf-8'),
				# 	# "X-WP-Nonce":"f9cfad3623",
				# }


				# with open(file_path, "rb") as img_file:
				# 	odoo_image = b64encode(img_file.read())
				# attachment_id_1 = odoo_image.decode("utf-8")
				# attachment_id = "data:image/png;base64,"+attachment_id_1
				# this attachment_id is converting in image online converter but not wroking on here


				# media = {'file': open(file_path,'rb'),
				# 	'caption': 'My great demo picture'}

				wc_image_id = product_image_id
				wp_image_url = ''
				if wc_image_id:
					wc_media_images = requests.get(
						url='{}/wp-json/wp/v2/media'.format(self.backend.location, wc_image_id),
						headers={'Content-Type': 'image/jpg'},
						auth=(self.backend.login_wp_username, self.backend.application_password_password))

					if wc_media_images.status_code == 200 or wc_media_images.status_code == 201:
						json = wc_media_images.json()
						guid = json.get('guid')
						wp_url = guid.get('rendered')
						wp_image_url = wp_url



				if not wp_image_url:
					data = open(file_path, 'rb').read()
					# res = requests.post(url='https://productdevs.techspawnmobiles.com/woo_qb_connector/wp-json/wp/v2/media',

					headers = {
						'Content-Type': 'image/jpg',
						'Content-Disposition': 'attachment; filename=%s' % fileName}

					auth = (self.backend.login_wp_username, self.backend.application_password_password)

					res = requests.post(
						url='{}/wp-json/wp/v2/media'.format(self.backend.location),
						data=data,
						headers=headers,
						auth=auth
					)
					json = res.json()
					guid = json.get('guid')
					# wp_url = guid.get('raw')
					wp_image_url = guid.get('raw')
					product_image_id = json['id']

				# image = product.env['ir.attachment'].create({
				# 	# datas_fname="Test.png",
				# 	'name' : product.name,
				# 	'type' : "url",
				# 	'url' : "/".join(path[-4:]),
				# 	'mimetype' : 'image/jpeg',
				# 	'public' : True,
				# 	'res_model' : 'product.template',
				# 	'res_id' : product.id,
				# 	})

				# # print('#'*20)
				# # print("URL : ", request.httprequest.host_url + image.url)
				# # print('#'*20)
				# print(request.httprequest.host_url + image.url)


				# woo_object = product.backend_id

				# client = Client(woo_object.location, woo_object.consumer_key, woo_object.consumer_secret)

				# # prepare metadata
				# data = {
				# 	'name': product.name + '.jpeg',
				# 	'type': 'image/jpeg',  # mimetype
				# 	}

				# # read the binary file and let the XMLRPC library encode it into base64
				# with open(file_path, 'rb') as img:
				# 	data['bits'] = xmlrpc_client.Binary(img.read())

				# response = client.call(media.UploadFile(data))
				# print('#'*20)
				# print("Response : ", response)
				# print('#'*20)
				# attachment_id = response['id']
				# txt_path = "/home/mac49/Desktop/ODOO13/custom/addons/odoo_woo_connect_27_8_2020/attachment_id.txt"
				# with open(txt_path, 'r') as file:
				# 	attachment_id = file.read().replace('\n','')

				# imgdata = base64.b64decode(attachment_id.replace(' ', '+'))

				# filename = 'some_image.jpg'
				# with open(filename, 'wb') as f:
				# 	f.write(imgdata)


				images = [{"src":wp_image_url,
							"name":product.name or None,
							"position": 0,
							'id': product_image_id or 0
							}]
		except:
			images = []
		else :
			images = []

		# if product.product_image_ids:
		# 	for image in product.product_image_ids:
		# 		image_converted=WpImportExport.convert_image(image.image)
		# 		mapper = image.backend_mapping.search([('backend_id', '=', self.backend.id),
		# 											   ('product_image_id', '=', image.id)], limit=1)
		# 		images.append({"src": image_converted.decode('utf-8') or None,
		# 					   "name": image.name or product.name + str(count),
		# 					   "position": count,
		# 					   'id': mapper.woo_id or 0})
		# 		count += 1
		return images

	def get_product_variant(self, product):
		""" get all variant of product """
		product_variant = []
		for var_ids in product.product_variant_ids:
			woo_product_comb = var_ids
			tot_price = 0
			attr_array = []
			# product_template_attribute_value_ids
			for attribute in woo_product_comb.product_template_attribute_value_ids:
				tot_price += attribute.price_extra
				attr_mapper = attribute.attribute_id.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('attribute_id', '=', attribute.attribute_id.id)])
				attr = {
					'id': attr_mapper.woo_id or None,
					'name': attribute.attribute_id.name or None,
					'option': attribute.name or None,
				}
				attr_array.append(attr)
			if woo_product_comb:
				mapper = woo_product_comb.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('product_id', '=', woo_product_comb.id)])
				product_variant_dict = {
					"id": mapper.woo_id or None,
					"sku": woo_product_comb.default_code or None,
					"weight": woo_product_comb.weight or None,
					"regular_price": str(woo_product_comb.lst_price) or None,
					'sale_price': str(woo_product_comb.sale_price) or None,
					"stock_quantity": woo_product_comb.qty_available or None,
					"sale_price": woo_product_comb.lst_price or None,
					# 'images': self.get_images(arguments[1]) ,
					"dimensions": [{'width': str(woo_product_comb.website_size_x) or None,
									'length': str(woo_product_comb.website_size_y) or None,
									'height': str(woo_product_comb.website_size_z) or None,
									}],
					'managing_stock': True,
					'attributes': attr_array or '',

				}
				product_variant.append(product_variant_dict)
		return product_variant

	def export_product(self, method, arguments):
		""" Export product data"""
		_logger.debug("Start calling Woocommerce api %s", method)		
		print(arguments[1].name)
		if arguments[1].website_published:
			status = 'publish'
		else:
			status = 'draft'
		attributes = []
		for attr in arguments[1].attribute_line_ids:
			attributes_value = []
			mapper = attr.attribute_id.backend_mapping.search(
				[('backend_id', '=', self.backend.id), ('attribute_id', '=', attr.attribute_id.id)])

			# export_product_attribute('attribute',[None, attr.attribute_id])
			for value in attr.value_ids:
				# export_product_attribute_value('attribute_value',[None, attr.attribute_id])
				attributes_value.append(value.name)
			attributes.append({
				"id": mapper.woo_id or None,
				"name": attr.attribute_id.name or None,
				"visible": True,
				"variation": True,
				"options": attributes_value,
			})
		result_dict = {
			'name': arguments[1].name or None,
			'sku': arguments[1].default_code or None,
			'weight': str(arguments[1].weight) or None,
			'stock_quantity': arguments[1].qty_available or None,
			'short_description': arguments[1].short_description or '',
			'description': arguments[1].description or '',
			'categories': self.get_category(arguments[1]),
			'attributes': self.get_attributes(arguments[1]),
			# 'variations': self.get_product_variant(arguments[1]),
			'images': self.get_images(arguments[1]) or None,
			'tags': self.get_tag(arguments[1]) or None,
			'dimensions': {'length': str(arguments[1].website_size_x) or None,
						   'width': str(arguments[1].website_size_y) or None,
						   'height': str(arguments[1].website_size_z) or None,
						   },
			'status': status,
		}

		if arguments[1].product_variant_count > 1:
			result_dict.update({
				'type': "variable",
				'regular_price': str(arguments[1].regular_price) or None,
				'sale_price': str(arguments[1].sale_price) or None,
				'variations': self.get_product_variant(arguments[1]),
			})

		else:
			result_dict.update({
				'type': "simple",
				'managing_stock': True,
				'regular_price': str(arguments[1].regular_price) or None,
				'sale_price': str(arguments[1].sale_price) or None,
			})
		if arguments[1].qty_available:
			result_dict['manage_stock'] = True
			result_dict['in_stock'] = True
			result_dict['stock_quantity'] = arguments[1].qty_available
		
		_logger.info("Odoo Product Export Data: %s",result_dict)
		r = self.export(method, result_dict, arguments)

		#for exporting product variants
		if arguments[1].product_variant_count > 1:
			res_data = {'status': r.status_code, 'data': r.json()}
			self.export_product_variant(arguments[1],res_data,self.backend)

		return {'status': r.status_code, 'data': r.json()}


	def export_product_variant(self, product, res_data,backend):
		"""export all variant of product """
		
		mapper = product.backend_mapping.search(
            [('backend_id', '=', backend.id), ('product_id', '=', product.id)], limit=1)

		if mapper and (res_data['status'] == 200 or res_data['status'] == 201):
			product.write({'default_code': res_data['data']['sku'], 'slug': res_data['data']['slug']})
			mapper.write({'product_id': product.id, 'backend_id': backend.id, 'woo_id': res_data['data']['id']})
        
		elif (res_data['status'] == 200 or res_data['status'] == 201):
			product.write({'default_code': res_data['data']['sku'], 'slug': res_data['data']['slug']})
			product.backend_mapping.create({'product_id': product.id, 'backend_id': backend.id, 'woo_id': res_data['data']['id']}) 

		product_templ_mapper_woo_id = mapper.woo_id   

		# method == 'variation'
		product_variant = []
		for var_ids in product.product_variant_ids:
			woo_product_comb = var_ids
			tot_price = 0
			attr_array = []
			# product_template_attribute_value_ids
			for attribute in woo_product_comb.product_template_attribute_value_ids:
				tot_price += attribute.price_extra
				attr_mapper = attribute.attribute_id.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('attribute_id', '=', attribute.attribute_id.id)])
				attr = {
					# 'id': attr_mapper.woo_id or None,
					'name': attribute.attribute_id.name or None,
					'option': attribute.name or None,
				}
				attr_array.append(attr)
			
			if woo_product_comb:
				mapper = woo_product_comb.backend_mapping.search(
					[('backend_id', '=', self.backend.id), ('product_id', '=', woo_product_comb.id)])
				product_variant_dict = {
					"id": mapper.woo_id or None,
					"sku": woo_product_comb.default_code or None,
					"weight": str(woo_product_comb.weight) or None,
					"regular_price": str(woo_product_comb.lst_price) or None,
					# 'sale_price': str(woo_product_comb.sale_price) or None,
					"stock_quantity": woo_product_comb.qty_available or None,
					"sale_price": str(woo_product_comb.lst_price) or None,
					# 'images': self.get_images(arguments[1]) ,
					"dimensions": [{'width': str(woo_product_comb.website_size_x) or None,
									'length': str(woo_product_comb.website_size_y) or None,
									'height': str(woo_product_comb.website_size_z) or None,
									}],
					'manage_stock': True,
					'in_stock': True,
					'attributes': attr_array or '',

				}
				product_variant.append(product_variant_dict)

				if product_variant_dict:
					version = "wc/v2"
					wcapi = API(url=self.backend.location, consumer_key=self.backend.consumer_key,consumer_secret=self.backend.consumer_secret, version=version, wp_api=True)
					
					if product_variant_dict['id']:		
						record_data = wcapi.put("products/{}/variations/{}".format(product_templ_mapper_woo_id,product_variant_dict['id']), product_variant_dict)						
					else:
						record_data = wcapi.post("products/{}/variations".format(product_templ_mapper_woo_id), product_variant_dict)		
					
					
					record_response = {'status': record_data.status_code, 'data': record_data.json()}
					_logger.info("Odoo Product Variant Export Data: %s",record_response)
					self.product_variant_map(woo_product_comb,backend,record_response)

	
	def product_variant_map(self,variant,backend,record_response):
		mapper = variant.backend_mapping.search(
            [('backend_id', '=', backend.id), ('product_id', '=', variant.id)])

		if mapper and (record_response['status'] == 200 or record_response['status'] == 201):
			# variant.write({'default_code': record_response['data']['sku']})
			mapper.write({'product_id': variant.id, 'backend_id': backend.id, 'woo_id': record_response['data']['id']})
        
		elif (record_response['status'] == 200 or record_response['status'] == 201):
			# variant.write({'default_code': record_response['data']['sku']})
			variant.backend_mapping.create({'product_id': variant.id, 'backend_id': backend.id, 'woo_id': record_response['data']['id']}) 



		