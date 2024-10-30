import pandas as pd
import sqlite3
from flask import Flask, render_template
import joblib

# Path to the SQLite database
DB_PATH = 'patients_data.db'

# Load the trained model from the file
multi_output_model = joblib.load('multi_output_updrs_model.pkl')

# Flask application setup
app = Flask(__name__)

# Function to get a new database connection
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enables access to row columns by name
    return conn

# Home route - Doctor's profile page
@app.route('/')
def index():
    doctor = {
        'name': 'Dr. Jane Doe',
        'specialization': 'Parkinson',
        'experience': 10,
        'email': 'janedoe@example.com'
    }
    return render_template('index.html', doctor=doctor)

# Route for list of patients (limited to 10 patients)
@app.route('/doctor-patients')
def doctor_patients():
    conn = get_db_connection()
    
    # Query to retrieve 10 unique patient IDs from the tables
    query = """
    SELECT DISTINCT patient_id 
    FROM (
        SELECT patient_id FROM t_plus_0
        UNION
        SELECT patient_id FROM t_plus_6
        UNION
        SELECT patient_id FROM t_plus_12
        UNION
        SELECT patient_id FROM t_plus_24
    ) 
    LIMIT 10
    """
    
    patients = conn.execute(query).fetchall()
    conn.close()

    # Convert rows to a list of dictionaries for the template
    patients_list = [dict(row) for row in patients]

    return render_template('patients_list.html', patients=patients_list)

# Route to display proteins for a specific visit and predict UPDRS scores
@app.route('/patient/<int:patient_id>/visit/<string:visit_id>')
def visit_proteins(patient_id, visit_id):
    conn = get_db_connection()

    # Query to retrieve all columns for the patient_id and visit_id from each table
    query = """
    SELECT * 
    FROM t_plus_0 WHERE patient_id = ? AND visit_id = ?
    UNION ALL
    SELECT * 
    FROM t_plus_6 WHERE patient_id = ? AND visit_id = ?
    UNION ALL
    SELECT * 
    FROM t_plus_12 WHERE patient_id = ? AND visit_id = ?
    UNION ALL
    SELECT * 
    FROM t_plus_24 WHERE patient_id = ? AND visit_id = ?
    """

    # Execute the query and fetch all data
    proteins_data = conn.execute(query, (patient_id, visit_id, patient_id, visit_id, patient_id, visit_id, patient_id, visit_id)).fetchone()
    conn.close()

    if proteins_data:
        # Extract protein data starting from the 11th column
        protein_values = proteins_data[10:]  # Index 10 and beyond are the protein values
        protein_columns = proteins_data.keys()[10:]  # Extract protein column names dynamically

        # Convert to DataFrame for prediction
        input_data = pd.DataFrame([protein_values], columns=protein_columns)
        predicted_updrs = multi_output_model.predict(input_data)

        # Prepare the data for rendering in the template
        protein_data = {column: value for column, value in zip(protein_columns, protein_values)}
        updrs_scores = {
            'updrs_1': predicted_updrs[0][0],
            'updrs_2': predicted_updrs[0][1],
            'updrs_3': predicted_updrs[0][2],
            'updrs_4': predicted_updrs[0][3]
        }

        return render_template(
            'proteins.html',
            patient_id=patient_id,
            visit_id=visit_id,
            protein_data=protein_data,
            updrs_scores=updrs_scores
        )

    return "No protein data found for this visit", 404

# Route to display visits of a specific patient
@app.route('/patient-visits/<int:patient_id>')
def patient_visits(patient_id):
    conn = get_db_connection()

    # Query to retrieve visits for the specific patient from all tables
    query = """
    SELECT visit_id, visit_month 
    FROM (
        SELECT visit_id, visit_month FROM t_plus_0 WHERE patient_id = ?
        UNION
        SELECT visit_id, visit_month FROM t_plus_6 WHERE patient_id = ?
        UNION
        SELECT visit_id, visit_month FROM t_plus_12 WHERE patient_id = ?
        UNION
        SELECT visit_id, visit_month FROM t_plus_24 WHERE patient_id = ?
    )
    ORDER BY visit_month
    """
    
    visits = conn.execute(query, (patient_id, patient_id, patient_id, patient_id)).fetchall()
    conn.close()

    # Convert rows to a list of dictionaries for the template
    visits_list = [dict(row) for row in visits]

    return render_template('patient_visits.html', patient_id=patient_id, visits=visits_list)


# Main function to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)