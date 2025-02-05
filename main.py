import os
from flask import Flask, render_template, flash, request, redirect, session, url_for # type: ignore
from flask_wtf import FlaskForm # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from wtforms import StringField, SubmitField, BooleanField, DateTimeField, RadioField, SelectField # type: ignore
from wtforms.validators import DataRequired # type: ignore
import json
import logging
import subprocess
import sys
import time
from os.path import dirname
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
import pandas as pd # type: ignore


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

def filter_input_timeline_by_request():
    input_file = '12-search-sql-injection.csv'
    output_file = '12-search-sql-injection-fix.csv'

    data = pd.read_csv(input_file)

    data_filtered = data[
        (data['source_long'] != 'File stat') & 
        ((data['source'] == 'WEBHIST') | (data['source'] == 'log'))
    ]

    selected_data = data_filtered[['datetime', 'message']]
    selected_data_ori = data_filtered[['datetime', 'message', 'source']]

    selected_data['datetime'] = pd.to_datetime(selected_data['datetime'], errors='coerce')
    selected_data_ori['datetime'] = pd.to_datetime(selected_data_ori['datetime'], errors='coerce')

    selected_data.to_csv(output_file, index=False, header=False)
    selected_data_ori.to_csv('12-search-sql-injection-original.csv', index=False)

@app.route('/create-event-abstraction')
def create_event_abstraction_using_drain():
    filter_input_timeline_by_request()
    logger = logging.getLogger(__name__)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')

    in_gz_file = "SSH.tar.gz"
    base_file_name = "12-search-sql-injection"
    in_log_file = base_file_name + "-fix.csv"
    if not os.path.isfile(in_log_file):
        logger.info(f"Downloading file {in_gz_file}")
        p = subprocess.Popen(f"curl https://zenodo.org/record/3227177/files/{in_gz_file} --output {in_gz_file}", shell=True)
        p.wait()
        logger.info(f"Extracting file {in_gz_file}")
        p = subprocess.Popen(f"tar -xvzf {in_gz_file}", shell=True)
        p.wait()

    config = TemplateMinerConfig()
    config.load(f"{dirname(__file__)}/drain3.ini")
    config.profiling_enabled = True
    template_miner = TemplateMiner(config=config)

    line_count = 0

    with open(in_log_file, encoding="utf-8") as f:
        lines = f.readlines()

    start_time = time.time()
    batch_start_time = start_time
    batch_size = 10000

    original_logs = {}

    index_baris = 0
    for line in lines:
        line = line.rstrip()
        tes = line.split(";")
        line = line.partition(": ")[2]
        result = template_miner.add_log_message(line)
        line_count += 1
        if line_count % batch_size == 0:
            time_took = time.time() - batch_start_time
            rate = batch_size / time_took
            logger.info(f"Processing line: {line_count}, rate {rate:.1f} lines/sec, "
                        f"{len(template_miner.drain.clusters)} clusters so far.")
            batch_start_time = time.time()

        if result["change_type"] != "none":
            result_json = json.dumps(result)
            logger.info(f"Input ({line_count}): {line}")
            logger.info(f"Result: {result_json}")

        original_logs[index_baris] = result['cluster_id']
        index_baris += 1

    sorted_clusters = sorted(template_miner.drain.clusters, key=lambda it: it.size, reverse=True)

    data_result = []
    result_drain = {}

    for cluster in sorted_clusters:
        cluster_id = cluster.cluster_id
        size = cluster.size
        template = cluster.get_template()
        line_id_original = [(key+1) for key, value in original_logs.items() if value == cluster_id]
        line_id_original.sort()
        line_id_original = ",".join(map(str, line_id_original))

        row = {
            "cluster_id": cluster_id, 
            "cluster_size": size,
            "abstract_message": template,
            "line_id_original": line_id_original
        }

        data_result.append(row)

        result_drain[cluster_id] = {
            "cluster_size": size,
            "abstract_message": template, 
        }

    df = pd.DataFrame(data_result)
    df.to_csv(base_file_name + "-event-abstraction.csv", index=False)

    df_ori = pd.read_csv(base_file_name + '-original.csv')
    df_ori['cluster_id'] = None 
    df_ori['abstract_message'] = None 

    for i in range(len(df_ori)):
        cluster_id_baris = original_logs[i]
        df_ori['cluster_id'][i] = cluster_id_baris

        abstract_message = result_drain[cluster_id_baris]["abstract_message"]

        if abstract_message == "":
            abstract_message = df_ori['message'][i]

        df_ori['abstract_message'][i] = abstract_message

    df_ori = df_ori[['datetime', 'cluster_id', 'source', 'message', 'abstract_message']] 

    df_ori.to_csv(base_file_name + "-mapping.csv", index=False)

    print("Prefix Tree:")
    # print(dict(sorted(original_logs.items())))
    template_miner.drain.print_tree()

    template_miner.profiler.report(0)
    return "<p1>Success</p1>"



if __name__ == '__main__':
    app.run(debug=True)