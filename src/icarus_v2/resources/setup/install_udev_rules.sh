#!/bin/bash

# Get the directory of the script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

group_name="dataq-di4108-users"
udev_rule="$script_dir/70-dataq-di-4108.rules"
udev_rule_destination="/etc/udev/rules.d/70-dataq-di-4108.rules"

# Function to display error and exit
function display_error_and_exit() {
    echo "Error: $1"
    exit 1
}

# Check if the group already exists
if grep -q "^$group_name:" /etc/group; then
    echo "Group $group_name already exists."
else
    echo "Creating group $group_name..."
    sudo groupadd "$group_name" || display_error_and_exit "Failed to create group $group_name."
fi

# Check if the user is already in the group
if groups "$(whoami)" | grep -q "\b$group_name\b"; then
    echo "$(whoami) is already a member of $group_name group."
else
    # Add the current user to the group
    echo "Adding $(whoami) to $group_name group..."
    sudo usermod -aG "$group_name" "$(whoami)" || display_error_and_exit "Failed to add user to group $group_name."
fi

# Check if the UDEV rule already exists and is accurate
if sudo cmp -s "$udev_rule" "$udev_rule_destination"; then
    echo "UDEV rule for the DATAQ DI-4108 USB device already exists and is accurate."
else
    # Copy the UDEV rule
    if [ -e "$udev_rule" ]; then
        echo "Copying UDEV rule for the DATAQ DI-4108 USB device..."
        sudo cp "$udev_rule" "$udev_rule_destination" || display_error_and_exit "Failed to copy UDEV rule to $udev_rule_destination."
    else
        display_error_and_exit "UDEV rule file not found at $udev_rule."
    fi
fi

# Reload UDEV rules
echo "Reloading UDEV rules..."
sudo udevadm control --reload-rules && sudo udevadm trigger || display_error_and_exit "Failed to reload UDEV rules."

echo "Installation complete."
