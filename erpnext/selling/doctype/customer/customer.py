# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.naming import make_autoname
from frappe import _, msgprint, throw
import frappe.defaults
from frappe.utils import flt, cint, cstr , nowdate
from frappe.desk.reportview import build_match_conditions
from erpnext.utilities.transaction_base import TransactionBase
from erpnext.utilities.address_and_contact import load_address_and_contact
from erpnext.accounts.party import validate_party_accounts
from frappe.model.mapper import get_mapped_doc
import datetime

class Customer(TransactionBase):
	def get_feed(self):
		return self.customer_name

	def onload(self):
		"""Load address and contacts in `__onload`"""
		load_address_and_contact(self, "customer")
		import time
		todays_date = datetime.datetime.strptime(cstr(nowdate()),'%Y-%m-%d')
		if todays_date.month > 6:
			self.get_financial_data()

	def get_financial_data(self):
		fiscal_year = frappe.db.sql("""select value from `tabSingles` where doctype='Global Defaults' and field='current_fiscal_year'""",as_list=1)
		if fiscal_year:
			last_fiscal_year = frappe.db.sql("""select name from `tabFiscal Year` where name < '%s' order by name desc limit 1"""%fiscal_year[0][0],as_list=1)
			if last_fiscal_year:
				if not frappe.db.sql("""select name from `tabFinancial Data` where customer='%s' and financial_year='%s'"""%(self.name,last_fiscal_year[0][0])):
					frappe.msgprint("Financial data is not updated")


	def autoname(self):
		cust_master_name = frappe.defaults.get_global_default('cust_master_name')
		if cust_master_name == 'Customer Name':
			self.name = self.get_customer_name()
		else:
			if not self.naming_series:
				frappe.throw(_("Series is mandatory"), frappe.MandatoryError)

			self.name = make_autoname(self.naming_series+'.#####')
			
	def get_customer_name(self):
		if frappe.db.get_value("Customer", self.customer_name):
			count = frappe.db.sql("""select ifnull(max(SUBSTRING_INDEX(name, ' ', -1)), 0) from tabCustomer
				 where name like  '%{0} - %'""".format(self.customer_name), as_list=1)[0][0]
			count = cint(count) + 1
			return "{0} - {1}".format(self.customer_name, cstr(count))
		
		return self.customer_name

	def validate(self):
		self.flags.is_new_doc = self.is_new()
		validate_party_accounts(self)
		self.validate_promoters()
		self.validate_cin()
		self.validate_pan()
		self.validate_pan_number(self.pan_number)
		if self.cin_number:
			self.validate_cin_number(self.cin_number)

	def validate_cin(self):
		if frappe.db.sql("""select name from `tabCustomer` where name!='%s' and cin_number='%s'"""%(self.name,self.cin_number)):
			name = frappe.db.sql("""select name from `tabCustomer` where name!='%s' and cin_number='%s'"""%(self.name,self.cin_number),as_list=1)
			frappe.msgprint("CIN No. '%s' is already linked with Customer '%s' "%(self.cin_number,name[0][0]),raise_exception=1)

	def validate_pan(self):
		if frappe.db.sql("""select name from `tabCustomer` where name!='%s' and pan_number='%s'"""%(self.name,self.pan_number)):
			name = frappe.db.sql("""select name from `tabCustomer` where name!='%s' and pan_number='%s'"""%(self.name,self.pan_number),as_list=1)
			frappe.msgprint("PAN No. '%s' is already linked with Customer '%s' "%(self.pan_number,name[0][0]),raise_exception=1)

	def validate_promoters(self):
		promoters_list = []
		if self.get('promoters_details'):
			for d in self.get('promoters_details'):
				if d.p_name not in promoters_list:
					promoters_list.append(d.p_name)
				else:
					frappe.msgprint("Duplicate promoter name is not allowed",raise_exception=1)
					break

	def validate_pan_number(self,pan_number):
		import re
		pattern = r'[A-Z]'
		if len(self.pan_number) == 10:
			if self.pan_number[0:5].isalpha():
					if self.pan_number[5:9].isdigit():
						if self.pan_number[-1].isalpha():
							pass
						else:
							frappe.msgprint("PAN number last charcter must be letter",raise_exception=1)
					else:
						frappe.msgprint("PAN number letters  from possition 6-9 must be numeric",raise_exception=1)
			else:
				frappe.msgprint("First five characters of PAN number must be letters",raise_exception=1)
		else:
			frappe.msgprint("PAN No. must be consist of 10 Digits.",raise_exception=1)


	def validate_cin_number(self,cin_number):
		import re
		pattern = r'[A-Z]'
		if len(self.cin_number) == 21:
				if self.cin_number[0:1].isalpha():
					if self.cin_number[1:6].isdigit():
						if self.cin_number[6:8].isalpha():
							if self.cin_number[8:12].isdigit():
								if self.cin_number[12:15].isalpha():
									if self.cin_number[15:21].isdigit():
										pass
									else:
										frappe.msgprint("CIN number letters  from possition 15-21 must be numeric",raise_exception=1)
								else:
									frappe.msgprint("CIN number letters  from possition 12-15 must be alphanumeric",raise_exception=1)
							else:
								frappe.msgprint("CIN number letters  from possition 9-12 must be numeric",raise_exception=1)

						else:
							frappe.msgprint("CIN number letters  from possition 7-8 must be alphanumeric",raise_exception=1)
					else:
						frappe.msgprint("CIN number letters  from possition 2-6 must be numeric",raise_exception=1)
				else:
					frappe.msgprint("First character of CIN number must be letter",raise_exception=1)
		else:
			frappe.msgprint("CIN No. must be consist of 21 Digits.",raise_exception=1)



	def update_lead_status(self):
		if self.lead_name:
			frappe.db.sql("update `tabLead` set status='Converted' where name = %s", self.lead_name)

	def update_address(self):
		frappe.db.sql("""update `tabAddress` set customer_name=%s, modified=NOW()
			where customer=%s""", (self.customer_name, self.name))

	def update_contact(self):
		frappe.db.sql("""update `tabContact` set customer_name=%s, modified=NOW()
			where customer=%s""", (self.customer_name, self.name))

	def create_lead_address_contact(self):
		if self.lead_name:
			if not frappe.db.get_value("Address", {"lead": self.lead_name, "customer": self.name}):
				frappe.db.sql("""update `tabAddress` set customer=%s, customer_name=%s where lead=%s""",
					(self.name, self.customer_name, self.lead_name))

			lead = frappe.db.get_value("Lead", self.lead_name, ["lead_name", "email_id", "phone", "mobile_no"], as_dict=True)

			c = frappe.new_doc('Contact')
			c.first_name = lead.lead_name
			c.email_id = lead.email_id
			c.phone = lead.phone
			c.mobile_no = lead.mobile_no
			c.customer = self.name
			c.customer_name = self.customer_name
			c.is_primary_contact = 1
			c.flags.ignore_permissions = self.flags.ignore_permissions
			c.autoname()
			if not frappe.db.exists("Contact", c.name):
				c.insert()

	def on_update(self):
		self.validate_name_with_customer_group()

		self.update_lead_status()
		self.update_address()
		self.update_contact()
		# self.update_financial_data()

		if self.flags.is_new_doc:
			self.create_lead_address_contact()

	def validate_name_with_customer_group(self):
		if frappe.db.exists("Customer Group", self.name):
			frappe.throw(_("A Customer Group exists with same name please change the Customer name or rename the Customer Group"), frappe.NameError)

	def delete_customer_address(self):
		addresses = frappe.db.sql("""select name, lead from `tabAddress`
			where customer=%s""", (self.name,))

		for name, lead in addresses:
			if lead:
				frappe.db.sql("""update `tabAddress` set customer=null, customer_name=null
					where name=%s""", name)
			else:
				frappe.db.sql("""delete from `tabAddress` where name=%s""", name)

	def delete_customer_contact(self):
		for contact in frappe.db.sql_list("""select name from `tabContact`
			where customer=%s""", self.name):
				frappe.delete_doc("Contact", contact)

	def on_trash(self):
		self.delete_customer_address()
		self.delete_customer_contact()
		if self.lead_name:
			frappe.db.sql("update `tabLead` set status='Interested' where name=%s",self.lead_name)

	def after_rename(self, olddn, newdn, merge=False):
		set_field = ''
		if frappe.defaults.get_global_default('cust_master_name') == 'Customer Name':
			frappe.db.set(self, "customer_name", newdn)
			self.update_contact()
			set_field = ", customer_name=%(newdn)s"
		self.update_customer_address(newdn, set_field)

	def update_customer_address(self, newdn, set_field):
		frappe.db.sql("""update `tabAddress` set address_title=%(newdn)s
			{set_field} where customer=%(newdn)s"""\
			.format(set_field=set_field), ({"newdn": newdn}))

@frappe.whitelist()
def get_dashboard_info(customer):
	if not frappe.has_permission("Customer", "read", customer):
		frappe.msgprint(_("Not permitted"), raise_exception=True)

	out = {}
	for doctype in ["Financial Data","FFWW","Operational Matrix","Project Commercial"]:
		if doctype == 'Operational Matrix':
			out[doctype] = frappe.db.get_value('Operation And Project Commercial',
			{"docstatus": ["!=", 2],"customer":customer,"operational_matrix_status":'Active' }, "count(*)")
		else:
			out[doctype] = frappe.db.get_value(doctype,
				{"customer": customer, "docstatus": ["!=", 2] }, "count(*)")

	return out


def get_customer_list(doctype, txt, searchfield, start, page_len, filters):
	if frappe.db.get_default("cust_master_name") == "Customer Name":
		fields = ["name", "customer_group", "territory"]
	else:
		fields = ["name", "customer_name", "customer_group", "territory"]

	match_conditions = build_match_conditions("Customer")
	match_conditions = "and {}".format(match_conditions) if match_conditions else ""

	return frappe.db.sql("""select %s from `tabCustomer` where docstatus < 2
		and (%s like %s or customer_name like %s)
		{match_conditions}
		order by
		case when name like %s then 0 else 1 end,
		case when customer_name like %s then 0 else 1 end,
		name, customer_name limit %s, %s""".format(match_conditions=match_conditions) %
		(", ".join(fields), searchfield, "%s", "%s", "%s", "%s", "%s", "%s"),
		("%%%s%%" % txt, "%%%s%%" % txt, "%%%s%%" % txt, "%%%s%%" % txt, start, page_len))


def check_credit_limit(customer, company):
	customer_outstanding = get_customer_outstanding(customer, company)

	credit_limit = get_credit_limit(customer, company)
	if credit_limit > 0 and flt(customer_outstanding) > credit_limit:
		msgprint(_("Credit limit has been crossed for customer {0} {1}/{2}")
			.format(customer, customer_outstanding, credit_limit))

		# If not authorized person raise exception
		credit_controller = frappe.db.get_value('Accounts Settings', None, 'credit_controller')
		if not credit_controller or credit_controller not in frappe.get_roles():
			throw(_("Please contact to the user who have Sales Master Manager {0} role")
				.format(" / " + credit_controller if credit_controller else ""))

def get_customer_outstanding(customer, company):
	# Outstanding based on GL Entries
	outstanding_based_on_gle = frappe.db.sql("""select sum(ifnull(debit, 0)) - sum(ifnull(credit, 0))
		from `tabGL Entry` where party_type = 'Customer' and party = %s and company=%s""", (customer, company))

	outstanding_based_on_gle = flt(outstanding_based_on_gle[0][0]) if outstanding_based_on_gle else 0

	# Outstanding based on Sales Order
	outstanding_based_on_so = frappe.db.sql("""
		select sum(base_grand_total*(100 - ifnull(per_billed, 0))/100)
		from `tabSales Order`
		where customer=%s and docstatus = 1 and company=%s
		and ifnull(per_billed, 0) < 100 and status != 'Stopped'""", (customer, company))

	outstanding_based_on_so = flt(outstanding_based_on_so[0][0]) if outstanding_based_on_so else 0.0

	# Outstanding based on Delivery Note
	unmarked_delivery_note_items = frappe.db.sql("""select
			dn_item.name, dn_item.amount, dn.base_net_total, dn.base_grand_total
		from `tabDelivery Note` dn, `tabDelivery Note Item` dn_item
		where
			dn.name = dn_item.parent
			and dn.customer=%s and dn.company=%s
			and dn.docstatus = 1 and dn.status != 'Stopped'
			and ifnull(dn_item.against_sales_order, '') = ''
			and ifnull(dn_item.against_sales_invoice, '') = ''""", (customer, company), as_dict=True)

	outstanding_based_on_dn = 0.0

	for dn_item in unmarked_delivery_note_items:
		si_amount = frappe.db.sql("""select sum(ifnull(amount, 0))
			from `tabSales Invoice Item`
			where dn_detail = %s and docstatus = 1""", dn_item.name)[0][0]

		if flt(dn_item.amount) > flt(si_amount) and dn_item.base_net_total:
			outstanding_based_on_dn += ((flt(dn_item.amount) - flt(si_amount)) \
				/ dn_item.base_net_total) * dn_item.base_grand_total

	return outstanding_based_on_gle + outstanding_based_on_so + outstanding_based_on_dn


def get_credit_limit(customer, company):
	credit_limit, customer_group = frappe.db.get_value("Customer", customer, ["credit_limit", "customer_group"])
	if not credit_limit:
		credit_limit = frappe.db.get_value("Customer Group", customer_group, "credit_limit") or \
			frappe.db.get_value("Company", company, "credit_limit")

	return credit_limit


@frappe.whitelist()
def get_customer_contact(customer):
	final_contact_list = []
	#contact_list = frappe.db.get_value("Contact", {"customer":customer}, "name")
	contact_list = frappe.db.sql("""select name from `tabContact` where customer='%s'"""%customer,as_list=1)

	if len(contact_list)>0:
		for i in contact_list:
			contact = frappe.get_doc("Contact", i[0])
			out = {
				"contact_person": contact.get("name"),
				"contact_display": " ".join(filter(None,
					[contact.get("first_name"), contact.get("last_name")])),
				"contact_email": contact.get("email_id"),
				"contact_email_personal": contact.get("email_id_personal"),
				"contact_mobile": contact.get("mobile_no"),
				"contact_mobile_official": contact.get("mobile_no_official"),
				"contact_phone": contact.get("phone"),
				"contact_designation": contact.get("contact_designation"),
				"customer": contact.get("customer")
				
			}
			final_contact_list.append(out)

	operationl_matrix_list = get_operational_matrix(customer)

	return {'final_contact_list': final_contact_list,
			'operationl_matrix_list': operationl_matrix_list}

def get_operational_matrix(customer):
	operationl_matrix_list = []
	operational_list = frappe.db.sql("""select name from `tabOperational Matrix` where customer='%s'"""%customer,as_list=1)
	
	if len(operational_list)>0:
		for i in operational_list:
			om = frappe.get_doc("Operational Matrix", i[0])
			out = {
				"first_name": om.get("f_name"),
				"Second_name": om.get("s_name"),
				"email": om.get("email"),
				"role": om.get("role"),
				"contact": om.get("contact")	
			}
			operationl_matrix_list.append(out)

		return operationl_matrix_list


@frappe.whitelist()
def get_financial_data(customer):
	fiscal_year = frappe.db.sql("""select value from `tabSingles` where doctype='Global Defaults' and field='current_fiscal_year'""",as_list=1)
	if fiscal_year:
		last_fiscal_year = frappe.db.sql("""select name from `tabFiscal Year` where name < '%s' order by name desc limit 1"""%fiscal_year[0][0],as_list=1)
		if last_fiscal_year:
			if frappe.db.sql("""select name from `tabFinancial Data` where customer='%s' and financial_year='%s'"""%(customer,last_fiscal_year[0][0])):
				return {"status":True}
			else:
				return {"status":False}



@frappe.whitelist()
def add_ffww(source_name, target_doc=None):
	return _add_ffww(source_name, target_doc)

def _add_ffww(source_name, target_doc=None, ignore_permissions=False):
	def set_missing_values(source, target):
		pass

	doclist = get_mapped_doc("Customer", source_name,
		{"Customer": {
			"doctype": "FFWW",
			"field_map": {
				"custmer_name": "name"
				
			}
		}}, target_doc, set_missing_values, ignore_permissions=ignore_permissions)

	return doclist
	