class FileSystem:
    def __init__(self):
        self.fs = {
            "home": {
                "ubuntu": {
                    "notes.txt": "Welcome to the system\n",
                    "readme.md": "This is a sample file\n"
                }
            },
            "etc": {},
            "var": {
                "log": {}
            }
        }

        self.cwd = "/home/ubuntu"
        self.home_dir = "/home/ubuntu"