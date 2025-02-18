from vnstock_stream import connect_to_db , get_current_price, append_database, get_list_company, get_historical_price, get_price_board, load_data_to_json , get_company_from_DB
import  pandas as pd
data_file_path = f'./data/data_test.txt'


from datetime import datetime

# connect_to_db()
# get_price()
# append_database()
# get_list_company()
# price_df = get_price_board(stock_code='TCB')
#
# print(price_df)
#
# print(price_df.droplevel(0 , axis=1))
#
# append_database(dict_data=price_df, table_name='price_board')
# #
# price_df = get_price_board(stock_code='BSR')
# #
# append_database(df=price_df, table_name='price_board')

# ls = list(([d["name"][0], d["class"][0]]))
# if isinstance(d, dict):
#     print(type(d))
#
# his_price = get_historical_price(start_date=datetime(year= 2018, month=1, day=1) , end_date=datetime(year= 2018, month=11, day=11) )
# print(his_price)

get_company_from_DB()