import os
from drain_helper import DrainHelper
from episode_mining import EpisodeMining
from flask import Flask, render_template, flash, request, redirect, session, url_for # type: ignore
from flask_wtf import FlaskForm # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from wtforms import StringField, SubmitField, BooleanField, DateTimeField, RadioField, SelectField # type: ignore
from wtforms.validators import DataRequired # type: ignore
import pandas as pd # type: ignore
from datetime import datetime

from forensic_timeline_helper import ForensicTimelineHelper
from process_mining import ProcessMining


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite') 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db  = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"User {self.name}"

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/execute')
def execute():
    forensic_timeline = ForensicTimelineHelper()
    drain = DrainHelper()
    episode_mining = EpisodeMining()
    process_mining = ProcessMining()

    base_filename = '12-search-sql-injection'
    source_filter = ['WEBHIST', 'LOG']
    start_datetime = ''
    end_datetime = ''
    rankdir = 'LR'
    minsup = 1
    
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

    return evaluation_metrics_ilp

if __name__ == '__main__':
    app.run(debug=True)