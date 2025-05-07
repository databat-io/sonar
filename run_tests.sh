#!/bin/bash

# Build the test container
docker build -t ble-counter-tests -f Dockerfile.test .

# Run tests in the container
docker run --rm \
    -v $(pwd):/app \
    -w /app \
    ble-counter-tests \
    pytest -v --cov=app --cov-report=term-missing