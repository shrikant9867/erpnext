// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Customer", "refresh", function(frm) {
	cur_frm.cscript.setup_dashboard(frm.doc);

	if(frappe.defaults.get_default("cust_master_name")!="Naming Series") {
		frm.toggle_display("naming_series", false);
	} else {
		erpnext.toggle_naming_series();
	}

	if(!frm.doc.__islocal) {
			frm.add_custom_button(__("ADD FFWW"), function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.selling.doctype.customer.customer.add_ffww",
					frm: frm
				})
			});
	}

	frm.toggle_display(['address_html','contact_html','financial_details'], !frm.doc.__islocal);

	if(!frm.doc.__islocal) {
		erpnext.utils.render_address_and_contact(frm);
	} else {
		erpnext.utils.clear_address_and_contact(frm);
	}

	var grid = cur_frm.get_field("sales_team").grid;
	grid.set_column_disp("allocated_amount", false);
	grid.set_column_disp("incentives", false);

})

cur_frm.cscript.onload = function(doc, dt, dn) {
	cur_frm.cscript.load_defaults(doc, dt, dn);
}
cur_frm.cscript.cin_number =  function(doc,cdt,cdn){
	var isnum = /^\d+$/.test(doc.cin_number);
	
	var reg = /^[a-zA-Z0-9_]*$/
	if(reg.test(doc.cin_number) == false) {
		msgprint('CIN No. must be Alphanumeric')
	}

	if(doc.cin_number.length!=21){
		msgprint('CIN No. must be consist of 21 Digits')
	}
	if(isnum==true){
		msgprint('CIN No. must be combination of Digits and Characters')
	}
}

cur_frm.cscript.pan_number =  function(doc,cdt,cdn){
	var isnum = /^\d+$/.test(doc.cin_number);
	var reg = /^[a-zA-Z0-9_]*$/
	if(reg.test(doc.pan_number) == false) {
		msgprint('PAN No. must be alphanumeric')
	}

	if(doc.pan_number.length!=10){
		msgprint('PAN No. must be consist of 10 Digits')
	}
	if(isnum==true){
		msgprint('PAN No. must be combination of Digits and Characters')
	}
}

cur_frm.cscript.load_defaults = function(doc, dt, dn) {
	doc = locals[doc.doctype][doc.name];
	if(!(doc.__islocal && doc.lead_name)) { return; }

	var fields_to_refresh = frappe.model.set_default_values(doc);
	if(fields_to_refresh) { refresh_many(fields_to_refresh); }
}

cur_frm.add_fetch('lead_name', 'company_name', 'customer_name');
cur_frm.add_fetch('default_sales_partner','commission_rate','default_commission_rate');

cur_frm.cscript.validate = function(doc, dt, dn) {
	if(doc.lead_name) frappe.model.clear_doc("Lead", doc.lead_name);
}

cur_frm.cscript.setup_dashboard = function(doc) {
	cur_frm.dashboard.reset(doc);
	if(doc.__islocal)
		return;
	var status = ''

	cur_frm.dashboard.add_doctype_badge("Financial Data", "customer");
	//cur_frm.dashboard.add_doctype_badge("FFWW Details", "customer");
	cur_frm.dashboard.add_page_badge("FFWW","customer");
	cur_frm.dashboard.add_page_badge("Operational Matrix","customer");
	cur_frm.dashboard.add_page_badge("Project Commercial","customer");


	frappe.call({
		type: "GET",
		method: "erpnext.selling.doctype.customer.customer.get_customer_contact",
		args: {
			customer: cur_frm.doc.name
		},
		callback: function(r) {
			frappe.call({
				type: "GET",
				method: "erpnext.selling.doctype.customer.customer.get_dashboard_info",
				args: {
					customer: cur_frm.doc.name
				},
				callback: function(r) {
					cur_frm.dashboard.set_headline(
								__("Other Details: ") + "<b>")
					cur_frm.dashboard.set_badge_count(r.message);
				}
			});
			cur_frm.dashboard.set_headline(
						__("Other Details: ") + "<b>")
			
		}

	});

	
}

cur_frm.fields_dict['customer_group'].get_query = function(doc, dt, dn) {
	return{
		filters:{'is_group': 'No'}
	}
}

cur_frm.fields_dict.lead_name.get_query = function(doc, cdt, cdn) {
	return{
		query: "erpnext.controllers.queries.lead_query"
	}
}

cur_frm.fields_dict['default_price_list'].get_query = function(doc, cdt, cdn) {
	return{
		filters:{'selling': 1}
	}
}

cur_frm.fields_dict['accounts'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
	var d  = locals[cdt][cdn];
	var filters = {
		'account_type': 'Receivable',
		'company': d.company,
		"is_group": 0
	};

	if(doc.party_account_currency) {
		$.extend(filters, {"account_currency": doc.party_account_currency});
	}

	return {
		filters: filters
	}
}


cur_frm.fields_dict['promoters_details'].grid.get_field('p_name').get_query = function(doc, cdt, cdn) {
	return {
		filters: {
			
			"contact_designation": 'Promoter'
		}
	}
}

cur_frm.cscript.date_of_incorporation = function(doc,cdt,cdn){
	var today = new Date();
	if(today<new Date(doc.date_of_incorporation)){
		msgprint("Date of incorporation must be less than the Future Date")
		doc.date_of_incorporation=''
		refresh_field('date_of_incorporation')
	}
}

cur_frm.cscript.promoters_percentage = function(doc,cdt,cdn){
	var d = locals[cdt][cdn]
	if(d.promoters_percentage>0 && d.promoters_percentage<=100){
		console.log("hi")
	}
	else{
		msgprint("Percentage value must be less than 100%")
		d.promoters_percentage=''
		refresh_field('promoters_details')
	}
}