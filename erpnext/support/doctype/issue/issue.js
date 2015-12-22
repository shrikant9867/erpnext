frappe.ui.form.on("Issue", {
	"onload": function(frm) {
		frm.email_field = "raised_by";
	},

	"refresh": function(frm) {
		if(frm.doc.status==="Open") {
			frm.add_custom_button("Close", function() {
				frm.set_value("status", "Closed");
				frm.save();
			});
		} else {
			frm.add_custom_button("Reopen", function() {
				frm.set_value("status", "Open");
				frm.save();
			});
		}
	}
});

frappe.ui.form.on("Issue", "onload",function(frm){
	return frappe.call({
		method: "erpnext.support.doctype.issue.issue.get_jobseekers_list",
		args: {
			"doc":cur_frm.doc
		},
		callback: function(r){
			console.log(r.message)
			if(r.message){
				cur_frm.set_value("job_seekers",r.message)	
				cur_frm.set_value("raised_by",r.message)
			}
		}	
	})
})


frappe.ui.form.on("Issue", "onload",function(frm){
	return frappe.call({
		method: "erpnext.support.doctype.issue.issue.get_email",
		args: {
			"doc":cur_frm.doc
		},
		callback: function(r){
			console.log(r.message)
			if(r.message){
				cur_frm.set_value("raised_by",r.message)
				refresh.field("raised_by")
			}
		}	
	})
})
