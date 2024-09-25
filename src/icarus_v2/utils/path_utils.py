import os
import sys
import subprocess


def get_base_directory():
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    else:
        # Remove the last three components from the path
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(base_dir)))

    return base_dir


def setup_udev_rules():
    base_dir = get_base_directory()
    script_path = os.path.join(base_dir, "setup", "install_udev_rules.sh")

    try:
        # Run the script with 'pkexec'
        command = ['pkexec', script_path]
        result = subprocess.run(command, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed: {result.stderr.decode().strip()}")
    except Exception as e:
        raise RuntimeError(f"Command execution failed: {str(e)}")
