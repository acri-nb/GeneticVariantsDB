

# Set wdir and other housekeeping
FROM continuumio/miniconda3

COPY environment.yaml .
COPY cron-dash /etc/cron.d/cron-dash
COPY refresh.sh .
COPY TFAPI_dwl.py .
COPY Add2VarDB.py .

SHELL ["/bin/bash","--login","-c"]

# Install system dependencies first
RUN apt-get update && apt-get -y install --fix-missing cron && apt-get clean && rm -rf /var/lib/apt/lists/*

#Create env
RUN conda env create --name docker-base --file=environment.yaml && conda clean -afy
RUN echo "conda activate docker-base" >> ~/.bashrc
SHELL ["/bin/bash","--login", "-c"]

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cron-dash

# Apply cron job
RUN crontab /etc/cron.d/cron-dash

# Create the log file to be able to run tail
RUN touch /var/log/cron.log
#RUN apt-get -y curl
#RUN apt-get -y unzip

# Make run commands use bash --login
#RUN conda config --append channels bioconda
#RUN conda env create --name docker-base --file=environment.yaml
#ENTRYPOINT ["/bin/bash","--login", "-c"]

# Run the command on container startup
CMD /usr/sbin/cron -f
