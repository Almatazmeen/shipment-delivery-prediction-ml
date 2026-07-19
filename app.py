# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
import joblib
import numpy as np
import pandas as pd
import folium
import shap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# =========================================================
# 1️⃣ CONFIGURATION
# =========================================================
MODEL_PATH = os.path.join('model', 'xgboost_shipment_model.pkl')
SHAP_OUT = os.path.join('static', 'shap', 'shap_summary.png')
MAP_OUT = os.path.join('static', 'maps', 'map.html')
THRESHOLD = 0.711199508182273  # optimal threshold

# SMTP configuration for email alerts
SMTP_CONFIG = {
    "enabled": os.environ.get("SMTP_ENABLED", "True").lower() in ("true", "1", "yes"),
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
    "sender": os.environ.get("SMTP_SENDER"),
    "password": os.environ.get("SMTP_PASSWORD", "").replace(" ", ""),
    "receiver": os.environ.get("SMTP_RECEIVER")
}

DB_PATH = "users.db"

# =========================================================
# 2️⃣ FLASK APP INITIALIZATION
# =========================================================
app = Flask(__name__)
app.secret_key = os.urandom(24)

# =========================================================
# 3️⃣ LOAD MODEL
# =========================================================
model = joblib.load(MODEL_PATH)

# =========================================================
# 4️⃣ SHAP EXPLAINER
# =========================================================
explainer = None
explainer = None
def get_explainer():
    global explainer
    if explainer is None:
        try:
            # Bypass bug in shap parsing new xgboost versions
            if hasattr(model, 'get_booster'):
                explainer = shap.TreeExplainer(model.get_booster())
            else:
                explainer = shap.TreeExplainer(model)
        except Exception:
            explainer = shap.Explainer(model)
    return explainer

# =========================================================
# 5️⃣ EMAIL ALERT HELPER
# =========================================================
def send_alert(subject, html_body):
    if not SMTP_CONFIG["enabled"]:
        return False, "SMTP disabled"
    try:
        msg = MIMEMultipart("alternative")
        msg['Subject'] = subject
        msg['From']    = f"ShipmentSure Alerts <{SMTP_CONFIG['sender']}>"
        msg['To']      = SMTP_CONFIG['receiver']
        msg['Reply-To'] = SMTP_CONFIG['sender']
        msg['X-Mailer'] = 'ShipmentSure v1.0'

        # Plain-text fallback (reduces spam score)
        plain_text = "ShipmentSure Alert: A shipment delay has been predicted. Please check the system for details."
        msg.attach(MIMEText(plain_text, 'plain'))

        # HTML content
        part = MIMEText(html_body, 'html')
        msg.attach(part)

        server = smtplib.SMTP(SMTP_CONFIG['smtp_server'], SMTP_CONFIG['smtp_port'])
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_CONFIG['sender'], SMTP_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        return True, "Sent"
    except Exception as e:
        return False, str(e)

# =========================================================
# 6️⃣ AUTHENTICATION (SQLite + Roles)
# =========================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                   (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    # Default admin
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    ('admin', generate_password_hash('admin123'), 'admin'))
    conn.commit()
    conn.close()

def validate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT password, role FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False, None
    stored_pw, role = row
    if check_password_hash(stored_pw, password):
        return True, role
    return False, None

# initialize DB
init_db()

# =========================================================
# 7️⃣ LOGIN & LOGOUT ROUTES
# =========================================================
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        ok, role = validate_user(u, p)
        if ok:
            session['username'] = u
            session['role'] = role
            flash('✅ Logged in successfully','success')
            return redirect(url_for('index'))
        else:
            flash('❌ Invalid credentials','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out','info')
    return redirect(url_for('login'))

# =========================================================
# 8️⃣ HOME (PROTECTED)
# =========================================================
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# =========================================================
# 9️⃣ ADMIN PAGE (PROTECTED)
# =========================================================
@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash('Admin access required','danger')
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if session.get('role') != 'admin':
        flash('Admin access required','danger')
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            u = request.form['username']
            p = request.form['password']
            r = request.form['role']
            try:
                cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                            (u, generate_password_hash(p), r))
                conn.commit()
                flash('User added successfully', 'success')
            except sqlite3.IntegrityError:
                flash('Username already exists', 'danger')
        elif action == 'delete':
            uid = request.form['user_id']
            cur.execute("SELECT username FROM users WHERE id=?", (uid,))
            row = cur.fetchone()
            if row and row[0] == session['username']:
                flash('Cannot delete your own account', 'danger')
            else:
                cur.execute("DELETE FROM users WHERE id=?", (uid,))
                conn.commit()
                flash('User deleted successfully', 'success')
                
    cur.execute("SELECT id, username, role FROM users")
    users = cur.fetchall()
    conn.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if session.get('role') != 'admin':
        flash('Admin access required','danger')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        SMTP_CONFIG['enabled'] = request.form.get('enabled') == 'on'
        SMTP_CONFIG['receiver'] = request.form.get('receiver')
        flash('Settings updated for this session', 'success')
        
    return render_template('admin_settings.html', config=SMTP_CONFIG)

# =========================================================
# 🔟 PREDICTION ROUTE
# =========================================================
@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    try:
        # ---- Form Data ----
        customer_care_calls = int(request.form['customer_care_calls'])
        customer_rating = int(request.form['customer_rating'])
        cost_of_product = float(request.form['cost_of_product'])
        prior_purchases = int(request.form['prior_purchases'])
        product_importance = request.form['product_importance']
        gender = request.form['gender']
        discount_offered = float(request.form['discount_offered'])
        weight_in_gms = float(request.form['weight_in_gms'])
        warehouse_block = request.form['warehouse_block']
        mode_of_shipment = request.form['mode_of_shipment']

        # ---- Derived Feature ----
        cost_to_weight_ratio = cost_of_product / max(weight_in_gms,1)

        # ---- Categorical Encoding ----
        wh_map = {'A':[0,0,0,0],'B':[1,0,0,0],'C':[0,1,0,0],'D':[0,0,1,0],'E':[0,0,0,1],'F':[0,0,0,0]}
        wh_enc = wh_map.get(warehouse_block, [0,0,0,0])

        mode_map = {'Ship':[1,0],'Air':[0,1],'Road':[0,0]}
        mode_enc = mode_map.get(mode_of_shipment,[0,0])

        importance_map = {'low':0,'medium':1,'high':2}
        product_importance_val = importance_map.get(product_importance.lower(),1)

        gender_map = {'male':1,'female':0}
        gender_val = gender_map.get(gender.lower(),0)

        # ---- Feature Vector ----
        features = [
            customer_care_calls, customer_rating, cost_of_product, prior_purchases,
            product_importance_val, gender_val, discount_offered, weight_in_gms,
            wh_enc[0], wh_enc[1], wh_enc[2], wh_enc[3],
            mode_enc[0], mode_enc[1], cost_to_weight_ratio
        ]

        X = pd.DataFrame([features], columns=[
            'Customer_care_calls','Customer_rating','Cost_of_the_Product','Prior_purchases',
            'Product_importance','Gender','Discount_offered','Weight_in_gms',
            'Warehouse_block_1','Warehouse_block_2','Warehouse_block_3','Warehouse_block_4',
            'Mode_of_Shipment_1','Mode_of_Shipment_2','Cost_to_Weight_ratio'
        ])

        # ---- Prediction ----
        prob = model.predict_proba(X)[0][1]
        binary = int(prob >= THRESHOLD)
        prediction_text = "✅ On-Time Delivery" if binary==1 else "❌ Not Delivered On Time"

        # ---- SHAP ----
        shap_img_file = None
        try:
            import xgboost as xgb
            # XGBoost native SHAP generation bypasses the version mismatch bug completely
            contribs = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)
            shap_values = contribs[0, :-1] # Extract the single instance SHAP values
            plt.figure(figsize=(6,4))
            
            # bar_plot is the correct function for a single instance prediction
            shap.bar_plot(shap_values, feature_names=X.columns.tolist(), show=False)
            
            os.makedirs(os.path.dirname(SHAP_OUT), exist_ok=True)
            plt.savefig(SHAP_OUT, bbox_inches='tight', dpi=150, transparent=True)
            plt.close()
            shap_img_file = os.path.basename(SHAP_OUT)
        except Exception as e:
            print(f"SHAP generation failed: {e}")
            plt.close()

        # ---- Shipment Map ----
        os.makedirs(os.path.dirname(MAP_OUT), exist_ok=True)
        m = folium.Map(location=[20.5937,78.9629], zoom_start=5)
        folium.Marker([28.7041,77.1025], tooltip='Warehouse').add_to(m)
        folium.Marker([19.0760,72.8777], tooltip='Destination').add_to(m)
        color = 'green' if binary == 1 else 'red'
        folium.PolyLine(locations=[[28.7041,77.1025],[19.0760,72.8777]], color=color, weight=4).add_to(m)
        m.save(MAP_OUT)

        # ---- Smart Email Alert ----
        email_status = None
        if binary == 0 and SMTP_CONFIG['enabled']:
            subject = "⚠️ Shipment Delay Alert"
            
            # Professional HTML Template
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <h2 style="color: #d9534f;">Shipment Delay Alert</h2>
                    <p>A shipment has been predicted to be <strong>DELAYED</strong>.</p>
                    <table style="border-collapse: collapse; width: 100%; max-width: 600px; margin-top: 20px;">
                        <tr style="background-color: #f9f9f9;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Probability of Delay</th>
                            <td style="padding: 10px; border: 1px solid #ddd;"><strong>{round(prob * 100, 2)}%</strong></td>
                        </tr>
                        <tr>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Mode of Shipment</th>
                            <td style="padding: 10px; border: 1px solid #ddd;">{mode_of_shipment}</td>
                        </tr>
                        <tr style="background-color: #f9f9f9;">
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Product Importance</th>
                            <td style="padding: 10px; border: 1px solid #ddd;">{product_importance.capitalize()}</td>
                        </tr>
                        <tr>
                            <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Warehouse Block</th>
                            <td style="padding: 10px; border: 1px solid #ddd;">{warehouse_block}</td>
                        </tr>
                    </table>
                    <p style="margin-top: 20px;">Please take appropriate actions.</p>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 12px; color: #999;">This is an automated message from ShipmentSure.</p>
                </body>
            </html>
            """
            
            ok,msg = send_alert(subject, html_body)
            email_status = (ok,msg)

        # ---- Render Result ----
        return render_template(
            'result.html',
            prediction=prediction_text,
            probability=round(prob,3),
            binary=binary,
            shap_img=shap_img_file,
            map_file=os.path.basename(MAP_OUT),
            email_status=email_status
        )
    except Exception as e:
        return render_template(
            'result.html', 
            prediction=f"Error: {e}",
            probability=None,
            binary=None,
            shap_img=None,
            map_file=None,
            email_status=None
        )

# =========================================================
# 🔹 MAP EMBED
# =========================================================
@app.route('/map')
def map_embed():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('map_embed.html', map_file='maps/map.html')

# =========================================================
# 🔹 RUN APP
# =========================================================
if __name__ == '__main__':
    app.run(debug=True)
