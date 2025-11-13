# syntax=docker/dockerfile:1

# Set wdir and other housekeeping
FROM continuumio/miniconda3
WORKDIR /app

COPY environment.yaml .
COPY vardb.py .

# Make run commands use bash --login
SHELL ["/bin/bash","--login","-c"]

# Create conda environment
RUN conda env create --name docker-base --file=environment.yaml && conda clean -afy
SHELL ["conda", "run", "-n", "docker-base", "/bin/bash", "-c"]

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "docker-base", "python3", "vardb.py"]
