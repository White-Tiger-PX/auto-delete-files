import time

program_start_time = time.time()

LOG_FOLDER                         = "logs/auto_delete_files"
DIRECTORY_WITH_SCANNED_DIRECTORIES = "data/scanned_directories"
DIRECTORIES_SETTINGS = [
    {
        "path": "C:/path/to/you/folder",
        "time_limit_for_modified_time": 604800,
        "time_limit_for_first_seen":    604800,
        "action_by_last_modified": True,
        "action_by_first_seen":    True,
        "delete_entire_folders":   True,
        "file_name_exceptions": [

        ],
        "directory_name_exceptions": [

        ]
    }
]
