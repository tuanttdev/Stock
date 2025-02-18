
FROM apache/airflow:2.10.3-python3.11

COPY requirements.txt /opt/airflow/

USER root
RUN apt-get update && apt-get install -y gcc python3-dev
# Cài đặt các công cụ cần thiết để cài đặt ODBC Driver

RUN apt-get update \
    && apt-get install -y curl apt-transport-https gnupg2 unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thêm các thư viện Python liên quan nếu cần
RUN pip install pyodbc

USER airflow

RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt
