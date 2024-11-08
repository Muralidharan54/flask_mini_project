import pandas as pd
from extensions import db
from models import RealEstateData
import os
import logging
from logging.handlers import RotatingFileHandler

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

def read_file(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        return pd.read_excel(file_path)
    elif file_path.endswith('.json'):
        return pd.read_json(file_path)
    elif file_path.endswith('.parquet'):
        return pd.read_parquet(file_path)
    else:
        raise ValueError("Unsupported file format")

def convert_datetime(df):
    df['prev_sold_date'] = pd.to_datetime(df['prev_sold_date'], errors='coerce')
    return df
class RealEstateETL:
    def extract_data(self):
        df_list=[]
        for root, dirs, files in os.walk('data_sources'):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    df = read_file(file_path)
                    df_list.append(df)
                    print(f"Successfully read {file_path}")
                except ValueError as ve:
                    print(f"Skipping {file_path}: {ve}")
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        
        final_frame=pd.concat(df_list)
        logger.debug("extraction done")
        return final_frame
    def transformation(self,df):
        df=df.dropna()
        df=df[df['status']=='for_sale']
        df = df[(df['bed'] >= 1) & (df['bed'] <= 10)]
        df = df[(df['bath'] >= 1) & (df['bath'] <= 10)]
        df=df[df['price']>0]
        df=convert_datetime(df)
        df['day']=df['prev_sold_date'].dt.day
        df['month']=df['prev_sold_date'].dt.month
        df['year']=df['prev_sold_date'].dt.year
        logger.debug("transform done")
        return df 
    

    def load_data(self,df):
        logger.debug(df)
        records = []
        for _, row in df.iterrows():
            record = RealEstateData(
                price=row['price'],
                bed=row['bed'],
                bath=row['bath'],
                state=row['state'],
                house_size=row['house_size'],
                day=row['day'],
                month=row['month'],
                year=row['year']
            )
            records.append(record)
        
        db.session.bulk_save_objects(records)
        db.session.commit()


