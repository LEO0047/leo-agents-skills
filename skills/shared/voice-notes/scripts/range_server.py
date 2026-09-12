#!/usr/bin/env python3
"""支援 Range 的靜態伺服器。

python -m http.server 不做 Range,瀏覽器就把 seekable 報成 [0,0],音檔完全不能 seek。
要驗證頁面的跳播行為就必須有這個。
"""

import os
import re
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

RANGE = re.compile(r"bytes=(\d*)-(\d*)")


class RangeHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):
        header = self.headers.get("Range")
        if not header:
            return super().send_head()

        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            f = open(path, "rb")
        except OSError:
            self.send_error(404)
            return None

        size = os.fstat(f.fileno()).st_size
        m = RANGE.fullmatch(header.strip())
        if not m or not any(m.groups()):
            f.close()
            self.send_error(400, "bad Range")
            return None
        start_s, end_s = m.group(1), m.group(2)
        if start_s:
            start = int(start_s)
            end = int(end_s) if end_s else size - 1
        else:  # bytes=-N → 最後 N 個位元組
            start = max(0, size - int(end_s))
            end = size - 1
        if start >= size or start > end:
            f.close()
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        end = min(end, size - 1)

        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        f.seek(start)
        self._remaining = end - start + 1
        return _Slice(f, self._remaining)


class _Slice:
    """只吐出指定範圍的檔案包裝,交給 copyfile 用。"""

    def __init__(self, fp, remaining):
        self.fp, self.remaining = fp, remaining

    def read(self, n=-1):
        if self.remaining <= 0:
            return b""
        if n is None or n < 0:
            n = self.remaining
        data = self.fp.read(min(n, self.remaining))
        self.remaining -= len(data)
        return data

    def close(self):
        self.fp.close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8124
    root = sys.argv[2] if len(sys.argv) > 2 else "."
    os.chdir(root)
    print(f"Range-capable server on http://127.0.0.1:{port} rooted at {root}", flush=True)
    HTTPServer(("127.0.0.1", port), RangeHandler).serve_forever()
