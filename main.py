# coding: utf-8

# V0.1.0

import traceback
import time
import datetime
import os
from pathlib import Path
from ksupk import get_files_list, calc_hash_of_file, calc_hash_of_str
from alerk_pack.message import MessageWrapper
from alerk_pack.communicator import Kommunicator, convert_strs_to_keys

# ==================================== config section ====================================


def get_dir() -> str:
    return "/path/to/dir2"


class Settings:
    sleep_before_check = 5  # How long to wait between
    startup_message = "smalk_dir_check up"  # message to alerk if this smalk turned on. Leave empty ("") if no need this hello message
    dirs = {
        "dir1":
            {
                "path": "/path/to/dir1",  # path to interested directory or callable
                "refresh_rate": 600,  # How often to check (seconds)
                "report_if_changed" : True,  #  Report if directory has changed. If set to False, then vice versa -- report if directory has not changed
                "message_for_alerk": "dir1 changed! ",  # Will show in message for alerk
                "consider_file_size": True,  # If the size of any file in a directory has changed, the directory is considered to have changed
                "consider_file_mod_date": True,  # If last modification date of any file in a directory has changed, the directory is considered to have changed
                "need_calc_file_hash": False,  # Calculate hash of files to understand that directory has changed. May take a long time
                "prev_hash": None,  # Do not edit it. Leave None here
                "last_check_time": None,  # Do not edit it. Leave None here
            },
        "dir2":
            {
                "path": get_dir,  # path to interested directory or callable
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
        prev_hash = dir_data_dict["prev_hash"]
        dir_data_dict["prev_hash"] = _hash
        if dir_data_dict["report_if_changed"]:
            return prev_hash == _hash
        else:
            return prev_hash != _hash


def report_to_alerk(dir_data: dict):
    msg_text: str = dir_data["message_for_alerk"]
    mw = MessageWrapper(MessageWrapper.MSG_TYPE_REPORT, msg_text, False)
    Kommunicator().add_msg(mw)


def unpack_path(path) -> str:
    if isinstance(path, str):
        return path
    elif isinstance(path, Path):
        return str(path)
    elif callable(path):
        return path()
    else:
        raise TypeError("(unpack_path) path must be path str or callable")


def process():
    while True:
        time.sleep(Settings.sleep_before_check)
        cur_time = time.time()
        dirs = Settings.dirs
        for dir_i in dirs:
            dir_data = dirs[dir_i]
            dir_path = dir_data["path"]
            dir_path = unpack_path(dir_path)
            refresh_rate = dir_data["refresh_rate"]
            last_check_time = dir_data["last_check_time"]
            if last_check_time is None or cur_time - last_check_time >= refresh_rate:
                need_report = not check_dir(dir_path, dir_data)
                if need_report:
                    report_to_alerk(dir_data)
                dir_data["last_check_time"] = time.time()


def main():
    keys = convert_strs_to_keys(Settings.priv_key, Settings.pub_key, Settings.sign_key, Settings.verif_key,
                                Settings.alerk_pub_key, Settings.alerk_verify_key, None)
    Kommunicator(url=Settings.alerk_url,
                 priv_key=keys[0],
                 public_key=keys[1],
                 sign_key=keys[2],
                 verify_key=keys[3],
                 alerk_pub_key=keys[4],
                 alerk_verify_key=keys[5],
                 sym_key=keys[6])
    Kommunicator().start()
    if Settings.startup_message != "":
        Kommunicator().add_msg(MessageWrapper(MessageWrapper.MSG_TYPE_REPORT, Settings.startup_message, False))
    try:
        process()
    except Exception as e:
        error_text = f"{traceback.format_exc()}\n{e}"
        print(f"Something gone wrong: {error_text}\n\n Restarting")
        time.sleep(15)


if __name__ == "__main__":
    main()
