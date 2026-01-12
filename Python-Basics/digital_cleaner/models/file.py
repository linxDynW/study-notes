class FileItem:
    def __init__(self, parent, basename, ext, target_folder):
        self.parent = parent
        self.basename = basename
        self.ext = ext
        self.target_folder = target_folder

    def full_name(self):
        return self.basename + self.ext