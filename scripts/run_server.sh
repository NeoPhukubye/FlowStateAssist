#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
uvicorn backend.app.main:app --reload
