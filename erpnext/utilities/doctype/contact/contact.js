// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

{% include 'controllers/js/contact_address_common.js' %};

cur_frm.add_fetch('customer', 'customer_name', 'customer_name');
cur_frm.add_fetch('country_name','country_code','country_code');
cur_frm.add_fetch('country_name','number_of_digits_allowed','digit');

cur_frm.email_field = "email_id";
frappe.ui.form.on("Contact", {
	refresh: function(frm) {
		//var doc = this.frm.doc;
		if(!frm.doc.__islocal) {
			frm.add_custom_button(__("Create Address"), function() {
				frappe.model.open_mapped_doc({
					method: "erpnext.utilities.doctype.contact.contact.make_address",
					frm: frm
				})
			});
		}
	},
	validate: function(frm) {
		// clear linked customer / supplier / sales partner on saving...
		$.each(["Customer", "Supplier", "Sales Partner"], function(i, doctype) {
			var name = frm.doc[doctype.toLowerCase().replace(/ /g, "_")];
			if(name && locals[doctype] && locals[doctype][name])
				frappe.model.remove_from_locals(doctype, name);
		});
	}
});

// Validate Email ID..........................................
cur_frm.cscript.email_id = function(doc,cdt,cdn){
	var d = locals[cdt][cdn];
	var reg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	if (reg.test(d.email_id) == false) 
	{
	    msgprint('Invalid Email Address');
	    d.email_id=''
	    refresh_field('contacts');
	}
}

// Validate Email ID.................................................
cur_frm.cscript.mobile_no = function(doc,cdt,cdn){
	var d = locals[cdt][cdn];
	if(isNaN(d.mobile_no)==true){
		msgprint("Mobile number must be consist of only Digits")
		d.mobile_no=''
		refresh_field('contacts');
	}
	if(d.country_name && d.mobile_no){
		if((d.mobile_no).toString().length != parseInt(d.digit)){
			msgprint('Mobile Number must be '+d.digit+' digits as per the country '+d.country_name+'');
			d.mobile_no=''
			refresh_field('contacts');
		}
	}
}

// Valdate mobile no with respect to its digits according to the country specified.........................
cur_frm.cscript.country_name = function(doc,cdt,cdn){
	var d = locals[cdt][cdn];
	if(d.mobile_no){
		if((d.mobile_no).toString().length!= parseInt(d.digit)){
			msgprint('Mobile Number must be '+d.digit+' digits as per the country '+d.country_name+'');
			d.mobile_no=''
			refresh_field('contacts');
		}
	}
}

// Trigger on addition of new row in contcat details child table.....
cur_frm.cscript.contacts_add = function(doc,cdt,cdn){
	var d = locals[cdt][cdn]
	
	if(frappe.route_history.length>1){
		var last_route = frappe.route_history.slice(-2, -1)[0];
		if(last_route && last_route[0]==="Form") {
			var doctype = last_route[1],
				docname = last_route.slice(2).join("/");
			if(doctype){
				if (doctype == 'FFWW'){
					d.ffww = docname
					refresh_field('contacts');
				}
			}
		}

	}
	if(frappe.route_options){
		
		d.ffww = frappe.route_options
		refresh_field('contacts')
	}

}