from flask import Flask, render_template, redirect, url_for, flash, request
import os
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import plotly.express as px
import plotly.utils
import json
from forms import LoginForm, RegistrationForm
from flask_migrate import Migrate
import pandas as pd
from config import MySQLConfig, PostgresConfig
from models import User, RealEstateData
from extensions import db
from etl import RealEstateETL
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler('real_estate_etl.log', maxBytes=10000, backupCount=1)
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

def avg_val(col_name1, df, col_name2):
        x_axis = set(df[col_name1])
        d1, d = dict(), dict()
        for i in x_axis:
            d[i] = 0
            d1[i] = 0
        for i in df.index:
            d[df[col_name1][i]] += df[col_name2][i]
            d1[df[col_name1][i]] += 1
        for i in d.keys():
            d[i] /= d1[i]
        return d

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
                return redirect(url_for('admin_dashboard'))
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

@app.route('/dashboard',methods=['GET', 'POST'])
@login_required
def dashboard():
    real_estate_data = RealEstateData.query.all()
    df = pd.DataFrame([{
        'price': data.price,
        'bed': data.bed,
        'bath': data.bath,
        'state': data.state,
        'house_size': data.house_size,
        'day': data.day,
        'month': data.month,
        'year': data.year
    } for data in real_estate_data])
    print(df.head())
    charts = []
    
    
    if current_user.role in ['admin', 'analyst', 'researcher']:
        bed_avg_price = avg_val('bed', df, 'price')
        fig1 = px.bar(x=list(bed_avg_price.keys()), y=list(bed_avg_price.values()),
                      labels={'x': 'Number of Beds', 'y': 'Average Price'},
                      title='Number of Beds vs Average Price')
        charts.append(json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder))

        bath_avg_price = avg_val('bath', df, 'price')
        fig2 = px.bar(x=list(bath_avg_price.keys()), y=list(bath_avg_price.values()),
                      labels={'x': 'Number of Baths', 'y': 'Average Price'},
                      title='Number of Baths vs Average Price')
        charts.append(json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder))

        state_avg_price = avg_val('state', df, 'price')
        fig3 = px.bar(x=list(state_avg_price.keys()), y=list(state_avg_price.values()),
                      labels={'x': 'State', 'y': 'Average Price'},
                      title='State vs Average Price')
        charts.append(json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder))

        state_avg_size = avg_val('state', df, 'house_size')
        fig4 = px.bar(x=list(state_avg_size.keys()), y=list(state_avg_size.values()),
                      labels={'x': 'State', 'y': 'Average House Size'},
                      title='State vs Average House Size')
        charts.append(json.dumps(fig4, cls=plotly.utils.PlotlyJSONEncoder))

        state_count = df['state'].value_counts()
        fig5 = px.bar(x=state_count.index, y=state_count.values,
                      labels={'x': 'State', 'y': 'Count'},
                      title='State vs Count of Listings')
        charts.append(json.dumps(fig5, cls=plotly.utils.PlotlyJSONEncoder))

        month_total_price = df.groupby('month')['price'].sum()
        fig6 = px.line(x=month_total_price.index, y=month_total_price.values,
                       labels={'x': 'Month', 'y': 'Total Price'},
                       title='Month Sold vs Total Price')
        charts.append(json.dumps(fig6, cls=plotly.utils.PlotlyJSONEncoder))
    
    elif current_user.role == 'validator':
        charts = charts[:2]
    
    elif current_user.role == 'viewer':
        charts = [charts[0]]
    
    return render_template('dashboard.html', charts=charts)



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
    etl_process = RealEstateETL()

    try:
        logger.info("Starting ETL process")
        data = etl_process.extract_data()
        logger.debug(f"Extracted {len(data)} records")

        transformed_data = etl_process.transformation(data)
        logger.debug(f"Transformed {len(transformed_data)} records")

        etl_process.load_data(transformed_data)
        logger.info("ETL process completed successfully")
        flash("ETL process completed successfully.")
    except Exception as e:
        logger.error(f"ETL process failed: {e}")
        flash(f"ETL process failed: {e}")

    return redirect(url_for('admin_portal'))

@app.route('/admin_portal')
def admin_portal():
    return render_template('admin.html')




@app.route('/switch_database')
@login_required
def switch_database():
    if current_user.role != 'admin':
        flash('Permission denied')
        return redirect(url_for('dashboard'))
    
    current_db = 'mysql' if 'mysql' in app.config['SQLALCHEMY_DATABASE_URI'] else 'postgresql'
    new_config = MySQLConfig if current_db == 'postgresql' else PostgresConfig
    app.config.from_object(new_config)
    
    db.session.remove()
    db.init_app(app)
    
    flash(f'Switched to {new_config.__name__}')
    return redirect(url_for('dashboard'))
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
