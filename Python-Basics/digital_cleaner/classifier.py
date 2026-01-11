import os
import shutil
from types import MappingProxyType

from file import FileItem
from history import HistoryManager
from loguru import logger
from tqdm import tqdm

EXTENSION_MAP = MappingProxyType({
    # === Image ===
    "Image": {
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".svg", ".psd", ".raw"
    },

    # === Document ===
    "Document": {
        ".txt", ".md", ".pdf", ".docx", ".xlsx",
        ".pptx", ".log"
    },

    # === Audio ===
    "Audio": {
        ".mp3", ".wav", ".flac", ".aac", ".ogg",
        ".wma", ".m4a", ".opus", ".mid", ".ape"
    },

    # === Video ===
    "Video": {
        ".mp4", ".mkv", ".mov", ".avi", ".wmv",
        ".flv", ".webm", ".m4v", ".rmvb", ".ts"
    },

    # === Code ===
    "Code": {
        ".c", ".cpp", ".py", ".java", ".js", ".ts",
        ".html", ".css", ".php", ".go", ".rs"
    },

    # === Data ===
    "Data": {
        ".json", ".yaml", ".yml", ".xml", ".sql",
        ".csv", ".nbt", ".dat", ".db", ".sqlite"
    },

    # === Archive ===
    "Archive": {
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".bz2", ".xz"
    },

    # === Executable ===
    "Executable": {
        ".exe", ".msi", ".bat", ".sh", ".ps1",
        ".dll", ".sys", ".iso", ".com", ".bin",
        ".deb", ".rpm", ".jar"
    },

    # === Specialized ===
    "Specialized": {
        ".litematic", ".schem", ".ttf", ".otf", ".cur"
    }
})

class FileClassifier:
    def __init__(self, history_manager: HistoryManager):
        self.files = []
        self.htma = history_manager

    def files_get(self, files_list, original_path):
        if  len(files_list) == 0:
            return

        for file_str in files_list:
            full_src_path = os.path.join(original_path, file_str)
            if os.path.isdir(full_src_path):
                logger.info(f"[忽略目录] {file_str}")
                continue

            name, ext = os.path.splitext(file_str)

            for i in EXTENSION_MAP:
                if ext.lower() in EXTENSION_MAP[i]:
                    target_folder = i
                    break
            target_folder = target_folder if 'target_folder' in locals() else "Other"
            file_obj = FileItem(original_path, name, ext, target_folder)
            self.files.append(file_obj)

    def to_target_folder(self, base_dst_path):
        pbar = tqdm(self.files, desc="移动文件", unit="个")
        for file_obj in self.files:
            pbar.set_postfix(file=(filename := file_obj.basename + file_obj.ext))

            original_full_path = os.path.join(file_obj.parent, filename)

            target_folder_path = os.path.join(base_dst_path, file_obj.target_folder)

            target_file_path = os.path.join(target_folder_path, filename)

            if not os.path.exists(target_folder_path):
                os.makedirs(target_folder_path)
            if os.path.exists(target_file_path):
                logger.warning(f"跳过同名文件: {filename}")
            try:
                shutil.move(original_full_path, target_file_path)
                self.htma.append_log_list(
                    original_full_path,
                    target_file_path,
                    filename
                    )
                logger.info(f"移动成功: {filename}")
            except Exception as e:
                logger.error(f"移动失败： {filename}: {e}")
            pbar.update(1)
        pbar.close()
        self.files = []

    def undo(self):
        if not self.htma.log:
            logger.warning("没有可以撤回的操作记录")
            return
        logger.info(f"开始执行撤回操作: 共{len(file_length := self.htma.log)}个文件")
        count = 0
        pbar = tqdm(file_length, desc="撤回文件", unit="个")
        for action in file_length:
            pbar.set_postfix(file=(filename := action["Operand"]))
            filename = action["Operand"]
            original_full_path = action["dst_path"]
            target_file_path = action["src_path"]

            if not os.path.exists(original_full_path):
                 logger.warning(f"文件不存在或无权访问(可能已被手动移动) : {filename}")
            if os.path.exists(target_file_path):
                logger.warning(f"跳过同名文件: {filename}")
            try:
                shutil.move(original_full_path, target_file_path)

                action["src_path"] = original_full_path
                action["dst_path"] = target_file_path
                action["time"] = self.htma.get_now()

                logger.info(f"已撤回: {filename}")
                count += 1
            except Exception as e:
                logger.error(f"移动失败 {filename}:{e}")
            pbar.update(1)
            logger.info(f"操作完成。共撤回 {count}个文件")
