#!/bin/bash

# Bash script to set up cron job for updating e-bike availability on PythonAnywhere
# Save this as a file in your project directory and run it, or execute commands manually in the PythonAnywhere console

# Navigate to your project directory
cd /home/yourusername/AisEbikeRental || {
    echo "Error: Could not find project directory. Please update the path."
    exit 1
}

# Create symbolic link to Django settings (if needed)
export DJANGO_SETTINGS_MODULE=ais_ebike_rental.settings
export PYTHONPATH=/home/yourusername/AisEbikeRental:$PYTHONPATH

# Run the management command
python manage.py update_ebike_availability

echo "E-bike availability update completed."

# Optional: Add this script to PythonAnywhere scheduled tasks via:
# 1. Go to your PythonAnywhere dashboard
# 2. Go to "Tasks" tab
# 3. Add a new scheduled task
# 4. Set command: /bin/bash /home/yourusername/AisEbikeRental/pythonanywhere_cron_setup.sh
<<<<<<< HEAD
# 5. Set schedule: Every 5 minutes for real-time updates:
#    */5 * * * *

# Alternative: For better cron job monitoring, you can also use:
# python /home/yourusername/AisEbikeRental/manage.py update_ebike_availability --silent
=======
# 5. Set schedule: Every hour (or your preferred interval)
>>>>>>> bc478c3b2f51a242be15138610bac84cb0a5f46a
