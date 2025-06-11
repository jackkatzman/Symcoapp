# Symco Quote App

A custom-built quoting system for Symco Kitchens. This web-based tool lets you generate quotes, invoices, and full PDF presentation packets for kitchen cabinetry jobs.

---

## 🚀 Features

- Add cabinets by SKU, finish, quantity, and hinge side
- Upload saved quotes via JSON
- Smart pricing logic with markup, shipping, discounts, and payments
- Custom line items for labor or extras
- Auto-calculated totals and balance
- Beautiful PDF export with company branding
- Editable disclaimers and invoice toggles
- Future support for scheduling, file attachments, and AI layout

---

## 🛠️ Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/jackkatzman/Symcoapp.git
   cd Symcoapp
   ```

2. Install dependencies:
   ```bash
   pip install flask pandas reportlab pillow
   ```

3. Place these files in the project folder:
   - `pricelist.xlsx` — your cabinet price list
   - `finishes.csv` — mapping of finish codes to names
   - `static/logo.png` — your company logo

4. Run the app:
   ```bash
   python symco_flask_app.py
   ```

5. Open browser to:
   ```
   http://localhost:5000
   ```

---

## 📦 Folder Structure

```
SymcoWebApp/
├── symco_flask_app.py
├── quote.html
├── README.md
├── pricelist.xlsx
├── finishes.csv
├── static/
│   └── logo.png
└── templates/
    └── quote.html
```

---

## 🤝 Special Thanks

Massive shout-out to **Yanky**, who happens to be the smartest guy I know.

Without his brainpower and big zchusim, this project would still be stuck at `SyntaxError`.  
If it works — he probably touched it. If it’s broken — I probably did.

— Jack @ Symco Kitchens

---

## 📄 License

This project is private and proprietary to Symco Kitchens. All rights reserved.
