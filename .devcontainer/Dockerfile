# Use an official Python image as base
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system libs WeasyPrint needs (cairo, pango)
RUN apt-get update && apt-get install -y \
    libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libxml2 libxslt1-dev \
    build-essential git curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create workspace user (already in base images generally)
USER vscode
