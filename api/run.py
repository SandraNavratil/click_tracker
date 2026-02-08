"""Entry point for running the Click Tracker API locally with uvicorn."""

import uvicorn

from api.app.app import app

if __name__ == "__main__":
    # only for local development
    uvicorn.run(app=app, host="localhost", port=8080, log_level="debug", lifespan="on")  # nosec
