import os
from drain_helper import DrainHelper
from episode_mining import EpisodeMining
from flask import Flask, jsonify, render_template, send_from_directory, abort, flash, request, redirect, session, url_for # type: ignore
from flask_wtf import FlaskForm # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from wtforms import StringField, SubmitField, BooleanField, DateTimeField, RadioField, SelectField # type: ignore
from wtforms.validators import DataRequired # type: ignore
import pandas as pd # type: ignore
from datetime import datetime
from werkzeug.utils import secure_filename # type: ignore
from forensic_timeline_helper import ForensicTimelineHelper
from process_mining import ProcessMining


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/download/<filename>', methods=['GET'])
def download_image(filename):
    IMAGE_FOLDER = os.path.join(os.getcwd(), "static", "images")
    return send_from_directory(IMAGE_FOLDER, filename + ".jpeg", as_attachment=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/execute', methods=['POST'])
def execute():
    UPLOAD_FOLDER = '.'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = {'csv'}

    file = request.files.get('file_upload')
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'File must be in CSV format'}), 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    base_filename = os.path.splitext(filename)[0]
    source_filter = request.form.getlist('selected_sources')
    start_datetime = request.form.get('start_date')
    end_datetime = request.form.get('end_date')
    rankdir = 'LR'
    minsup = request.form.get('min_support')

    forensic_timeline = ForensicTimelineHelper()
    drain = DrainHelper()
    episode_mining = EpisodeMining()
    process_mining = ProcessMining()
    
    forensic_timeline.filter_by_request(base_filename, source_filter, start_datetime, end_datetime)
    drain.run(base_filename)

    forensic_timeline.select_columns_used_for_episode_mining(base_filename)
    forensic_timeline.convert_forensic_timeline_into_episode_mining_input_format(base_filename)

    output_filename = episode_mining.run(base_filename, minsup, 'MINEPI+')
    list_of_traces = episode_mining.extract_output_spmf_to_list(output_filename)
    df = episode_mining.create_df_with_case_id(base_filename, list_of_traces)

    event_log = process_mining.format_df_into_pm4py_event_log(df)

    net_heuristics, initial_marking_heuristics, final_marking_heuristics = process_mining.generate_petri_net_heuristics(event_log, base_filename, rankdir)
    net_alpha, initial_marking_alpha, final_marking_alpha = process_mining.generate_petri_net_alpha(event_log, base_filename, rankdir)
    net_inductive, initial_marking_inductive, final_marking_inductive = process_mining.generate_petri_net_inductive_miner(event_log, base_filename, rankdir)
    net_ilp, initial_marking_ilp, final_marking_ilp = process_mining.generate_petri_net_ilp_miner(event_log, base_filename, rankdir)

    evaluation_metrics_heuristics = {
        "precision" : process_mining.get_precision(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics),
        "fitness" : process_mining.get_fitness(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics),
        "generalization" : process_mining.get_generalization(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics),  
        "simplicity" : process_mining.get_simplicity(net_heuristics)
    }

    evaluation_metrics_alpha = {
        "precision" : process_mining.get_precision(event_log, net_alpha, initial_marking_alpha, final_marking_alpha),
        "fitness" : process_mining.get_fitness(event_log, net_alpha, initial_marking_alpha, final_marking_alpha),
        "generalization" : process_mining.get_generalization(event_log, net_alpha, initial_marking_alpha, final_marking_alpha),  
        "simplicity" : process_mining.get_simplicity(net_alpha)
    }

    evaluation_metrics_inductive = {
        "precision" : process_mining.get_precision(event_log, net_inductive, initial_marking_inductive, final_marking_inductive),
        "fitness" : process_mining.get_fitness(event_log, net_inductive, initial_marking_inductive, final_marking_inductive),
        "generalization" : process_mining.get_generalization(event_log, net_inductive, initial_marking_inductive, final_marking_inductive),  
        "simplicity" : process_mining.get_simplicity(net_inductive)
    }

    evaluation_metrics_ilp = {
        "precision" : process_mining.get_precision(event_log, net_ilp, initial_marking_ilp, final_marking_ilp),
        "fitness" : process_mining.get_fitness(event_log, net_ilp, initial_marking_ilp, final_marking_ilp),
        "generalization" : process_mining.get_generalization(event_log, net_ilp, initial_marking_ilp, final_marking_ilp),  
        "simplicity" : process_mining.get_simplicity(net_ilp)
    }

    alignment = process_mining.get_alignment(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics)
    alignment = alignment.replace("\n", "<br>")

    forensic_timeline.remove_files(base_filename, minsup)

    return "sukses"

if __name__ == '__main__':
    app.run(debug=True)