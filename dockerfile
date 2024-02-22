#### GENERATED AUTOMATICALLY NEED TO TRY FIRST BEFORE USING

# Use Miniconda as the base image
FROM continuumio/miniconda3:latest

# Set the working directory in the container
WORKDIR /app

# Copy the Python script into the container at /app
COPY . /app

# Create a Conda environment using an environment.yml file (if you have one)
# If you don't have an environment.yml, you can install packages directly as shown below
# COPY environment.yml /app/environment.yml
# RUN conda env create -f /app/environment.yml

# Alternatively, install Python packages
RUN conda install -c conda-forge dropbox

# add path of the scripts that run the program
ENV PATH=/app:$PATH