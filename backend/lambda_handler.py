"""AWS Lambda entry point (Function URL, payload v2). Handler: lambda_handler.handler"""
from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")
