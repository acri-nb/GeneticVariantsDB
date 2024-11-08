

# Set wdir and other housekeeping
FROM continuumio/miniconda3

COPY environment.yaml .
COPY cron-dash /etc/cron.d/cron-dash
COPY refresh.sh .
COPY TFAPI_dwl.py .
COPY Add2VarDB.py .

SHELL ["/bin/bash","--login","-c"]

#Create env
RUN conda env create --name docker-base --file=environment.yaml
RUN echo "conda activate docker-base" >> ~/.bashrc
SHELL ["/bin/bash","--login", "-c"]

# Other required commands
#RUN apt-get -y install nano
RUN apt-get update && apt-get -y install cron

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
