# How to Run FlowBot Hub with Docker

This guide explains how to run the FlowBot Hub application using Docker. This setup includes the Python backend (FastAPI) and the React frontend (Nginx), orchestrated with Docker Compose.

## Prerequisites

- Docker
- Docker Compose

## Setup

1.  **Database Persistence**:
    The setup uses a local directory `backend_data` to persist the database and uploaded files. This directory will be automatically created when you run the containers.
    
    If you have an existing `flowbot.db` in `backend/` or the root directory that you want to preserve:
    - Create a folder named `backend_data` in the root of the project.
    - Copy your `flowbot.db` into `backend_data/`.
    - Ensure the file is named `flowbot.db`.

2.  **Configuration**:
    The `docker-compose.yml` sets the `DATABASE_URL` environment variable to look for the database in the mounted volume.
    
    If you need to change ports, edit `docker-compose.yml`.
    - Frontend default: Port 80
    - Backend default: Port 8000

## Running the Application

1.  Open a terminal in the project root.
2.  Run the following command to build and start the containers:

    ```bash
    docker-compose up -d --build
    ```

3.  The application should now be accessible at `http://localhost` (or your server's IP address).
    - API documentation: `http://localhost/api/docs` unless masked by Nginx (you can access it via direct backend port if exposed, e.g. `http://localhost:8000/docs`). Note that Nginx config provided proxies `/api` to the backend, so `http://localhost/api/docs` might work if FastAPI root path is configured, but usually docs are at `/docs`.
    
    *accessing docs via nginx*:
    The `nginx.conf` proxies `/api` to the backend. FastAPI docs are at `/docs` by default, not `/api/docs`.
    If you want docs to be accessible via Nginx, you would need to proxy `/docs` and `/openapi.json` as well, or configure FastAPI to serve docs at `/api/docs`.
    Currently, you can access docs via port 8000: `http://your-server-ip:8000/docs`.

## Stopping the Application

To stop the containers:

```bash
docker-compose down
```

## Troubleshooting

-   **Database Locked**: If you encounter issues with SQLite locking, ensure only one process is accessing the database file.
-   **Permissions**: Ensure the `backend_data` directory is writable by the Docker container user (usually root).
