import importlib
import subprocess
import os
import platform

# Conditionally import `pwd` only on Unix-based systems
if platform.system() == "Linux":
    import pwd


# Adds permissions for the user to access the USB device
def setup_udev_rules():
    if platform.system() != "Linux":
        raise RuntimeError("This script must be run on Linux systems.")

    with importlib.resources.path('icarus_v2.resources.setup', 'install_udev_rules.sh') as script_path:
        try:
            # Run the script with 'pkexec'
            current_user = pwd.getpwuid(os.getuid()).pw_name
            command = ['pkexec', '--user', current_user, str(script_path)]  # Convert PosixPath to string
            result = subprocess.run(command, stderr=subprocess.PIPE)
            if result.returncode != 0:
                raise RuntimeError(f"Command failed: {result.stderr.decode().strip()}")
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {str(e)}") from e
