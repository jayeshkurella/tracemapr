#!/bin/bash

# Define project directory and log directory paths
project_directory="/var/lib/jenkins/workspace/tracemapr_beta"
log_directory="/var/log/chhaya"

echo "Changing directory to project workspace directory"
cd $project_directory || { echo "Failed to change directory to $project_directory"; exit 1; }

echo "Validate the present working directory"
pwd

# Check if gunicorn.service file exists in the correct location
service_file="$project_directory/scripts/chhaya_new.service"

if [ -f "$service_file" ]; then
    echo "gunicorn.service found. Copying the service file..."
    sudo cp "$service_file" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl start chhaya_new.service
    sudo systemctl enable chhaya_new.service
    echo "Gunicorn has been started and enabled."
else
    echo "Error: chhaya_new.service not found in $service_file. Please ensure the file exists."
    exit 1
fi

# Restart and check the status of the gunicorn service
# Check the service status and handle errors correctly
sudo systemctl restart chhaya_new.service || { echo "Failed to restart chhaya.service"; exit 1; }

# Checking the status of the service after attempting to restart
service_status=$(sudo systemctl is-active chhaya_new.service)
if [ "$service_status" == "active" ]; then
    echo "chhaya_new.service is running successfully."
else
    echo "chhaya_new.service failed to start. Status: $service_status"
    exit 1
fi

# Create /var/log/chhaya directory, set permissions, and create log files
if [ -d "$log_directory" ]; then
    echo "Log directory $log_directory is present."
else
    echo "Log directory $log_directory not found. Creating the directory..."
    sudo mkdir -p $log_directory
    sudo chown $USER:$USER $log_directory
    sudo touch $log_directory/error.log $log_directory/access.log
    echo "Log directory and files have been created at $log_directory."
fi
