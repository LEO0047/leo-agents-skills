from pathlib import Path
import json, base64, mimetypes
ROOT=Path(__file__).resolve().parent
def embed(path):
    file=(ROOT/path).resolve()
    if not file.is_relative_to(ROOT): raise ValueError("圖片必須位於本份教材資料夾")
    mime=mimetypes.guess_type(file.name)[0]
    if mime not in ("image/png","image/jpeg","image/webp","image/svg+xml"): raise ValueError("Unsupported image")
    return "data:"+mime+";base64,"+base64.b64encode(file.read_bytes()).decode()
data=json.loads((ROOT/"對話資料.json").read_text())
assert len({s["id"] for s in data["steps"]})==len(data["steps"])
for step in data["steps"]:
    if step.get("asset"): step["asset_data"]=embed(Path("素材")/step.get("asset_display",step["asset"]))
    if step.get("capture"):
        step["capture_data"]=embed(Path("截圖")/step["capture"])
        step["gallery_data"]=[{"label":"重點畫面","data":step["capture_data"]}]+[{"label":f"其他畫面 {i+1}","data":embed(Path("截圖")/name)} for i,name in enumerate(step.get("additional_captures",[]))]
encoded=json.dumps(data,ensure_ascii=False).replace("<","\\u003c")
output=(ROOT/"對話版樣板.html").read_text().replace("__GUIDE_DATA__",encoded)
target=ROOT/"ChatGPT使用入門 - 初稿.html"
target.write_text(output)
print(f"{len(data['steps'])} steps; {sum(bool(s.get('capture_data')) for s in data['steps'])} captures; {target.stat().st_size} bytes")
