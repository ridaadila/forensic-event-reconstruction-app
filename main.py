import os
from drain_helper import DrainHelper
from episode_mining import EpisodeMining
from flask import Flask, jsonify, render_template, send_from_directory, request # type: ignore
from werkzeug.utils import secure_filename # type: ignore
from forensic_timeline_helper import ForensicTimelineHelper
from process_mining import ProcessMining
import pandas as pd # type: ignore

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
    try:
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
        
        start_datetime = pd.to_datetime(start_datetime, errors='coerce')
        end_datetime = pd.to_datetime(end_datetime, errors='coerce')

        start_date_str = start_datetime.strftime('%Y-%m-%d') if not pd.isna(start_datetime) else None
        end_date_str = end_datetime.strftime('%Y-%m-%d') if not pd.isna(end_datetime) else None

        start_time_str = start_datetime.strftime('%H:%M:%S') if not pd.isna(start_datetime) else None
        end_time_str = end_datetime.strftime('%H:%M:%S') if not pd.isna(end_datetime) else None

        rankdir = 'LR'
        minsup = request.form.get('min_support')

        forensic_timeline = ForensicTimelineHelper()
        drain = DrainHelper()
        episode_mining = EpisodeMining()
        process_mining = ProcessMining()
        
        forensic_timeline.filter_by_request(base_filename, source_filter, start_date_str, end_date_str, start_time_str, end_time_str)
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

        evaluation_metrics = {
            "Alpha Miner" : {
                "Precision" : process_mining.get_precision(event_log, net_alpha, initial_marking_alpha, final_marking_alpha),
                "Fitness" : process_mining.get_fitness(event_log, net_alpha, initial_marking_alpha, final_marking_alpha),
                "Generalization" : process_mining.get_generalization(event_log, net_alpha, initial_marking_alpha, final_marking_alpha),  
                "Simplicity" : process_mining.get_simplicity(net_alpha)
            }, 
            "Heuristics Miner" : {
                "Precision" : process_mining.get_precision(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics),
                "Fitness" : process_mining.get_fitness(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics),
                "Generalization" : process_mining.get_generalization(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics),  
                "Simplicity" : process_mining.get_simplicity(net_heuristics)
            },
            "Inductive Miner" : {
                "Precision" : process_mining.get_precision(event_log, net_inductive, initial_marking_inductive, final_marking_inductive),
                "Fitness" : process_mining.get_fitness(event_log, net_inductive, initial_marking_inductive, final_marking_inductive),
                "Generalization" : process_mining.get_generalization(event_log, net_inductive, initial_marking_inductive, final_marking_inductive),  
                "Simplicity" : process_mining.get_simplicity(net_inductive)
            },
            "ILP Miner" : {
                "Precision" : process_mining.get_precision(event_log, net_ilp, initial_marking_ilp, final_marking_ilp),
                "Fitness" : process_mining.get_fitness(event_log, net_ilp, initial_marking_ilp, final_marking_ilp),
                "Generalization" : process_mining.get_generalization(event_log, net_ilp, initial_marking_ilp, final_marking_ilp),  
                "Simplicity" : process_mining.get_simplicity(net_ilp)
            }
        }

        alignments = {
            "Alpha Miner": process_mining.get_alignment(event_log, net_alpha, initial_marking_alpha, final_marking_alpha),
            "Heuristics Miner": process_mining.get_alignment(event_log, net_heuristics, initial_marking_heuristics, final_marking_heuristics),
            "Inductive Miner": process_mining.get_alignment(event_log, net_inductive, initial_marking_inductive, final_marking_inductive),  
            "ILP Miner": process_mining.get_alignment(event_log, net_ilp, initial_marking_ilp, final_marking_ilp)
        }

        list_of_images = {
            "Alpha Miner" : base_filename + '-petri-net-alpha.jpeg',
            "Heuristics Miner" : base_filename + '-petri-net-heuristics.jpeg',
            "Inductive Miner" : base_filename + '-petri-net-inductive-miner.jpeg',
            "ILP Miner" : base_filename + '-petri-net-ilp-miner.jpeg',
        }

        forensic_timeline.remove_files(base_filename, minsup)

        return render_template('show.html', images=list_of_images, evaluation_metrics=evaluation_metrics, alignments=alignments)

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
if __name__ == '__main__':
    app.run(debug=True)