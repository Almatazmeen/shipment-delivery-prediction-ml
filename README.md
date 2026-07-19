# 🚀 ShipmentSure: Predictive Logistics Control Center

ShipmentSure is an advanced, industry-level machine learning application designed to predict supply chain efficiency. It operates as a high-tech "Mission Control" dashboard that allows logistics operators to input shipment parameters and instantly receive an AI-driven probability of whether a package will arrive on time. 

Beyond simple predictions, ShipmentSure features Explainable AI (SHAP) to tell you *why* a decision was made, automated SMTP alert relays for high-risk shipments, dynamic route mapping, and a secure Role-Based Access Control (RBAC) Admin dashboard.

---

## 🛠️ Technology Stack

### Backend & Machine Learning
* **Python 3**: Core programming language.
* **Flask**: Lightweight web framework handling the routing, template rendering, and API logic.
* **XGBoost**: High-performance gradient boosting library used for the core classification model (`xgboost_shipment_model.pkl`).
* **SHAP (Shapley Additive exPlanations)**: Used for Explainable AI (XAI). It breaks down the XGBoost prediction to show exactly which features (e.g., package weight, customer rating) contributed positively or negatively to the outcome.
* **Pandas / Joblib**: Data manipulation and model loading.
* **Folium**: Python library used to generate interactive leaflet maps (`map.html`) showing the theoretical origin/destination of the shipment based on warehouse block.
* **SQLite3**: Lightweight relational database used to store operator credentials securely.

### Frontend
* **HTML5 / Jinja2**: Templating engine for injecting Python variables into the web pages.
* **Vanilla CSS3**: Custom-built "Glassmorphism" dark-mode tech aesthetic. Features CSS variables for theming, CSS grid/flexbox for responsive layouts, and keyframe animations.
* **FontAwesome**: Iconography used throughout the dashboards.

### Infrastructure & Security
* **python-dotenv**: Environment variable management (securing SMTP passwords).
* **Werkzeug Security**: Password hashing (`generate_password_hash`, `check_password_hash`) to ensure plain-text passwords are never stored in the database.
* **smtplib & MIME**: Native Python libraries used to construct and send professional HTML-formatted email alerts via Gmail's SMTP servers.

---

## 📂 Project Structure & Architecture

```text
ShipmentSure/
│
├── app.py                  # Core backend server, routing, and ML execution
├── users.db                # SQLite database storing operator credentials/roles
├── .env                    # Environment variables (SMTP credentials) - NOT COMMITTED
│
├── model/                  
│   └── xgboost_shipment_model.pkl  # The pre-trained XGBoost Classifier
│
├── static/                 
│   ├── css/
│   │   └── style.css       # Core stylesheet (Dark mode dashboard aesthetic)
│   ├── shap/               # Directory where generated SHAP plot images are saved
│   └── maps/               # Directory where generated Folium HTML maps are saved
│
└── templates/              # Jinja2 HTML Templates
    ├── login.html          # Authentication terminal
    ├── index.html          # Main Mission Control input dashboard
    ├── result.html         # Mission Status (Prediction, SHAP, Metrics)
    ├── admin.html          # Admin Control Center hub
    ├── admin_users.html    # Operator management (Add/Delete users)
    └── admin_settings.html # Alert Relay configuration (Toggle emails)
```

---

## ⚙️ Core Functionality & Features

### 1. The Prediction Engine (`/predict`)
Operators input 10 unique logistical parameters (e.g., Warehouse Block, Transit Mode, Prior Purchases, Discount Offered). The Flask backend passes this data to a Pandas DataFrame and feeds it to the XGBoost model. 
* The model returns a binary classification (`0` = Delayed, `1` = On-Time).
* It also returns a probability score (e.g., `99.9%` confidence of on-time delivery).

### 2. Explainable AI (SHAP Visualization)
Instead of operating as a "black box," the application utilizes XGBoost's native `pred_contribs` API to calculate SHAP values. It generates a horizontal bar chart (`shap.bar_plot`) showing exactly how much each variable influenced the AI's final decision. This image is saved dynamically and displayed on the results page.

### 3. Automated Alert Relays (SMTP)
If the AI detects a high risk of delay (binary prediction = `0`), the system automatically triggers an alert protocol. It logs into a secure Gmail SMTP server and sends a professionally formatted HTML email to the designated receiver, warning them of the potential supply chain bottleneck.

### 4. Dynamic Route Mapping
Depending on the selected Origin Warehouse (Blocks A-F), the `generate_map()` function uses **Folium** to plot a visual path from a simulated warehouse coordinates to a destination, generating an interactive HTML map embedded directly into the results flow.

### 5. Role-Based Access Control & Admin Panel
The application is secured by a login portal. Users are verified against `users.db`. 
* **Standard Users** can run predictions.
* **Admins** have access to the `/admin` routes. Here, they can dynamically toggle the global SMTP email alerts on/off without restarting the server, update the receiver email, and manage the operator roster (creating new user accounts and deleting old ones).

---

## 🚀 How to Run & Work on the Project

### Prerequisites
1. Python 3.8+ installed.
2. Required packages: `pip install flask xgboost shap pandas folium python-dotenv`

### Setup Instructions
1. **Clone the Repository** and navigate to the root directory.
2. **Environment Setup**: Create a `.env` file in the root directory and add your SMTP credentials:
   ```env
   SMTP_ENABLED=True
   SMTP_SENDER=your_email@gmail.com
   SMTP_APP_PASSWORD=your_16_digit_app_password
   ```
3. **Database Initialization**: The `users.db` is already created. The default admin credentials are `admin` / `admin123`. 
4. **Run the Server**: 
   ```bash
   python app.py
   ```
5. **Access the App**: Open your browser and navigate to `http://127.0.0.1:5000`.

### Future Development (For New Developers)
If you are taking over this project, here are areas for immediate scaling:
* **Database Migration**: Swap SQLite for PostgreSQL for cloud deployment (e.g., Render, Heroku).
* **Model Retraining Pipeline**: Build an `/admin/retrain` route that accepts CSV uploads to continuously train the XGBoost model on new logistical data.
* **REST API**: Separate the frontend from the backend by converting `app.py` into a pure JSON REST API or GraphQL endpoint.
