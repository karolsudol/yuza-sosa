FROM apache/airflow:2.7.1

USER root

# Install PostgreSQL client and Grafana dependencies
RUN apt-get update && apt-get install -y postgresql-client \
    apt-transport-https \
    software-properties-common \
    wget \
    gnupg2

# Create airflow the logs directory and set correct permissions
RUN mkdir -p /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins \
    && chown -R airflow:root /opt/airflow \
    && chmod -R g+w /opt/airflow

# Add Grafana GPG key and repository
RUN wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
RUN echo "deb https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list

# Install Grafana
RUN apt-get update && apt-get install -y grafana

USER airflow

# Install additional Python packages
COPY requirements.txt /requirements.txt
RUN pip install --user --no-cache-dir -r /requirements.txt

# Copy DAG file to airflow home directory
COPY dags/ETL.py /opt/airflow/dags/ETL.py
