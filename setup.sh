#!/bin/bash
set -e

source .env

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Docker is not installed. Please install Docker and try again."
        exit 1
    fi
}

check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        echo "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
}

check_port_available() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use. Please free this port and try again."
        exit 1
    fi
}

run_tests() {
    echo "Running unit tests..."
    make test-unit
}

set_airflow_variables() {
    echo "Setting Airflow variables..."
    
    if [ ! -f .env ]; then
        echo ".env file not found. Please create a .env file with necessary variables."
        exit 1
    fi
    source .env
    if [ -z "$DUNE_API_KEY" ]; then
        echo "DUNE_API_KEY is not set in .env file."
        exit 1
    fi
    docker-compose run --rm airflow-webserver airflow variables set DUNE_API_KEY "$DUNE_API_KEY"
    echo "Airflow variables set successfully."
}

wait_for_service() {
    echo "Waiting for $1 to be ready..."
    until docker-compose exec $1 $2; do
        echo "Waiting for $1..."
        sleep 5
    done
    echo "$1 is ready."
}

configure_grafana() {
    echo "Configuring Grafana..."
    until curl -s http://localhost:${GRAFANA_PORT} > /dev/null; do
        echo "Waiting for Grafana to start..."
        sleep 5
    done

    curl -X POST -H "Content-Type: application/json" -d '{
        "name":"PostgreSQL",
        "type":"postgres",
        "url":"postgres:${POSTGRES_PORT}",
        "database":"'${POSTGRES_DB}'",
        "user":"'${POSTGRES_USER}'",
        "password":"'${POSTGRES_PASSWORD}'",
        "access":"proxy",
        "basicAuth":false
    }' http://${GF_SECURITY_ADMIN_USER}:${GF_SECURITY_ADMIN_PASSWORD}@localhost:${GRAFANA_PORT}/api/datasources
    
    echo "Grafana configured with PostgreSQL data source."
}

main() {
    check_docker
    check_docker_compose
    check_port_available ${AIRFLOW_WEBSERVER_PORT}
    check_port_available ${POSTGRES_PORT}
    check_port_available ${GRAFANA_PORT}

    echo "Setting up Airflow with Grafana and PostgreSQL..."

    echo "Building Docker images..."
    make build

    echo "Initializing Airflow..."
    make init

    set_airflow_variables

    echo "Starting all services..."
    make up

    wait_for_service postgres "pg_isready -U $POSTGRES_USER"
    wait_for_service airflow-webserver "airflow jobs check"

    configure_grafana

    echo "Setup complete! Services are now running."
    echo "You can access the Airflow web interface at http://localhost:${AIRFLOW_WEBSERVER_PORT}"
    echo "Username: $AIRFLOW_WWW_USER_USERNAME"
    echo "Password: $AIRFLOW_WWW_USER_PASSWORD"
    echo "You can access the Grafana web interface at http://localhost:${GRAFANA_PORT}"
    echo "Username: $GF_SECURITY_ADMIN_USER"
    echo "Password: $GF_SECURITY_ADMIN_PASSWORD"
    
    echo "Displaying logs. Press Ctrl+C to exit."
    make logs
}

main