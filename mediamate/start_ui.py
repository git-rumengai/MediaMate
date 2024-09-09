import subprocess
from mediamate.config import config


if __name__ == "__main__":
    ui_script = f'{config.PROJECT_DIR}/ui/主页.py'
    command = ['streamlit', 'run', ui_script]

    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    print(result)
    print(result.stderr)
