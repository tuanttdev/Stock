import uuid
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
import json
import requests

# from utils.constants import OUTPUT_PATH
OUTPUT_PATH = '/opt/airflow/data'
default_args={
    'owner': 'TuanTT', 
    'start_date': datetime(2024,11,17)
}

def get_data(): 
    res = requests.get("https://randomuser.me/api/")
    res=res.json()
    res = res['results'][0]
    
    return res

def format_data(res):
    data = {}
    location = res['location']
    # data['id'] = uuid.uuid4()
    data['first_name'] = res['name']['first']
    data['last_name'] = res['name']['last']
    data['gender'] = res['gender']
    data['address'] = f"{str(location['street']['number'])} {location['street']['name']}, " \
                      f"{location['city']}, {location['state']}, {location['country']}"
    data['post_code'] = location['postcode']
    data['email'] = res['email']
    data['username'] = res['login']['username']
    data['dob'] = res['dob']['date']
    data['registered_date'] = res['registered']['date']
    data['phone'] = res['phone']
    data['picture'] = res['picture']['medium']

    return data
     
def stream_data(): 
    # from kafka import KafkaProducer
    import time 
    import logging

    res = get_data()
    res = format_data(res)
    file_path = f'{OUTPUT_PATH}/output.txt'
    load_data_to_json(res, file_path)
    # producer = KafkaProducer(bootstrap_servers=['broker:29092'], max_block_ms=5000)
    curr_time = time.time()

    while True: 
        if time.time() > curr_time + 6000:
            break
        try: 
            res = get_data()
            res = format_data(res)
            load_data_to_json(res, file_path)

            # producer.send('users_created', json.dumps(res).encode('utf-8'))
            

        except Exception as e: 
            file_path = f'{OUTPUT_PATH}/errors.txt'
            f = open(file_path, 'a', encoding='utf-8') 
            f.write(f'An error occured: {e}' + datetime.now())
            logging.error(f'An error occured: {e}')
            continue


def load_data_to_json (data: dict, path:str):
    f = open(path, 'a', encoding='utf-8')  
    f.write('\n')
    f.write(json.dumps(data, indent=4))
    f.close()

# stream_data()
with DAG('user_automation', 
        default_args=default_args, 
        schedule= None,
        catchup=False) as dag: 
    
    streaming_task = PythonOperator(
    task_id ='stream_data_from_api', 
    python_callable=stream_data
)

# declare dag user_automation , task stream_data_from_api , function call stream_data 
# stream_data()

