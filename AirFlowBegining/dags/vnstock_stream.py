import airflow
import airflow.operators
import airflow.operators.empty
import vnstock3
from vnstock3 import Vnstock

from airflow.decorators import dag, task
from datetime import datetime
from time import time
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import json

import pyodbc

import pandas as pd
from decimal import Decimal # dùng để chuyển từ số float (có lỗi làm tròn ) sang Decimal để dữ nguyên phần thập phân sau dấu phẩy
import ast # module ast dùng để phân tích cú pháp chuỗi Python an toàn, chỉ hỗ trợ các loại dữ liệu cơ bản như list, dict, tuple, int, float, str, v.v.


OUTPUT_PATH = '/opt/airflow/data'
err_file_path = f'{OUTPUT_PATH}/errors.txt'
data_file_path = f'{OUTPUT_PATH}/data.txt'

default_args = {
    "created_date": datetime(year=2024, month=11, day=28),
    "owner": "TuanDz",
    "description":"This Dag created to call vnstock3 api, then store the data into database."

}

# Cấu hình kết nối sql server
server = '192.168.1.52,1433'  # Tên server SQL Server
database = 'stock_db'  # Tên database
username = 'sa'  # Tên đăng nhập SQL Server
password = 'tuantt'  # Mật khẩu SQL Server

def error_log_save (path:str, err:str):
    f = open(path, 'a', encoding='utf-8')
    f.write('\n')
    f.write(time() + ' :' + err)
    f.close()

def load_data_to_json (path:str, data: dict):
    f = open(path, 'a', encoding='utf-8')
    f.write('\n')
    f.write(json.dumps(data, indent=4))
    f.close()

def get_current_price(stock_code = 'TCB'):
    last_call = time()
    vn30 = ['TCB', 'YEG' , 'SSI' , 'ACB', 'BCM' , 'BID', 'BVH', 'CTG', 'FPT' , 'GAS', 'GVR' , 'HDB', 'HPG' , 'MBB', 'MSN' , 'MWG', 'PLX' , 'POW', 'SAB', 'SHB', 'SSB' , 'STB' , 'TPB', 'VCB' , 'VHM', 'VIB', 'VIC', 'VJC' , 'VNM', 'VPB', 'VRE' ]
    price_df = None
    # while True:
    #     if time() > last_call + 60:
    try:
        # for stock_code in vn30:
        #     price_df_for1_stock_code = get_price_board(stock_code)
        price_df = get_price_board(stock_code)
    except Exception as e :
        error_log_save( err_file_path, f'get_current_price() {e}')
    # last_call = time()
    return price_df

def get_historical_price(stock_code='TCB', stock_id=1, start_date=datetime.now(), end_date=datetime.now()):
    start_date = start_date.strftime('%Y-%m-%d')

    end_date = end_date.strftime( '%Y-%m-%d')
    print(type(start_date) , type(end_date))

    stock = Vnstock().stock(symbol=stock_code, source='VCI')

    print(start_date , end_date)
    try:
        # for stock_code in vn30:
        #     price_df_for1_stock_code = get_price_board(stock_code)
        his_price = stock.quote.history(symbol=stock_code, start=start_date, end=end_date)
        # his_price = his_price.drop(columns=his_price.columns[0])
        his_price['time'] = his_price['time'].dt.strftime('%Y-%m-%d')
        his_price['id'] = stock_id
        his_price['symbol'] = stock_code

        #  round open , high, low , close
        #

        # return data_to_insert
        return his_price.values.tolist()
    except Exception as e :
        print( f'get_historical_price(start_date = {start_date} , end_date={end_date}) {e}')
        # error_log_save( err_file_path, f'get_historical_price(start_date = {start_date} , end_date={end_date}) {e}')


def get_price_board(stock_code='TCB' ):
    stock = Vnstock().stock(symbol=stock_code, source='VCI')
    price_board = stock.trading.price_board([stock_code])
    # convert to single index, contain only columns name.
    price_board = price_board.droplevel(0, axis=1)
    # price_board = price_board.droplevel(0, axis=0)
    # add last_update column
    price_board['last_update']= datetime.now()
    price_board['last_update'] = price_board['last_update'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))

    # conver to list

    # price_board_lst = price_board.to_dict(orient='list')

    price_board_lst = price_board.values.tolist()
    return price_board_lst


def connect_to_db():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 18 for SQL Server};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            'TrustServerCertificate=Yes;' ## SQL Server đang sử dụng chứng chỉ SSL tự ký (self-signed certificate), Vì chứng chỉ là tự ký nên ODBC Driver không thể xác thực tính hợp lệ của nó (do không có sự tin tưởng từ phía hệ thống).
                                            ## vì vậy mà cần dùng TrustServerCertificate=Yes; để bỏ qua xác thực SSL
        )
        print("Kết nối thành công!")

        # # Tạo cursor để thực hiện truy vấn
        # cursor = conn.cursor()
        # cursor.execute("SELECT @@VERSION")  # Truy vấn SQL
        # row = cursor.fetchone()
        # print(f"Phiên bản SQL Server: {row[0]}")
        #
        # # Đóng kết nối
        # cursor.close()
        # conn.close()
        return conn
    except Exception as e:
        print(f"Lỗi kết nối db: {e}")



def append_database(table_name=any, dict_data = list, **context):
    conn = connect_to_db()

    if conn is not None:
        cursor = conn.cursor()
        # print(type(dict_data))
        # print(dict_data)
        if not isinstance(dict_data, list):
            dict_data = ast.literal_eval(dict_data)

        print(type(dict_data))
        print(dict_data)
        try:
            if table_name == 'historical_price':
                data_tuple = tuple(dict_data)
                for each in data_tuple:
                    each[1] = Decimal(str(each[1]))
                    each[2] = Decimal(str(each[2]))
                    each[3] = Decimal(str(each[3]))
                    each[4] = Decimal(str(each[4]))

                print(data_tuple)

                # data_to_insert = [tuple(row) for row in his_price.itertuples(index=False, name=None)]

                sql = f'''insert into {table_name} ( date0, [open], high, low, [close], volume , id, symbol)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        '''

                cursor.executemany(sql, data_tuple)
                cursor.commit()
            elif table_name == 'price_board':
                sql = f'''insert into {table_name} (symbol, ceiling, floor, ref_price, stock_type, exchange, last_trading_date, listed_share, type, id, organ_name, prior_close_price, benefit, trading_date, match_price, match_vol, accumulated_volume, accumulated_value, avg_match_price, highest, lowest, match_type, foreign_sell_volume, foreign_buy_volume, current_room, total_room, total_accumulated_value, total_accumulated_volume, reference_price, bid_1_price, bid_1_volume, bid_2_price, bid_2_volume, bid_3_price, bid_3_volume, ask_1_price, ask_1_volume, ask_2_price, ask_2_volume, ask_3_price, ask_3_volume, last_update)
                                       select ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                                       '''

                # list_of_values  = list(tuple([dict_data["symbol"]), dict_data["ceiling"], dict_data["floor"], dict_data["ref_price"], dict_data["stock_type"], dict_data["exchange"], dict_data["last_trading_date"], dict_data["listed_share"], dict_data["type"], dict_data["id"], dict_data["organ_name"], dict_data["prior_close_price"], dict_data["benefit"], dict_data["trading_date"], dict_data["match_price"], dict_data["match_vol"], dict_data["accumulated_volume"], dict_data["accumulated_value"], dict_data["avg_match_price"], dict_data["highest"], dict_data["lowest"], dict_data["match_type"], dict_data["foreign_sell_volume"], dict_data["foreign_buy_volume"], dict_data["current_room"], dict_data["total_room"], dict_data["total_accumulated_value"], dict_data["total_accumulated_volume"], dict_data["reference_price"], dict_data["bid_1_price"], dict_data["bid_1_volume"], dict_data["bid_2_price"], dict_data["bid_2_volume"], dict_data["bid_3_price"], dict_data["bid_3_volume"], dict_data["ask_1_price"], dict_data["ask_1_volume"], dict_data["ask_2_price"], dict_data["ask_2_volume"], dict_data["ask_3_price"], dict_data["ask_3_volume"], dict_data["last_update"]])
                # list_of_values = list([(dict_data["symbol"].value, dict_data["ceiling"].value)])

                # sql = f'''insert into {table_name} (symbol, ceiling) select ?, ?'''

                # print (list_of_values)
                cursor.executemany(sql, dict_data)
                cursor.commit()
            else:
                print('Bảng không tồn tại')

        except Exception as e:
            print(f"Có lỗi khi thực hiện append_database: {e}")

        finally:
            if conn:
                conn.close()

def get_company_from_DB():
    conn = connect_to_db()

    if conn is not None:
        cursor = conn.cursor()

        # Truy vấn dữ liệu từ bảng (ví dụ bảng 'your_table')
        cursor.execute("SELECT id , symbol FROM stockcompany")
        columns = [column[0] for column in cursor.description]
        print("Tên các cột:", columns)
        # Lấy tất cả kết quả truy vấn
        rows = cursor.fetchall()
        print(type(rows))
    return rows

def get_list_company():
    stock = Vnstock().stock(symbol="ACB", source='VCI')
    list_company = stock.listing.symbols_by_exchange()
    conn = connect_to_db()
    try:

        cursor = conn.cursor()
        sql = '''insert into stockcompany(id ,symbol, organ_name )
        VALUES (?, ?, ?)
        '''

        cursor.executemany(sql, list_company[['id' ,'symbol', 'organ_name']].values.tolist())
        cursor.commit()
        conn.close()
    except Exception as e :
        print(f"Có lỗi khi thực hiện: {e}")

    return list_company
#
## tạm comment lại
# with DAG(dag_id='stock_information',
#         default_args=default_args,
#         start_date= datetime(year=2025, month=2, day=17, hour=9, minute=30, second=0),
#         end_date = datetime(year=2025, month=10, day=17, hour=16, minute=30, second=0),
#         schedule_interval= '*/1 0-11,13-17 * * 1-5', #
#         catchup=False) as dag:
#     stock_symbols = get_company_from_DB()
#
#     call_api_task = PythonOperator(
#         task_id ='stream_data_from_api'
#         , python_callable= get_current_price
#         , provide_context = True
#     )
#     do_nothing = EmptyOperator(task_id="do_nothing")
#     append_database_task = PythonOperator(
#         task_id='append_to_database'
#         , python_callable= append_database
#         , op_kwargs={'table_name': 'price_board', 'dict_data' : '{{ ti.xcom_pull(task_ids="stream_data_from_api") }}'}  # Truyền giá trị vào tham số my_var
#         , provide_context=True
#
#     )
#
#     call_api_task  >> append_database_task
## tạm comment lại

@dag(
    dag_id='stock_information_dynamic',
    start_date=datetime(2025, 2, 17, 9, 30, 0),
    end_date=datetime(2025, 10, 17, 16, 30, 0),
    schedule_interval='*/1 0-11,13-17 * * 1-5',
    catchup=False
)
def stock_information_dynamic():
    stock_symbols = [(8424683, 'TCB'), (8424512 ,'ACB')] # get_company_from_DB()  # Trả về danh sách [(id1, symbol1), ...]

    @task
    def fetch_price(stock):
        stock_id, stock_code = stock
        print(f"Fetching price for {stock_code} (ID: {stock_id})")
        return get_current_price(stock_code=stock_code)

    @task
    def append_to_database(price_data):
        append_database(table_name="price_board", dict_data=price_data)

    prices = fetch_price.expand(stock=stock_symbols)
    append_to_database.expand(price_data=prices)

stock_information_dynamic()

dag2 = DAG(dag_id='history_price',
        default_args=default_args,
        start_date= datetime(year=2025, month=2, day=16, hour=9, minute=30, second=0),
        end_date = datetime(year=2025, month=4, day=16, hour=23, minute=30, second=0),
         # schedule_interval= '* * * * *',
        schedule_interval= None,
        catchup=False
)

symbols = get_company_from_DB()
for symbol in symbols:

    call_api_task1 = PythonOperator(
        task_id =f'stream_history_data_from_api_for_stock_{symbol[1]}'
        , python_callable= get_historical_price
        , op_kwargs={'stock_code':symbol[1], 'stock_id':symbol[0] , 'start_date': datetime(year=2018, month=1 , day =1) ,'end_date': datetime.now() }
        # Truyền giá trị vào tham số my_var
        , provide_context = True
        , dag=dag2
    )

    append_database_task1 = PythonOperator(
        task_id=f'append_to_database_for_stock_{symbol[1]}'
        , python_callable= append_database
        , op_kwargs={'table_name': 'historical_price',
                     'dict_data': '{{ ti.xcom_pull(task_ids="stream_history_data_from_api_for_stock_' + symbol[1] + '") }}'
                     }
        , provide_context=True
        , dag=dag2
    )

    call_api_task1  >> append_database_task1

# get_price()