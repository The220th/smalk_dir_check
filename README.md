# smalk_dir_check

smalk implementation for directory activity check

# Setup and run

Edit file `main.py` (config section).

Create venv, activate it, install requirements:

```bash
python3 -m venv {PATH_TO_YOUR_VENV_DIR}
source {PATH_TO_YOUR_VENV_DIR}/bin/activate
pip3 install -r requirements.txt
```

Edit crontab and reboot.

```bash
crontab -e
# add to the end this line:
@reboot sleep 30 && {PATH_TO_YOUR_VENV_DIR}/bin/python {PATH_TO_YOUR_MAIN_PY_FILE}
```

Done!