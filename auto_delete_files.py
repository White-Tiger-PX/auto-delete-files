import os
import json
import shutil

from set_logger import set_logger
from utils_json import load_json, save_json

import config


def delete_files(directory_info):
    for file_path, file_info in directory_info['files'].items():
        if file_info['it_is_forbidden_to_delete'] is False:
            try:
                os.remove(file_path)

                logger.info("Файл '%s' удалён.", file_path)
            except Exception as error:
                logger.error("Ошибка при удалении файла '%s': %s", file_path, error)


def deletion_only_files(directories_data):
    for directory_path, directory_info in directories_data.items():
        delete_files(directory_info=directory_info)


def build_directory_structure(directory_path, directories_data):
    directory_info = directories_data[directory_path]

    file_names = [file_data["name"] for file_data in directory_info['files'].values()]

    sub_directories = {
        sub_dir_path: build_directory_structure(sub_dir_path, directories_data)
        for sub_dir_path in directory_info['sub_directories'].keys()
    }

    structure = {
        "file_names":      file_names,
        "sub_directories": sub_directories
    }

    return structure


def deletion_with_entire_folders(path_settings, directories_data):
    directories_data_keys = directories_data.keys()

    for directory_path in list(directories_data.keys())[::-1]:
        all_sub_directories_delete = all(
            directories_data[sub_directory_path]['can_delete_all']
            for sub_directory_path in directories_data[directory_path]['sub_directories'].keys()
            if sub_directory_path in directories_data_keys
        )

        all_file_delete = all(
            file_info['it_is_forbidden_to_delete'] is False
            for file_info in directories_data[directory_path]['files'].values()
        )

        if 'can_delete_all' not in directories_data[directory_path]:
            directories_data[directory_path]['can_delete_all'] = all_sub_directories_delete and all_file_delete

    directories_data[path_settings['path']]['can_delete_all'] = False

    for directory_path, directory_info in directories_data.items():
        if directory_info['can_delete_all']:
            try:
                directory_structure = {directory_path: build_directory_structure(directory_path, directories_data)}
                structure_json      = json.dumps(directory_structure, indent=4, ensure_ascii=False)

                logger.info(
                    "Директория '%s' со следующей структурой удалена:\n%s",
                    directory_path,
                    structure_json
                )

                shutil.rmtree(directory_path)
                save_directory(directories_data=directories_data, directory_path=directory_path)
            except Exception as error:
                logger.error("Ошибка при удалении директории '%s': %s", directory_path, error)

                delete_files(directory_info=directory_info)
        else:
            delete_files(directory_info=directory_info)


def update_files_info(directory_path, file_names, archive_directory_data, directory_data):
    files_data = {}

    for file_name in file_names:
        file_path = os.path.join(directory_path, file_name)

        try:
            archive_file_data = archive_directory_data.get(file_path)
            file_first_seen_time = config.program_start_time

            if archive_file_data:
                file_first_seen_time = archive_file_data['file_first_seen_time']
        except Exception as err:
            file_first_seen_time = config.program_start_time
            logger.error("Ошибка получения архивных данных первого обнаружения файла '%s': %s", file_path, err)

        try:
            file_modified_time = os.path.getmtime(file_path)
        except Exception as err:
            file_modified_time = config.program_start_time
            logger.error("Ошибка получения времени последнего изменения файла '%s': %s", file_path, err)

        files_data[file_path] = {
            "name": file_name,
            "file_modified_time": file_modified_time,
            "file_first_seen_time": file_first_seen_time
        }

    directory_data['files'] = files_data


def directory_walk(root_directory_path, archive_data, directories_data):
    for directory_path, sub_directories, file_names in os.walk(root_directory_path):
        try:
            archive_directory_data = archive_data.pop(directory_path)
            archive_directory_data = archive_directory_data['files']
        except Exception:
            archive_directory_data = {}

        directory_data = {
            'name':            os.path.basename(directory_path),
            'files':           {},
            'sub_directories': {}
        }

        update_files_info(
            directory_path         = directory_path,
            file_names             = file_names,
            archive_directory_data = archive_directory_data,
            directory_data         = directory_data
        )

        for sub_directory_name in sub_directories:
            sub_directory_path = os.path.join(directory_path, sub_directory_name)
            directory_data['sub_directories'][sub_directory_path] = {}

        directories_data[directory_path] = directory_data


def save_directory(directories_data, directory_path):
    for sub_directory_path in directories_data[directory_path]['sub_directories'].keys():
        save_directory(directories_data=directories_data, directory_path=sub_directory_path)

    directories_data[directory_path]['can_delete_all']  = False
    directories_data[directory_path]['files']           = {}
    directories_data[directory_path]['sub_directories'] = {}


def checking_the_condition_for_action(path_settings, file_name_exceptions, directory_name_exceptions, directories_data):
    time_limit_for_modified_time = config.program_start_time - path_settings['time_limit_for_modified_time']
    time_limit_for_first_seen    = config.program_start_time - path_settings['time_limit_for_first_seen']
    action_by_last_modified      = path_settings['action_by_last_modified']
    action_by_first_seen         = path_settings['action_by_first_seen']

    for directory_path, directory_info in directories_data.items():
        directory_has_exception = any(
            directory_name_exception in directory_info['name']
            for directory_name_exception in directory_name_exceptions
        )

        if directory_has_exception:
            save_directory(directories_data=directories_data, directory_path=directory_path)

            continue

        for file_path, file_info in directory_info['files'].items():
            directory_info['files'][file_path]['it_is_forbidden_to_delete'] = True # True по умолчанию

            file_has_exception = any(
                file_name_exception in file_info['name']
                for file_name_exception in file_name_exceptions
            )

            if file_has_exception:
                continue

            first_seen_condition    = file_info['file_first_seen_time'] < time_limit_for_first_seen
            modified_time_condition = file_info['file_modified_time']   < time_limit_for_modified_time

            if action_by_last_modified and action_by_first_seen:
                if modified_time_condition and first_seen_condition:
                    directory_info['files'][file_path]['it_is_forbidden_to_delete'] = False
            elif action_by_last_modified and modified_time_condition:
                directory_info['files'][file_path]['it_is_forbidden_to_delete'] = False
            elif action_by_first_seen and first_seen_condition:
                directory_info['files'][file_path]['it_is_forbidden_to_delete'] = False


def update_dir_info(directory_path, directories_data):
    archive_data = {}

    if not os.path.exists(directory_path):
        return archive_data

    archive_data_file_name = f"{directory_path.replace('\\', '_').replace('/', '_').replace(':', '')}.json"
    archive_data_file_path = os.path.join(config.DIRECTORY_WITH_SCANNED_DIRECTORIES, archive_data_file_name)

    archive_data = load_json(file_path=archive_data_file_path, default_type={}, logger=logger)

    directory_walk(
        root_directory_path = directory_path,
        archive_data        = archive_data,
        directories_data    = directories_data
    )

    save_json(file_path=archive_data_file_path, data=directories_data, logger=logger)


def main():
    for path_settings in config.DIRECTORIES_SETTINGS:
        if not os.path.exists(path_settings['path']):
            continue

        directories_data          = {}
        file_name_exceptions      = path_settings['file_name_exceptions']
        directory_name_exceptions = path_settings['directory_name_exceptions']

        update_dir_info(
            directory_path      = path_settings['path'],
            directories_data    = directories_data
        )

        checking_the_condition_for_action(
            path_settings             = path_settings,
            file_name_exceptions      = file_name_exceptions,
            directory_name_exceptions = directory_name_exceptions,
            directories_data          = directories_data
        )

        if path_settings['delete_entire_folders']:
            deletion_with_entire_folders(path_settings=path_settings, directories_data=directories_data)
        else:
            deletion_only_files(directories_data=directories_data)


if __name__ == "__main__":
    logger = set_logger(log_folder=config.LOG_FOLDER)

    main()
