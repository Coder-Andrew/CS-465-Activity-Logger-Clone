#!/bin/bash
cp settings.env .env

export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5001