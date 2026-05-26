#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Installing frontend dependencies..."
cd frontend
npm ci

echo "Building frontend..."
npm run build

echo "Copying build output to server/static/..."
rm -rf ../server/static/*
cp -r dist/* ../server/static/

echo "Frontend build complete. Static files are in server/static/"
