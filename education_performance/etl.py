import pandas as pd
from extensions import db
from models import EducationData
import os
import logging
from logging.handlers import RotatingFileHandler

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
    


class ETL:
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
        df=df[df['Hours_Studied']>0]
        df=df[df['Sleep_Hours']>0]
        df=df[df['Exam_Score']>0]
        return df 
    

    def load_data(self,df):
        logger.debug(df)
        records = []
        for _, row in df.iterrows():
            new_record = EducationData(
        hours_studied=row['Hours_Studied'],
        attendance=row['Attendance'],
        sleep_hours=row['Sleep_Hours'],
        physical_activity=row['Physical_Activity'],
        learning_disabilities=row['Learning_Disabilities'],
        parental_involvement=row['Parental_Involvement'],
        parental_education_level=row['Parental_Education_Level'],
        distance_from_home=row['Distance_from_Home'],
        peer_influence=row['Peer_Influence'],
        exam_score=row['Exam_Score']
    )
            records.append(new_record)
        
        db.session.bulk_save_objects(records)
        db.session.commit()



