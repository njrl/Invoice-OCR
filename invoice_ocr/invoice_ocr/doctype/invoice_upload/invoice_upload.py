import frappe
import json
import pytesseract
import re
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from frappe.utils.file_manager import get_file_path
from frappe.model.document import Document
from PIL import Image
from frappe.utils import add_days
from frappe.utils import get_url_to_form



class InvoiceUpload(Document):
    def on_submit(self):
        self.ocr_status = "Processing"
        self.save()
        frappe.db.commit()

        try:
            if not self.file:
                frappe.throw("No file attached for OCR.")

            file_path = get_file_path(self.file)

            text = ""
            if file_path.endswith(".pdf"):
                images = convert_from_path(file_path)
                for img in images:
                    text += pytesseract.image_to_string(img)
            else:
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)

            frappe.logger().info(f"[OCR] Extracted Text:\n{text}")

            invoice_data = {
                "invoice_no": self.extract_keyword(text, ["Invoice#", "Invoice No", "Invoice Number"]),
                "date": self.extract_keyword(text, ["Date"]),
                "items": self.extract_items(text),
                "total": self.extract_keyword(text, ["Total", "Amount Due"])
            }

            frappe.db.set_value("Invoice Upload", self.name, "ocr_status", "Extracted")
            frappe.db.set_value("Invoice Upload", self.name, "extracted_data", json.dumps(invoice_data, indent=2))
            frappe.db.commit()

            self.create_invoice(invoice_data)

        except Exception:
            frappe.db.set_value("Invoice Upload", self.name, "ocr_status", "Failed")
            frappe.db.commit()
            frappe.log_error(frappe.get_traceback(), "OCR Failed")

    def extract_keyword(self, text, keys):
        for line in text.splitlines():
            for key in keys:
                if key.lower() in line.lower():
                    return line.split()[-1]
        return ""

    def extract_items(self, text):
        lines = text.splitlines()
        items = []
        item_pattern = re.compile(r"(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)$")

        for line in lines:
            match = item_pattern.search(line)
            if match:
                description = match.group(1).strip()
                qty = float(match.group(2))
                rate = float(match.group(3))
                items.append({
                    "description": description,
                    "qty": qty,
                    "rate": rate
                })

        return items

    def create_invoice(self, data):
        if not data.get("items"):
            frappe.throw("No items found from OCR. Please upload a clearer invoice or check the format.")

        if self.party_type == "Supplier":
            pi = frappe.new_doc("Purchase Invoice")
            pi.supplier = self.party
        else:
            self.ensure_customer_exists()
            pi = frappe.new_doc("Sales Invoice")
            pi.customer = self.party

        expense_account = self.get_expense_account()

        for item in data.get("items", []):
            item_code = self.ensure_item_exists(item["description"])
            pi.append("items", {
                "item_code": item_code,
                "qty": item.get("qty"),
                "rate": item.get("rate"),
				"uom":"Nos",
                "expense_account": expense_account
            })

        pi.posting_date = data.get("date")
        pi.due_date = add_days(pi.posting_date, 30)
        pi.base_write_off_amount = 0.0
        pi.write_off_amount = 0.0

        if self.party_type == "Supplier":
            pi.write_off_account = frappe.db.get_value("Company", pi.company, "default_payable_account")
        else:
            pi.write_off_account = frappe.db.get_value("Company", pi.company, "default_receivable_account")

        pi.set_missing_values()
        pi.calculate_taxes_and_totals()
        pi.insert(ignore_permissions=True)

        frappe.msgprint(f"<a href='{get_url_to_form(pi.doctype, pi.name)}'>{pi.name}</a> created")


    def get_expense_account(self):
        company = frappe.defaults.get_user_default("Company")
        account = frappe.db.get_value("Company", company, "default_expense_account")
        if not account:
            account = frappe.db.get_value("Account", {
                "account_type": "Expense",
                "company": company,
                "is_group": 0
            }, "name")
        if not account:
            frappe.throw("No default Expense Account found for the company. Please set it in Company master.")
        return account

    def ensure_item_exists(self, description):
        item_code = frappe.db.get_value("Item", {"item_name": description})
        if not item_code:
            item = frappe.get_doc({
                "doctype": "Item",
                "item_name": description,
                "item_code": description.replace(" ", "-").lower(),
                "item_group": "All Item Groups",
                "stock_uom": "Nos",
                "is_stock_item": 0,
                "disabled": 0
            })
            item.insert(ignore_permissions=True)
            item_code = item.name
        return item_code

    def ensure_customer_exists(self):
        if not frappe.db.exists("Customer", self.party):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": self.party,
                "customer_group": "All Customer Groups",
                "territory": "All Territories"
            })
            customer.insert(ignore_permissions=True)
