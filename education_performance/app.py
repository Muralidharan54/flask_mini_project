from flask import Flask, render_template, redirect, url_for, flash, request
import os
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import plotly.express as px
import plotly.utils
import json
from forms import LoginForm, RegistrationForm
from flask_migrate import Migrate
import pandas as pd
from config import MongoDBConfig, PostgresConfig
from models import User, EducationData
from extensions import db
from etl import ETL
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
mongo=PyMongo()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler('education_etl.log', maxBytes=10000, backupCount=1)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(console_handler)

app = Flask(__name__)
app.config.from_object('config.MySQLConfig')  
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'





@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            if user.role=='admin':
                return redirect(url_for('admin_portal'))
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard',methods=['POST','GET'])
@login_required
def dashboard():
    data = EducationData.query.all()
    df = pd.DataFrame([{
        'hours_studied': d.hours_studied,
        'attendance': d.attendance,
        'sleep_hours': d.sleep_hours,
        'physical_activity': d.physical_activity,
        'learning_disabilities': d.learning_disabilities,
        'parental_involvement': d.parental_involvement,
        'parental_education_level': d.parental_education_level,
        'distance_from_home': d.distance_from_home,
        'peer_influence': d.peer_influence,
        'exam_score': d.exam_score
    } for d in data])

    charts = []
    
    fig1 = px.bar(df.groupby('hours_studied').exam_score.mean().reset_index(),
                  x='hours_studied', y='exam_score',
                  title='Hours Studied vs Average Exam Score')
    charts.append(json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig2 = px.bar(df.groupby('attendance').exam_score.mean().reset_index(),
                  x='attendance', y='exam_score',
                  title='Attendance vs Average Exam Score')
    charts.append(json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig3 = px.bar(df.groupby('sleep_hours').exam_score.mean().reset_index(),
                  x='sleep_hours', y='exam_score',
                  title='Sleep Hours vs Average Exam Score')
    charts.append(json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig4 = px.bar(df.groupby('physical_activity').sleep_hours.mean().reset_index(),
                  x='physical_activity', y='sleep_hours',
                  title='Physical Activity vs Average Sleep Hours')
    charts.append(json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig5 = px.bar(df.groupby('learning_disabilities').exam_score.mean().reset_index(),
                  x='learning_disabilities', y='exam_score',
                  title='Learning Disabilities vs Average Exam Score')
    charts.append(json.dumps(fig5, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig6 = px.bar(df.groupby('parental_involvement').exam_score.mean().reset_index(),
                  x='parental_involvement', y='exam_score',
                  title='Parental Involvement vs Average Exam Score')
    charts.append(json.dumps(fig6, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig7 = px.bar(df.groupby('parental_education_level').exam_score.mean().reset_index(),
                  x='parental_education_level', y='exam_score',
                  title='Parental Education Level vs Average Exam Score')
    charts.append(json.dumps(fig7, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig8 = px.bar(df.groupby('distance_from_home').exam_score.mean().reset_index(),
                  x='distance_from_home', y='exam_score',
                  title='Distance from Home vs Average Exam Score')
    charts.append(json.dumps(fig8, cls=plotly.utils.PlotlyJSONEncoder))
    
    fig9 = px.bar(df.groupby('peer_influence').exam_score.mean().reset_index(),
                  x='peer_influence', y='exam_score',
                  title='Peer Influence vs Average Exam Score')
    charts.append(json.dumps(fig9, cls=plotly.utils.PlotlyJSONEncoder))
    
    if current_user.role=='admin':
        return render_template('dashboard.html', charts=charts)
    elif current_user.role=='teacher':
        return render_template('dashboard.html', charts=charts[:2])
    elif current_user.role=='med_asst':
        return render_template('dashboard.html', charts=charts[2:5])
    elif current_user.role=='coordinator':
        return render_template('dashboard.html', charts=charts[5:8])
    return render_template('dashboard.html', charts=charts[8])
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file uploaded.")
        return redirect(url_for('admin_portal'))
    
    file = request.files['file']
    if file.filename == '':
        flash("No selected file.")
        return redirect(url_for('admin_portal'))
    
    if not os.path.exists('./data_sources'):
        os.makedirs('./uploads')
    
    file_path = os.path.join('./data_sources', file.filename)
    file.save(file_path)
    flash("File uploaded successfully.")
    return redirect(url_for('admin_portal'))

@app.route('/etl', methods=['GET','POST'])
def etl():
    etl_process = ETL()

    try:
        logger.info("Starting ETL process")
        data = etl_process.extract_data()
        logger.debug(f"Extracted {len(data)} records")

        transformed_data = etl_process.transformation(data)
        logger.debug(f"Transformed {len(transformed_data)} records")

        etl_process.load_data(transformed_data)
        logger.debug("ETL process completed successfully")
        flash("ETL process completed successfully.")
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        flash(f"ETL process failed: {e}")

    return redirect(url_for('admin_portal'))

@app.route('/admin_portal')
def admin_portal():
    return render_template('admin.html')


@app.route('/switch_database')
@app.route('/switch_database')
@login_required
def switch_database():
    if current_user.role != 'admin':
        flash('Permission denied')
        return redirect(url_for('dashboard'))
    
    current_db = 'mongo' if 'MONGO_URI' in app.config else 'postgresql'
    
    if current_db == 'postgresql':
        app.config.from_object(MongoDBConfig)
        mongo.init_app(app)
        db.session.remove()
        db.dispose() 
        db = None 
        flash('Switched to MongoDB')
    else:
        app.config.from_object(PostgresConfig)
        db.init_app(app)
        flash('Switched to PostgreSQL')

    return redirect(url_for('dashboard'))




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
