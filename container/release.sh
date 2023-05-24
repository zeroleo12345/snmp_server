#!/usr/bin/env sh

export ENVIRONMENT=production; export DEBUG=False; export RESTART_POLICY=unless-stopped; ENTRYPOINT="" docker-compose up -d alert
