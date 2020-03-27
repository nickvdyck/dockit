import subprocess

def mount(type, device, path) -> int:
    result = subprocess.run(["mount", "-t", type, device, path])
    result.returncode
