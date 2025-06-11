from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
import os
import textwrap
from datetime import datetime
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

app = Flask(__name__)

pricelist = pd.read_excel("pricelist.xlsx")
pricelist["ITEM #"] = pricelist["ITEM #"].astype(str).str.upper()
finishes = pd.read_csv("finishes.csv").set_index("Code")["Style Name"].to_dict()

@app.route("/autocomplete")
def autocomplete():
    term = request.args.get("term", "").strip().upper()
    matches = pricelist["ITEM #"].dropna().unique()
    suggestions = [sku for sku in matches if sku.startswith(term)][:10]
    return jsonify(suggestions)

@app.route("/", methods=["GET", "POST"])
def quote():
    if request.method == "POST":
        customer = {
            "name": request.form.get("customer_name", ""),
            "phone": request.form.get("customer_phone", ""),
            "email": request.form.get("customer_email", "")
        }
        bill_to = {k: request.form.get(f"bill_{k}", "") for k in ["name", "address", "city", "state", "zip", "phone"]}
        ship_to = {k: request.form.get(f"ship_{k}", "") for k in ["name", "address", "city", "state", "zip", "phone"]}

        try:
            markup = float(request.form.get("markup", 1.0))
            assembly = float(request.form.get("assembly", 0.0))
            shipping = float(request.form.get("shipping", 0.0))
            discount = float(request.form.get("discount", 0.0))
            discount_type = request.form.get("discount_type", "%")
            payment = float(request.form.get("payment", 0.0))
        except:
            markup = 1.0
            assembly = shipping = discount = payment = 0.0
            discount_type = "%"

        items = request.form.getlist("item[]")
        finishes_selected = request.form.getlist("finish[]")
        qtys = request.form.getlist("qty[]")
        hinges = request.form.getlist("hinge[]")

        custom_descs = request.form.getlist("custom_desc[]")
        custom_prices = request.form.getlist("custom_price[]")
        custom_qtys = request.form.getlist("custom_qty[]")

        quote_data = []
        subtotal = 0

        unit_prices = request.form.getlist("unit_price[]")
        for item, finish, qty, hinge, form_unit_price in zip(items, finishes_selected, qtys, hinges, unit_prices):
            item = item.strip().upper()
            try:
                qty = int(qty)
            except:
                continue

            row = pricelist[pricelist["ITEM #"] == item]
            if not row.empty and finish in row.columns and pd.notna(row[finish].values[0]) and str(row[finish].values[0]).strip() not in ["", "-"]:
                base_price = float(row[finish].values[0])
                unit_price = (base_price + assembly) * markup
            else:
                try:
                    unit_price = float(form_unit_price)
                except:
                    continue

            line_total = qty * unit_price
            subtotal += line_total
            desc = item
            quote_data.append((item, desc, finishes.get(finish, finish), qty, unit_price, line_total, hinge))

        for desc, price, qty in zip(custom_descs, custom_prices, custom_qtys):
            if not desc.strip():
                continue
            try:
                price = float(price)
                qty = int(qty)
            except:
                continue
            line_total = price * qty
            subtotal += line_total
            quote_data.append(("CUSTOM", desc, "Custom", qty, price, line_total, "N/A"))

        discount_amount = (discount / 100.0 * subtotal) if discount_type == "%" else discount
        grand_total = subtotal + shipping - discount_amount
        balance = grand_total - payment

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50

        try:
            from PIL import Image
            logo_path = "static/logo.png"
            if os.path.exists(logo_path):
                logo_pil = Image.open(logo_path).convert("RGB")
                logo_reader = ImageReader(logo_pil)
                c.drawImage(logo_reader, 40, y - 80, width=120, height=120, mask='auto')
        except:
            pass

        c.setFont("Helvetica-Bold", 16)
        c.drawRightString(width - 40, y, "Symco Kitchens")
        c.setFont("Helvetica", 10)
        c.drawRightString(width - 40, y - 15, "6479 US 9N, Howell, NJ 07731")
        c.drawRightString(width - 40, y - 30, "Phone: 732-800-1299")
        c.drawRightString(width - 40, y - 45, "jack@symcousa.com")
        c.drawRightString(width - 40, y - 60, "www.symcokitchens.com")
        y -= 90

        now = datetime.now()
        quote_number = f"Q{now.strftime('%Y%m%d-%H%M')}"
        custom_name = request.form.get("custom_filename", "").strip().replace(" ", "-") or customer['name'].split()[0]

        c.drawString(50, y, f"Quote #: {quote_number}")
        c.drawString(250, y, now.strftime("%B %d, %Y"))
        y -= 25

        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Bill To:")
        c.drawString(250, y, "Ship To:")
        y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(50, y, bill_to['name'])
        c.drawString(250, y, ship_to['name'])
        y -= 15
        c.drawString(50, y, bill_to['address'])
        c.drawString(250, y, ship_to['address'])
        y -= 15
        c.drawString(50, y, f"{bill_to['city']}, {bill_to['state']} {bill_to['zip']}")
        c.drawString(250, y, f"{ship_to['city']}, {ship_to['state']} {ship_to['zip']}")
        y -= 15
        c.drawString(50, y, f"Phone: {bill_to['phone']}")
        c.drawString(250, y, f"Phone: {ship_to['phone']}")
        y -= 25

        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Qty")
        c.drawString(80, y, "SKU")
        c.drawString(140, y, "Description")
        c.drawString(410, y, "Hinge")
        c.drawString(330, y, "Finish")
        c.drawString(470, y, "Unit Price")
        c.drawString(530, y, "Total")
        y -= 15
        c.setFont("Helvetica", 9)

        for item, desc, finish, qty, unit, line_total, hinge in quote_data:
            wrapped = textwrap.wrap(desc, width=40)
            c.drawString(40, y, str(qty))
            c.drawString(80, y, item)
            c.drawString(140, y, wrapped[0])
            c.drawString(410, y, hinge)
            c.drawString(330, y, finish)
            c.drawString(470, y, f"${unit:.2f}")
            c.drawString(530, y, f"${line_total:.2f}")
            y -= 15
            for extra_line in wrapped[1:]:
                c.drawString(140, y, extra_line)
                y -= 15
            y -= 10

        c.setFont("Helvetica-Bold", 10)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(400, y, "Subtotal:")
        c.drawRightString(width - 50, y, f"${subtotal:.2f}")
        y -= 15
        c.drawString(400, y, "Shipping:")
        c.drawRightString(width - 50, y, f"${shipping:.2f}")
        y -= 15
        c.drawString(400, y, "Discount:")
        c.drawRightString(width - 50, y, f"-${discount_amount:.2f}")
        y -= 15
        c.drawString(400, y, "Grand Total:")
        c.drawRightString(width - 50, y, f"${grand_total:.2f}")
        y -= 15
        c.drawString(400, y, "Payment:")
        c.drawRightString(width - 50, y, f"${payment:.2f}")
        y -= 15
        c.drawString(400, y, "Balance:")
        c.drawRightString(width - 50, y, f"${balance:.2f}")
        y -= 50

        c.setFont("Helvetica-Oblique", 9)
        c.drawString(50, y, "Disclaimer: All quotes valid for 30 days.")
        c.save()
        buffer.seek(0)

        try:
            os.makedirs("C:/Users/jkatzman3/Dropbox/KITCHEN ORDERS/QUOTES/1 quotes from webapp/saves", exist_ok=True)
            import json
            quote_items = []
            for item, desc, finish, qty, unit, line_total, hinge in quote_data:
                quote_items.append({
                    "sku": item,
                    "description": desc,
                    "finish": finish,
                    "qty": qty,
                    "hinge": hinge,
                    "unit_price": unit,
                    "line_total": line_total
                })
            data = {
                "quote_number": quote_number,
                "customer": customer,
                "bill_to": bill_to,
                "ship_to": ship_to,
                "quote_data": quote_items,
                "markup": markup,
                "assembly": assembly,
                "subtotal": subtotal,
                "shipping": shipping,
                "discount": discount,
                "discount_type": discount_type,
                "grand_total": grand_total,
                "payment": payment,
                "balance": balance,
                "timestamp": str(datetime.now())
            }
            json_path = f"C:/Users/jkatzman3/Dropbox/KITCHEN ORDERS/QUOTES/1 quotes from webapp/saves/{quote_number}_{custom_name}.json"
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("❌ JSON save failed:", e)

        return send_file(buffer, as_attachment=True, download_name=f"{quote_number}_{custom_name}.pdf", mimetype='application/pdf')

    return render_template("quote.html", finishes=finishes)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")