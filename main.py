import os
from drain_helper import DrainHelper
from flask import Flask, render_template, flash, request, redirect, session, url_for # type: ignore
from flask_wtf import FlaskForm # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from wtforms import StringField, SubmitField, BooleanField, DateTimeField, RadioField, SelectField # type: ignore
from wtforms.validators import DataRequired # type: ignore
import pandas as pd # type: ignore
from datetime import datetime

from forensic_timeline_helper import ForensicTimelineHelper


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
    
    forensic_timeline.filter_by_request()
    drain.run()
    return "<p1>Sukses</p1>"

if __name__ == '__main__':
    app.run(debug=True)