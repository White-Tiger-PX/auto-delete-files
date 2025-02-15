import os
import time
import json
import shutil

from set_logger import set_logger


def save_directory(directories_data, directory_path):
    for sub_directory_path in directories_data[directory_path]['sub_directories'].keys():
        save_directory(directories_data, sub_directory_path)

    directories_data[directory_path]['action'] = False
    directories_data[directory_path]['files'] = {}
    directories_data[directory_path]['sub_directories'] = {}


def checking_the_condition_for_action(program_start_time, path_settings, file_name_exceptions, directory_name_exceptions, directories_data):
    time_limit_for_modified_time = program_start_time - path_settings['time_limit_for_modified_time']
    time_limit_for_first_seen = program_start_time - path_settings['time_limit_for_first_seen']
    action_by_last_modified = path_settings['action_by_last_modified']
    action_by_first_seen = path_settings['action_by_first_seen']

    for directory_path, directory_info in directories_data.items():
        if any(directory_name_exception in directory_info['name'] for directory_name_exception in directory_name_exceptions):
            save_directory(directories_data, directory_path)
        else:
            new_files_info = {}

            for file_path, file_info in directory_info['files'].items():
                new_files_info[file_path] = True # delete_restricted по умолчанию

                is_file_exception = any(file_name_exception in file_info['name'] for file_name_exception in file_name_exceptions)
                is_modified_time_condition = file_info['file_modified_time'] < time_limit_for_modified_time
                is_first_seen_condition = file_info['file_first_seen_time'] < time_limit_for_first_seen

                if is_file_exception:
                    continue

                if action_by_last_modified and action_by_first_seen:
                    if is_modified_time_condition and is_first_seen_condition:
                        new_files_info[file_path] = False
                elif action_by_last_modified and is_modified_time_condition:
                    new_files_info[file_path] = False
                elif action_by_first_seen and is_first_seen_condition:
                    new_files_info[file_path] = False

            directories_data[directory_path]['files'] = new_files_info


def deletion_with_entire_folders(path_settings, directories_data):
    directories_data_keys = directories_data.keys()

    for directory_path in list(directories_data.keys())[::-1]:
        all_sub_directories_delete = all(
            directories_data[sub_directory_path]['action']
            for sub_directory_path in directories_data[directory_path]['sub_directories'].keys()
            if sub_directory_path in directories_data_keys
        )

        all_file_delete = all(
            delete_restricted is False
            for delete_restricted in directories_data[directory_path]['files'].values()
        )

        if not ('action' in directories_data[directory_path].keys()):
            directories_data[directory_path]['action'] = all_sub_directories_delete and all_file_delete

    directories_data[path_settings['path']]['action'] = False

    for directory_path, directory_info in directories_data.items():
        if directory_info['action']:
            try:
                shutil.rmtree(directory_path)
                save_directory(directories_data, directory_path)
                logger.info("Удалена директория %s", directory_path)
            except Exception as error:
                logger.error("Ошибка при удалении директории %s: %s", directory_path, error)
                delete_files(directory_info)
        else:
            delete_files(directory_info)


def deletion_only_files(directories_data):
    for directory_path, directory_info in directories_data.items():
        delete_files(directory_info)


def delete_files(directory_info):
    for file_path, delete_restricted in directory_info['files'].items():
        if delete_restricted:
            continue

        try:
            os.remove(file_path)
            logger.info("Удалён файл %s", file_path)
        except Exception as error:
            logger.error("Ошибка при удалении файла %s: %s", file_path, error)


def save_json(file_path, data):
    try:
        file_path = os.path.normpath(file_path)

        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as err:
        logger.error("Ошибка при сохранении файла %s: %s", file_path, err)


def update_files_info(program_start_time, directory_path, file_names, archive_directory_data, directory_data):
    files_data = {}

    for file_name in file_names:
        file_path = os.path.join(directory_path, file_name)

        try:
            archive_file_data = archive_directory_data.get(file_path, None)

            if archive_file_data:
                file_first_seen_time = archive_file_data['file_first_seen_time']
            else:
                file_first_seen_time = program_start_time
        except Exception as err:
            file_first_seen_time = program_start_time
            logger.error("Ошибка получения архивных данных первого обнаружения файла %s: %s", file_path, err)

        try:
            file_modified_time = os.path.getmtime(file_path)
        except Exception as err:
            file_modified_time = program_start_time
            logger.error("Ошибка получения времени последнего изменения файла %s: %s", file_path, err)

        files_data[file_path] = {
            "name": file_name,
            "file_modified_time": file_modified_time,
            "file_first_seen_time": file_first_seen_time
        }

    directory_data['files'] = files_data


def directory_walk(program_start_time, root_directory_path, archive_data, directories_data):
    for directory_path, sub_directories, file_names in os.walk(root_directory_path):
        try:
            archive_directory_data = archive_data.pop(directory_path)
            archive_directory_data = archive_directory_data['files']
        except Exception:
            archive_directory_data = {}

        directory_data = {
            'name': os.path.basename(directory_path),
            'files': {},
            'sub_directories': {}
        }

        update_files_info(program_start_time, directory_path, file_names, archive_directory_data, directory_data)

        for sub_directory_name in sub_directories:
            sub_directory_path = os.path.join(directory_path, sub_directory_name)
            directory_data['sub_directories'][sub_directory_path] = {}

        directories_data[directory_path] = directory_data


def update_dir_info(program_start_time, directory_with_scanned_directories, directory_path):
    directories_data, archive_data = {}, {}

    if not os.path.exists(directory_path):
        return archive_data

    archive_file_name = directory_path.replace('\\', '_').replace('/', '_').replace(':', '')
    path = f"{directory_with_scanned_directories}/{archive_file_name}.json"

    archive_data = load_json(path, default_type={})

    directory_walk(program_start_time, directory_path, archive_data, directories_data)
    save_json(path, directories_data)

    return directories_data


def main(settings):
    directory_with_scanned_directories = settings['directory_with_scanned_directories']

    for path_settings in settings['directories']:
        path_settings['path'] = os.path.normpath(path_settings['path'])

        if not os.path.exists(path_settings['path']):
            continue

        program_start_time = time.time()
        file_name_exceptions = path_settings['file_name_exceptions']
        directory_name_exceptions = path_settings['directory_name_exceptions']

        directories_data = update_dir_info(program_start_time, directory_with_scanned_directories, path_settings['path'])
        checking_the_condition_for_action(program_start_time, path_settings, file_name_exceptions, directory_name_exceptions, directories_data)

        if path_settings['delete_entire_folders']:
            deletion_with_entire_folders(path_settings, directories_data)
        else:
            deletion_only_files(directories_data)


def load_json(file_path, default_type):
    try:
        file_path = os.path.normpath(file_path)

        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            logger.warning("Файл %s не найден, возвращаем значение по умолчанию.", file_path)
    except Exception as err:
        logger.error("Ошибка при загрузке файла %s: %s", file_path, err)

    return default_type


if __name__ == "__main__":
    SETTING_PATH = 'settings.json'

    settings = load_json(SETTING_PATH, default_type={})

    logger = set_logger(log_folder=settings['log_folder']) if settings['save_logs'] else set_logger()

    main(settings)
