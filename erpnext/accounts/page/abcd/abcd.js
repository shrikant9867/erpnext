frappe.pages['abcd'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'abcd',
		single_column: true
	});
}