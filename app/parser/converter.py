import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class DWGConverter:
    """
    Converts DWG files to DXF using the ODA File Converter.

    You can either:
    1. Install ODA File Converter normally.
    2. Set the environment variable:
       ODA_FILE_CONVERTER=C:\\Path\\To\\ODAFileConverter.exe
    """

    def __init__(self, oda_path=None):

        self.oda_path = oda_path or os.getenv("ODA_FILE_CONVERTER")

        if not self.oda_path:
            self.oda_path = self.find_converter()

    @staticmethod
    def find_converter():

        possible_paths = [

            # ODA
            r"C:\Program Files\ODA\ODA File Converter\ODAFileConverter.exe",
            r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",

            # Open Design Alliance
            r"C:\Program Files\Open Design Alliance\ODA File Converter\ODAFileConverter.exe",
            r"C:\Program Files\Open Design Alliance\ODAFileConverter\ODAFileConverter.exe",

            # 32-bit
            r"C:\Program Files (x86)\ODA\ODA File Converter\ODAFileConverter.exe",
            r"C:\Program Files (x86)\ODA\ODAFileConverter\ODAFileConverter.exe",

            # Custom install
            r"C:\ODAFileConverter\ODAFileConverter.exe",
        ]

        for path in possible_paths:
            if os.path.isfile(path):
                return path

        # Search Program Files recursively
        for root in [
            r"C:\Program Files",
            r"C:\Program Files (x86)"
        ]:
            if os.path.exists(root):
                for dirpath, _, filenames in os.walk(root):
                    if "ODAFileConverter.exe" in filenames:
                        return os.path.join(dirpath, "ODAFileConverter.exe")

        # Search PATH
        exe = shutil.which("ODAFileConverter.exe")
        if exe:
            return exe

        exe = shutil.which("ODAFileConverter")
        if exe:
            return exe

        return None

    def available(self):
        return self.oda_path is not None and os.path.isfile(self.oda_path)

    def convert(self, dwg_path: str) -> str:

        if not self.available():
            raise RuntimeError(
                "ODA File Converter is not installed.\n\n"
                "Please install it from:\n"
                "https://www.opendesign.com/guestfiles/oda_file_converter\n\n"
                "or set the ODA_FILE_CONVERTER environment variable."
            )

        dwg_path = os.path.abspath(dwg_path)

        input_dir = tempfile.mkdtemp(prefix="dwg_input_")
        output_dir = tempfile.mkdtemp(prefix="dwg_output_")

        filename = os.path.basename(dwg_path)

        shutil.copy2(
            dwg_path,
            os.path.join(input_dir, filename)
        )

        command = [
            self.oda_path,
            input_dir,
            output_dir,
            "ACAD2018",
            "DXF",
            "0",
            "1",
            "*.DWG"
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                "ODA conversion failed.\n\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}"
            )

        dxf_name = Path(filename).with_suffix(".dxf")
        dxf_path = os.path.join(output_dir, dxf_name.name)

        if not os.path.exists(dxf_path):
            raise FileNotFoundError(
                f"Converted DXF not found:\n{dxf_path}"
            )

        return dxf_path