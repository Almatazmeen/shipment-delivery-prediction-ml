# ShipmentSure – Predictive Logistics Control Center

ShipmentSure is an AI-powered machine learning application that predicts whether a shipment will arrive on time. It combines predictive analytics with Explainable AI to provide transparent predictions and help identify high-risk shipments.

## Live Demo

https://shipment-delivery-prediction-ml.onrender.com/

> The application is hosted on Render's free tier, so the first load may take a few moments.

## Key Features

- Shipment delivery prediction using XGBoost
- Prediction probability and confidence
- Explainable AI using SHAP
- Automated email alerts for high-risk shipments
- Secure user authentication
- Role-Based Access Control (RBAC)
- Admin dashboard for user and alert management

## Tech Stack

- **Backend:** Python, Flask
- **Machine Learning:** XGBoost
- **Explainable AI:** SHAP
- **Data Processing:** Pandas
- **Database:** SQLite
- **Frontend:** HTML, CSS, Jinja2
- **Security:** Werkzeug Security
- **Email Alerts:** SMTP
- **Deployment:** Render

## How It Works

1. The user logs into the application.
2. Shipment details are entered through the prediction dashboard.
3. The XGBoost model predicts the shipment delivery outcome.
4. SHAP explains which factors influenced the prediction.
5. High-risk shipments can automatically trigger email alerts.
6. Administrators can manage users and alert settings through the Admin Dashboard.

## Run Locally

Clone the repository:

git clone https://github.com/Almatazmeen/shipment-delivery-prediction-ml.git

Install dependencies:

pip install -r requirements.txt

Run the application:

python app.py

Then open:

http://127.0.0.1:5000

## Future Enhancements

- PostgreSQL integration
- Automated model retraining
- REST API development
- CI/CD pipeline
- Docker containerization

## Disclaimer

This project was developed for educational and portfolio purposes. Machine learning predictions should not be used as the sole basis for real-world logistics decisions.
