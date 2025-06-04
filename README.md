# 📄 Invoice OCR App for ERPNext

Automatically extract invoice data from scanned **PDF** or **image** files and generate Sales or Purchase Invoices in ERPNext using Tesseract OCR.

---

## 🚀 Features

- 🔍 OCR extraction using `pytesseract` from PDF or image
- 📄 Parses invoice number, date, line items, and total
- 🧾 Creates:
  - ✅ Sales Invoice (for Customer)
  - ✅ Purchase Invoice (for Supplier)
- 📦 Automatically creates Items if not found
- 🔄 Dynamic Party Link (Customer or Supplier)
- 📂 JSON preview of extracted data for audit

---

## 📁 Doctypes

### `Invoice Upload`

| Field           | Type          | Description                              |
|------------------|---------------|------------------------------------------|
| Party Type       | Select         | Customer / Supplier                      |
| Party            | Dynamic Link   | Links to Customer or Supplier            |
| File             | Attach         | Upload scanned invoice file              |
| OCR Status       | Select         | Pending / Processing / Extracted / Failed |
| Extracted Data   | Code           | Raw JSON preview of OCR results          |
| Create Invoice   | Button         | Manually trigger invoice creation        |

---

## ⚙️ Full Installation Guide

### ✅ 1. Prerequisites

Install required system packages:

```bash

sudo apt update
sudo apt install -y poppler-utils tesseract-ocr

cd ~/frappe-bench/apps
bench get-app https://github.com/YOUR-USERNAME/invoice_ocr.git

# Activate your Frappe virtual environment
source ~/frappe-bench/env/bin/activate

# Install required Python libraries
pip install -r invoice_ocr/requirements.txt

# Or manually:

pip install pytesseract pdf2image Pillow PyPDF2

# 4. Install the app on your site

cd ~/frappe-bench
bench new-site invoice_ocr
bench --site invoice_ocr install-app invoice_ocr
bench migrate
bench restart
