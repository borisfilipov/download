# Use Red Hat Enterprise Linux 8 UBI minimal image
FROM devops-app3.dev.ditd.census.gov:7106/base/rhel/ubi9:9.5
USER root

# Set environment variables
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

# Install Python and pip
RUN yum install microdnf -y
RUN microdnf update -y && \
    microdnf install -y python3 python3-pip && \
    microdnf clean all

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Optional: install Python dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip3 install --no-cache-dir -r requirements.txt; fi

# Default command: run app or fall back to tail to keep the container alive
#CMD python3 datamonitorV2.py
CMD ["/bin/bash", "-c", "tail -f /dev/null"]