import pandas as pd
import sqlite3
from flask import Flask, render_template, request, jsonify, url_for
import joblib
import requests

# Path to the SQLite database and model file
DB_PATH = 'patients_data.db'


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
    patients_list = [dict(row) for row in patients]
    return render_template('patients_list.html', patients=patients_list)

# Route to display visits of a specific patient
@app.route('/patient-visits/<int:patient_id>')
def patient_visits(patient_id):
    conn = get_db_connection()
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
    visits_list = [dict(row) for row in visits]
    return render_template('patient_visits.html', patient_id=patient_id, visits=visits_list)

# Route to display proteins for a specific visit and predict UPDRS scores
@app.route('/patient/<int:patient_id>/visit/<string:visit_id>', methods=['GET', 'POST'])
def visit_proteins(patient_id, visit_id):
    conn = get_db_connection()
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
    proteins_data = conn.execute(query, (patient_id, visit_id, patient_id, visit_id, patient_id, visit_id, patient_id, visit_id)).fetchone()
    conn.close()

    if not proteins_data:
        return "No protein data found for this visit", 404

    protein_values = proteins_data[10:]
    protein_columns = proteins_data.keys()[10:]
    input_data = pd.DataFrame([protein_values], columns=protein_columns)

    if request.method == 'POST':
        # Parse the selected model from the request
        data = request.get_json()
        selected_model = data.get('model')

        # Map models to their file paths
        model_paths = {
            'linear': 'best_linear_regression_model.pkl',
            'random_forest': 'best_random_forest_model.pkl',
            'svr': 'best_svr_model.pkl'
        }

        # Load the selected model and feature names
        model_path = model_paths.get(selected_model)
        if not model_path:
            return jsonify({'error': 'Invalid model selected'}), 400

        model, feature_names = joblib.load(model_path)

        # Align input data with the feature names
        input_data = input_data.reindex(columns=feature_names, fill_value=0)

        # Predict UPDRS scores
        try:
            predicted_updrs = model.predict(input_data)
            scores = {
                'updrs_1': float(predicted_updrs[0][0]),
                'updrs_2': float(predicted_updrs[0][1]),
                'updrs_3': float(predicted_updrs[0][2]),
                'updrs_4': float(predicted_updrs[0][3])
            }
            return jsonify({'scores': scores})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Default behavior for GET requests (rendering the page)
    protein_data = {column: value for column, value in zip(protein_columns, protein_values)}

    # Provide a placeholder for UPDRS scores initially
    updrs_scores = {'updrs_1': 0, 'updrs_2': 0, 'updrs_3': 0, 'updrs_4': 0}

    return render_template(
        'proteins.html',
        patient_id=patient_id,
        visit_id=visit_id,
        protein_data=protein_data,
        updrs_scores=updrs_scores
    )


# Function to fetch and parse protein information
def protein_information(response_text):
    lines = response_text.strip().split('\n')
    protein_info = {
        'ID': '',
        'Accession': '',
        'ProteinName': '',
        'Organism': '',
        'Function': '',
        'DiseaseInvolvement': ''
    }
    reading_function = False
    reading_disease = False

    for line in lines:
        if line.startswith("ID   "):
            protein_info['ID'] = line.split()[1]
        elif line.startswith("AC   "):
            protein_info['Accession'] = line.split()[1].rstrip(';')
        elif 'RecName: Full=' in line:
            protein_info['ProteinName'] = line.split('Full=')[1].split(';')[0].strip()
        elif line.startswith("OS   "):
            protein_info['Organism'] = line.split('OS   ')[1].rstrip('.')
        elif line.startswith("CC   -!- FUNCTION:"):
            reading_function = True
            protein_info['Function'] = line[19:].strip()
        elif reading_function and line.startswith("CC       "):
            protein_info['Function'] += ' ' + line.strip("CC   ")
        elif not line.startswith("CC       ") and reading_function:
            reading_function = False
        elif line.startswith("CC   -!- DISEASE:"):
            reading_disease = True
            protein_info['DiseaseInvolvement'] = line[19:].strip()
        elif reading_disease and line.startswith("CC       "):
            protein_info['DiseaseInvolvement'] += ' ' + line.strip()
        elif not line.startswith("CC       ") and reading_disease:
            reading_disease = False

    return protein_info

# Route to display protein annotation
@app.route('/protein/<proteinId>/annotation', methods=['GET'])
def protein_annotation(proteinId):
    try:
        url = f"https://www.uniprot.org/uniprot/{proteinId}.txt"
        response = requests.get(url)
        response.raise_for_status()
        protein_info = protein_information(response.text)

        if not protein_info.get('ID'):
            protein_info = {}

        protein_info['IsParkinsonRelated'] = 'Parkinson' in protein_info.get('DiseaseInvolvement', '')
        return render_template('proteins_annotation.html', protein_info=protein_info)

    except requests.HTTPError:
        return render_template('proteins_annotation.html', protein_info={})

    except Exception:
        return render_template('proteins_annotation.html', protein_info={})

# Route to display variant viewer page for a given accession
@app.route('/variant_viewer/<accession>', methods=['GET'])
def variant_viewer(accession):
    return render_template('variant_viewer.html', accession=accession)

# Specified order of amino acids for y-axis
amino_acids = ['*', 'd', 'P', 'W', 'Y', 'F', 'H', 'K', 'R', 'Q', 'E', 'N', 'D', 'M', 'C', 'T', 'S', 'I', 'L', 'V', 'A', 'G']

# Types that qualify a variant as a "Predicted consequence"
predicted_consequence_types = {'missense', 'nonsense', 'frameshift', 'inframe'}

# Map clinical significance to colors
color_discrete_map = {
    'likely pathogenic or pathogenic': 'red',
    'predicted consequence': 'blue',
    'likely benign or benign': 'green',
    'uncertain significance': 'cyan',
    'unknown': 'grey'
}

# Function to fetch variants by accession from UniProt
def fetch_uniprot_variants(accession):
    url = f"https://www.ebi.ac.uk/proteins/api/variation/{accession}?format=json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def categorize_variant(variant):
    clinical_significance = variant.get('clinicalSignificances', [])
    if clinical_significance:
        significance_type = clinical_significance[0].get('type', '').lower()
        if "pathogenic" in significance_type:
            return "likely pathogenic or pathogenic"
        elif "benign" in significance_type:
            return "likely benign or benign"
        elif "uncertain" in significance_type:
            return "uncertain significance"
    consequence_type = variant.get('consequenceType', '').lower()
    if consequence_type in predicted_consequence_types:
        return "predicted consequence"
    return "unknown"

def parse_variants(json_data):
    variants = []
    for variant in json_data.get('features', []):
        if variant.get('type') == 'VARIANT':
            category = categorize_variant(variant)
            color = color_discrete_map.get(category, 'grey')
            provenance_sources = {location.get('source') for location in variant.get('locations', []) if location.get('source')}
            provenance = ', '.join(provenance_sources) if provenance_sources else 'N/A'
            wild_type = variant.get('wildType', '')
            alternative_sequence = variant.get('alternativeSequence', '')
            formatted_change = f"{wild_type}>{alternative_sequence}" if wild_type and alternative_sequence else 'N/A'
            
            variants.append({
                'variant_id': variant.get('xrefs', [{}])[0].get('id', 'N/A'),
                'position': int(variant.get('begin', 0)),
                'change': alternative_sequence,
                'formatted_change': formatted_change,
                'description': variant.get('descriptions', [{}])[0].get('value', 'No description') if 'descriptions' in variant else 'N/A',
                'clinical_significance': category,
                'provenance': provenance,
                'color': color
            })
    return variants

# Endpoint to get variants based on accession
@app.route('/get_variants', methods=['POST'])
def get_variants():
    accession = request.form['accession'].strip()
    try:
        json_data = fetch_uniprot_variants(accession)
        variants = parse_variants(json_data)
        return jsonify({'variant_data': variants, 'amino_acids': amino_acids})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/home')
def home():
    return render_template('home.html')

from werkzeug.utils import secure_filename
import os

# Define the upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/add-visit/<int:patient_id>', methods=['POST'])
def add_visit(patient_id):
    try:
        # Retrieve form data
        visit_month = request.form['visit_month']
        proteins_file = request.files['proteins_file']
        peptides_file = request.files['peptides_file']

        # Save files securely
        proteins_filename = secure_filename(proteins_file.filename)
        peptides_filename = secure_filename(peptides_file.filename)
        proteins_file_path = os.path.join(app.config['UPLOAD_FOLDER'], proteins_filename)
        peptides_file_path = os.path.join(app.config['UPLOAD_FOLDER'], peptides_filename)
        proteins_file.save(proteins_file_path)
        peptides_file.save(peptides_file_path)

        # Generate a unique visit ID
        visit_id = f"{patient_id}_{visit_month}"

        # Insert visit data into the t_plus_0 table (if necessary)
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO t_plus_0 (visit_id, patient_id, visit_month)
            VALUES (?, ?, ?)
            """,
            (visit_id, patient_id, visit_month),
        )

        # Insert file data into the visit_files table
        conn.execute(
            """
            INSERT INTO visit_files (visit_id, proteins_file, peptides_file)
            VALUES (?, ?, ?)
            """,
            (visit_id, proteins_filename, peptides_filename),
        )

        conn.commit()
        conn.close()

        return jsonify({'message': 'Visit added successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
