# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cstr
from frappe.model.mapper import get_mapped_doc
from erpnext.controllers.status_updater import StatusUpdater
from frappe.utils import flt, cint, cstr , nowdate

class Contact(StatusUpdater):
	def autoname(self):

		count = frappe.db.sql("""select name from `tabContact` where first_name='%s' and last_name='%s' """%(self.first_name,self.last_name),as_list=1,debug=1)

		number = cint(len(count)) + 1
		name = " ".join(filter(None,
			[cstr(self.get(f)).strip() for f in ["first_name", "last_name"]]))
		self.name = "-".join(filter(None,
			[cstr(f).strip() for f in [number, name]]))

		# concat party name if reqd
		# for fieldname in ("customer", "supplier", "sales_partner"):
		# 	if self.get(fieldname):
		# 		self.name = self.name + "-" + cstr(self.get(fieldname)).strip()
		# 		break

	def validate(self):
		self.set_status()
		self.validate_primary_contact()
		self.set_user()
		self.validate_childtable_entry()
		self.validate_linkdedin_id()
		self.validate_skype_id()
		self.validate_duplication_emailid()
		self.validate_one_preffered_contact()
		self.create_preferred_details()
		

	def create_preferred_details(self):
		if self.get('contacts'):
			for d in self.get('contacts'):
				if d.preffered == 1:
					self.country_code = d.country_code
					self.email = d.email_id
					self.mobile = d.mobile_no
					self.landline = d.landline


	def validate_childtable_entry(self):
		if not self.get('contacts'):
			frappe.msgprint("At least one entry is necessary in Contact Details child table",raise_exception=1)

	def set_user(self):
		if not self.user and self.email_id:
			self.user = frappe.db.get_value("User", {"email": self.email_id})

	def validate_linkdedin_id(self):
		if self.linkedin_id:
			if frappe.db.sql("""select name from `tabContact` where name!='%s' and linkedin_id='%s'"""%(self.name,self.linkedin_id)):
				frappe.msgprint("Linkedin id '%s' is already assigned for another contact"%self.linkedin_id,raise_exception=1)

	def validate_skype_id(self):
		if self.skype_id:
			if frappe.db.sql("""select name from `tabContact` where name!='%s' and skype_id='%s'"""%(self.name,self.skype_id)):
				frappe.msgprint("Skype id '%s' is already assigned for another contact"%self.skype_id,raise_exception=1)

	def validate_duplication_emailid(self):
		email_list = []
		if self.get('contacts'):
			for d in self.get('contacts'):
				if d.email_id not in email_list:
					email_list.append(d.email_id)
				else:
					frappe.msgprint("Duplicate Email ID is not allowed",raise_exception=1)
					break

	def validate_one_preffered_contact(self):
		count = 0
		if self.get('contacts'):
			for d in self.get('contacts'):
				if d.preffered == 1:
					count = count + 1
			if cint(count)>1:
				frappe.msgprint("Only one contact details must be preferred as primary details",raise_exception=1)
			elif cint(count)<1:
				frappe.msgprint(" At least one contact must be selected as preferred primary details",raise_exception=1)



	def validate_primary_contact(self):
		if self.is_primary_contact == 1:
			if self.customer:
				frappe.db.sql("update tabContact set is_primary_contact=0 where customer = %s",
					(self.customer))
			elif self.supplier:
				frappe.db.sql("update tabContact set is_primary_contact=0 where supplier = %s",
					 (self.supplier))
			elif self.sales_partner:
				frappe.db.sql("""update tabContact set is_primary_contact=0
					where sales_partner = %s""", (self.sales_partner))
		else:
			if self.customer:
				if not frappe.db.sql("select name from tabContact \
						where is_primary_contact=1 and customer = %s", (self.customer)):
					self.is_primary_contact = 1
			elif self.supplier:
				if not frappe.db.sql("select name from tabContact \
						where is_primary_contact=1 and supplier = %s", (self.supplier)):
					self.is_primary_contact = 1
			elif self.sales_partner:
				if not frappe.db.sql("select name from tabContact \
						where is_primary_contact=1 and sales_partner = %s",
						self.sales_partner):
					self.is_primary_contact = 1

	def on_trash(self):
		frappe.db.sql("""update `tabIssue` set contact='' where contact=%s""",
			self.name)

@frappe.whitelist()
def invite_user(contact):
	contact = frappe.get_doc("Contact", contact)
	if contact.has_permission("write"):
		user = frappe.get_doc({
			"doctype": "User",
			"first_name": contact.first_name,
			"last_name": contact.last_name,
			"email": contact.email_id,
			"user_type": "Website User",
			"send_welcome_email": 1
		}).insert(ignore_permissions = True)

		return user.name

@frappe.whitelist()
def make_address(source_name, target_doc=None):
	return _make_address(source_name, target_doc)

def _make_address(source_name, target_doc=None, ignore_permissions=False):
	def set_missing_values(source, target):
		pass
		# if source.company_name:
		# 	target.customer_type = "Company"
		# 	target.customer_name = source.company_name
		# else:
		# 	target.customer_type = "Individual"
		# 	target.customer_name = source.lead_name

		# target.customer_group = frappe.db.get_default("customer_group")

	doclist = get_mapped_doc("Contact", source_name,
		{"Contact": {
			"doctype": "Address",
			"field_map": {
				"contact": "name"
				# "company_name": "customer_name",
				# "contact_no": "phone_1",
				# "fax": "fax_1"
			}
		}}, target_doc, set_missing_values, ignore_permissions=ignore_permissions)

	return doclist

@frappe.whitelist()
def get_contact_details(contact):
	contact = frappe.get_doc("Contact", contact)
	out = {
		"contact_person": contact.get("name"),
		"contact_display": " ".join(filter(None,
			[contact.get("first_name"), contact.get("last_name")])),
		"contact_email": contact.get("email_id"),
		"contact_mobile": contact.get("mobile_no"),
		"contact_phone": contact.get("phone"),
		"contact_designation": contact.get("designation"),
		"contact_department": contact.get("department")
	}
	return out
