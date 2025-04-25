import subprocess
import config
import os

LOG_PATH = "logs/"

def get_log_filename(log_type: str, terminal_type: str, channel: str) -> str:
    os.makedirs(LOG_PATH, exist_ok=True)  # Ensure logs/ directory exists
    filename = f"{LOG_PATH}{log_type}_{terminal_type}_{channel}.log"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("")  # Create empty log file
    
    return filename


def open_terminal_cmd(title, filepath):
# Check if a window with the same title is already open
# Use PowerShell to check for existing windows with the title
    try:
        check_cmd = [
            "powershell",
            "-Command",
            f"Get-Process cmd | Where-Object {{$_.MainWindowTitle -like '*{title}*'}}"
        ]
        existing = subprocess.run(check_cmd, capture_output=True, text=True)
        if title.lower() in existing.stdout.lower():
            print(f"⚠️ Terminal '{title}' already open. Skipping new launch.")
            if config.RESET_LOGS_ON_START:
                open(filepath, "w").close()
            return None
    except Exception as e:
        print(f"❌ Error checking terminal title: {e}")

    # Launch the actual terminal
    return subprocess.Popen(
        f'start "{title}" cmd /k powershell -Command "Clear-Host; Get-Content -Path \\"{filepath}\\" -Wait"',
        shell=True
    )


def print_to_log(file_name, message, access_type): 
    """
    Writes a formatted message to a log file using the specified access mode.

    Args:
        file_name (str): Path to the log file.
        message (str): message content
        access_type (str): File access mode to use when opening the file.

            Supported file modes:
            - 'r'   : Read (file must exist)
            - 'w'   : Write (overwrite if exists, create if not)
            - 'a'   : Append (create if not exists)
            - 'x'   : Exclusive creation (fail if file exists)
            - 'b'   : Binary mode (combine with others, e.g., 'wb')
            - 't'   : Text mode (default, can combine with others)
            - '+'   : Read and write (combine with 'r', 'w', or 'a')

            Common combinations:
            - 'r+'  : Read/write, file must exist
            - 'w+'  : Read/write, file is overwritten or created
            - 'a+'  : Read/append, file is created if it doesn't exist

    Returns:
        None
    """
    with open(file_name, access_type, encoding="utf-8") as f:
        f.write(f"{message}\n")

# def open_terminal_powershell(title, filepath):
#     return subprocess.Popen([
#         "powershell", "-NoExit", "-Command",
#         f"$host.UI.RawUI.WindowTitle = '{title}'; Get-Content -Path '{filepath}' -Wait"
#     ])

# def open_terminal_windows_terminal(title, filepath):
#     return subprocess.Popen([
#         "wt", f'-w 0 nt --title "{title}" powershell -NoExit -Command "Get-Content -Path \'{filepath}\' -Wait"'
#     ])


# --- Open terminals and keep handles ---
# if terminal_type == "cmd":
#     chat_proc = open_terminal_cmd(f'Twitch Chat - {CHANNEL} - All', chat_log)
#     filtered_proc = open_terminal_cmd(f'Filtered Chat {CHANNEL}', filtered_log)
