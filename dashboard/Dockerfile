# syntax=docker/dockerfile:1


# Set wdir and other housekeeping
FROM continuumio/miniconda3
WORKDIR /mnt/acri4_2/acri/dashboard

COPY environment.yaml .
COPY vardb.py .

# Make run commands use bash --login

SHELL ["/bin/bash","--login","-c"]

# Make run commands use bash --login
RUN conda config --append channels bioconda
RUN conda env create --name docker-base --file=environment.yaml
SHELL ["conda", "run", "-n", "docker-base", "/bin/bash", "-c"]

COPY vardb.py .

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "docker-base", "python3", "vardb.py"]
