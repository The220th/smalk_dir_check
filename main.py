# coding: utf-8

# V0.0.1

import traceback
import time
import datetime
import os
from ksupk import get_files_list, calc_hash_of_file, calc_hash_of_str
from alerk_pack.message import MessageWrapper
from alerk_pack.communicator import Kommunicator
from alerk_pack.crypto import str_to_asym_key

# ==================================== config section ====================================

class Settings:
    sleep_before_check = 30  # How long to wait between
    dirs = {
        "/path/to/dir1":
            {
                "refresh_rate": 600,  # How often to check (seconds)
                "report_if_changed" : True,  #  Report if directory has changed. If set to False, then vice versa -- report if directory has not changed
                "message_for_alerk": "dir1 changed! ",  # Will show in message for alerk
                "consider_file_size": True,  # If the size of any file in a directory has changed, the directory is considered to have changed
                "consider_file_mod_date": True,  # If last modification date of any file in a directory has changed, the directory is considered to have changed
                "need_calc_file_hash": False,  # Calculate hash of files to understand that directory has changed. May take a long time
                "prev_hash": None,  # Do not edit it. Leave None here
                "last_check_time": None,  # Do not edit it. Leave None here
            },
        "/path/to/dir2":
            {
              "...": "copy from one above",
            },
    }

    # Generate keys below with command "alerk gen_keys" (more info: https://github.com/The220th/alerk)
    priv_key = ""
    pub_key = ""
    sign_key = ""
    verif_key = ""

    alerk_url = "127.0.0.1:8000/enry"
    alerk_pub_key = ""
    alerk_verify_key = ""

# ==================================== config section ====================================

def get_cur_time():
    template = "%Y.%m.%d %H:%M:%S"
    time_str = datetime.datetime.now().strftime(template)
    return time_str


def check_dir(dir_path: str, dir_data_dict: dict) -> bool:
    """
    :return: True if all os ok, False if needed to report to alerk
    """
    files = get_files_list(dir_path)
    file_strs = []
    for file_i in files:
        file_str = f"{os.path.relpath(file_i, dir_path)}"
        if dir_data_dict["consider_file_size"]:
            file_size = os.path.getsize(file_i)
            file_str += f" {file_size}"
        if dir_data_dict["consider_file_mod_date"]:
            file_last_mod_time = os.path.getmtime(file_i)
            file_str += f" {file_last_mod_time}"
        if dir_data_dict["need_calc_file_hash"]:
            file_hash = calc_hash_of_file(file_i)
            file_str += f" {file_hash}"

        file_strs.append(file_str)
    _hash = calc_hash_of_str("\n".join(file_strs))

    if dir_data_dict["prev_hash"] is None:
        dir_data_dict["prev_hash"] = _hash
        return True
    else:
        if dir_data_dict["report_if_changed"]:
            return dir_data_dict["prev_hash"] == _hash
        else:
            return dir_data_dict["prev_hash"] != _hash


def report_to_alerk(dir_data: dict):
    msg_text: str = dir_data["message_for_alerk"]
    mw = MessageWrapper(MessageWrapper.MSG_TYPE_REPORT, msg_text, False)
    Kommunicator().add_msg(mw)


def process():
    while True:
        time.sleep(Settings.sleep_before_check)
        cur_time = time.time()
        dirs = Settings.dirs
        for dir_i in dirs:
            dir_data = dirs[dir_i]
            refresh_rate = dir_data["refresh_rate"]
            last_check_time = dir_data["last_check_time"]
            if last_check_time is None or cur_time - last_check_time >= refresh_rate:
                need_report = not check_dir(dir_i, dir_data)
                if need_report:
                    report_to_alerk(dir_data)
                dir_data["last_check_time"] = time.time()


def main():
    Kommunicator(url=Settings.alerk_url,
                 priv_key=str_to_asym_key(Settings.priv_key, False),
                 public_key=str_to_asym_key(Settings.pub_key, True),
                 sign_key=str_to_asym_key(Settings.sign_key, False),
                 verify_key=str_to_asym_key(Settings.verif_key, True),
                 alerk_pub_key=str_to_asym_key(Settings.alerk_pub_key, True),
                 alerk_verify_key=str_to_asym_key(Settings.alerk_verify_key, True),
                 sym_key=None)
    Kommunicator().start()
    try:
        process()
    except Exception as e:
        error_text = f"{traceback.format_exc()}\n{e}"
        print(f"Something gone wrong: {error_text}\n\n Restarting")
        time.sleep(15)


if __name__ == "__main__":
    main()
