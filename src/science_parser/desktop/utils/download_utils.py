import re
import filetype
from pathlib import Path

def check_object_on_file(response, url) -> dict:
    content_disposition = response.headers.get("Content-Disposition", "")
    filename = None
    if "attachment" in content_disposition:
        match = re.search(r'filename="?([^";]+)"?', content_disposition)
        if match:
            filename = match.group(1)

    if not filename:
        filename = url.split("/")[-1].split("?")[0] or "downloaded_file"
    
    head = b""
    for chunk in response.iter_content(chunk_size=1024):
        head = chunk
        break
    
    if head.lower().lstrip().startswith(b"<!doctype html") or head.lower().lstrip().startswith(b"<html"):
        return {"status": "html"}

    try:
        res = response.json()
        return {"status": "json", "json": res}
    except Exception as e:
        pass 

    kind = filetype.guess(head)
    if kind:
        if not filename.endswith(f".{kind.extension}"):
            filename = f"{Path(filename).stem}.{kind.extension}"

    return {"status": "file", "filename": filename}
