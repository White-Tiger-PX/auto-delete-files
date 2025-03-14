<p align="center">
  <a href="README.ru.md"><img src="https://img.shields.io/badge/Русский-Readme-blue" alt="Russian" /></a>&nbsp;&nbsp;
  <a href="README.md"><img src="https://img.shields.io/badge/English-Readme-blue" alt="English" /></a>&nbsp;&nbsp;
  <img src="https://visitor-badge.laobi.icu/badge?page_id=White-Tiger-PX.auto-delete-files" alt="visitors" />&nbsp;&nbsp;
  <img src="https://img.shields.io/github/stars/White-Tiger-PX/auto-delete-files?style=social" alt="GitHub stars" />
</p>

# auto-delete-files

This script is designed to delete files and folders based on certain conditions, such as the last modified time and the first seen time of the file.

## Description

The utility performs the following actions:

- Scans the specified directory and its subdirectories.
- Checks files based on their last modified time and first seen time.
- Deletes files and folders that meet the specified conditions.
- Provides detailed logs of actions (if the log saving option is enabled).

## Configuration

All settings are specified in the `config.py` file. Example configuration structure:

```python
LOG_FOLDER                         = "logs"
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
```

### Field Descriptions

- **LOG_FOLDER**: The folder where logs will be saved (used if `LOG_FOLDER` is not 'None').
- **DIRECTORY_WITH_SCANNED_DIRECTORIES**: The folder where data about scanned directories will be stored.
- **DIRECTORIES_SETTINGS**: A list of directories to be processed. Each directory should contain the following parameters:
  - **path**: The path to the directory being processed.
  - **time_limit_for_modified_time**: The time (in seconds) since the last modification, after which the file meets the action criteria.
  - **time_limit_for_first_seen**: The time (in seconds) after which a file is considered outdated (based on its first seen time).
  - **action_by_last_modified**: A boolean value indicating whether the last modified time of the file should be taken into account.
  - **action_by_first_seen**: A boolean value indicating whether the first seen time of the file should be taken into account.
  - **delete_entire_folders**: A boolean value indicating whether entire folders can be deleted if all files within them meet the criteria for deletion and the folders are empty.
  - **file_name_exceptions**: A list of file name exceptions, indicating files that should not be deleted.
  - **directory_name_exceptions**: A list of directory name exceptions, indicating directories that should not be processed.

## Notes

- The script uses Python's standard libraries, so no additional dependencies are required.
- Processing large amounts of data and many folders may take some time.
- Ensure that the paths in `config.py` are correctly specified and compatible with your operating system (for Windows, use backslashes `\`).

### Automatic Execution

On Windows (using Task Scheduler):

1. Open the **Task Scheduler** by searching for it in the Start menu.
2. Click on **Create task** in the right-hand panel.
3. Give your task a name (e.g., "Telegram Bot Task").
4. Go to the **Triggers** tab, and click **New**.
    - Set the **Begin the task** option to **At logon** to make sure the task starts when you log into your system.
    - Check **Repeat task every** and set it to repeat every X minutes (e.g., every 10 minutes).
5. Go to the **Actions** tab, click **New**, and choose **Start a Program**.
6. Browse and select the Python executable (`python.exe`).
7. In the **Add arguments** field, enter the path to your script (e.g., `C:\programs\auto_delete_files.py`).
8. Click **OK** to save the task.

<div style="justify-content: space-between; align-items: center;">
  <div style="text-align: center;">
    <img src="Task Scheduler - General.png" alt="Task Scheduler - General" width="75%" />
  </div>

  <div style="text-align: center;">
    <img src="Task Scheduler - Triggers.png" alt="Task Scheduler - Triggers" width="75%" />
  </div>

  <div style="text-align: center;">
    <img src="Task Scheduler - Actions.png" alt="Task Scheduler - Actions" width="75%" />
  </div>
</div>
