import subprocess
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "ImageCraftsman.settings"

subprocess.run(
    [
        "uvicorn",
        "ImageCraftsman.asgi:application",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ],
)
