// Copyright (c) 2025, mohtashim and contributors
// For license information, please see license.txt

frappe.ui.form.on('Invoice Upload', {
    create_invoice: function (frm) {
        frappe.call({
            method: "invoice_ocr.utils.create_invoice",
            args: { name: frm.doc.name },
            callback: function (r) {
                if (r.message) {
                    frappe.set_route("Form", r.message.doctype, r.message.name);
                }
            }
        });
    }
});
