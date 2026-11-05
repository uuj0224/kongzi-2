"""Deterministic import from pinned GitHub source snapshots; never generate source text."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def chunks(text, limit=460):
    # Preserve every character in order; prefer sentence boundaries.
    result, current = [], ""
    for part in re.findall(r"[^。！？]+[。！？]?|[。！？]", text):
        if current and len(current) + len(part) > limit:
            result.append(current); current = ""
        while len(part) > limit:
            result.append(part[:limit]); part = part[limit:]
        current += part
    if current:
        result.append(current)
    assert "".join(result) == text
    return result


def build():
    manifest = json.loads((ROOT / "data/sources.json").read_text())
    sources = {x["file"]: x for x in manifest}
    notes = json.loads((ROOT / "data/notes.json").read_text())
    rows = []
    def add(id, book, chapter, section, text, kind, source):
        rows.append(dict(id=id, book=book, chapter=chapter, section=section, text=text, kind=kind,
                         note=notes.get(id, ""), note_status="项目整理，待教师复核" if id in notes else "",
                         source_url=sources[source]["url"], source_commit=sources[source]["commit"]))
    lunyu = json.loads((ROOT / "data/raw/lunyu.json").read_text())
    assert len(lunyu) == 20
    for i, ch in enumerate(lunyu, 1):
        for j, paragraph in enumerate(ch["paragraphs"], 1):
            add(f"ly-{i:02}-{j:03}", "论语", ch["chapter"], j, paragraph.strip(), "语录经典", "lunyu.json")
    shiji = (ROOT / "data/raw/shiji.txt").read_text(encoding="utf-8-sig")
    for prefix, title, next_title in [("sj-47", "卷四十七 孔子世家第十七", "卷四十八 陈涉世家第十八"), ("sj-67", "卷六十七 仲尼弟子列传第七", "卷六十八 商君列传第八")]:
        start = shiji.rindex(title) + len(title)
        match = re.search(r"(?m)^\s*卷[一二三四五六七八九十百]+ [^\n]+", shiji[start:])
        if not match:
            raise ValueError("Missing next chapter boundary")
        end = start + match.start()
        body = re.sub(r"\s+", "", shiji[start:end])
        assert len(body) > 1000
        for j, part in enumerate(chunks(body), 1):
            add(f"{prefix}-{j:03}", "史记", title.split(" ")[1], j, part, "史传记述", "shiji.txt")
    liji = (ROOT / "data/raw/liji.txt").read_text(encoding="utf-8-sig")
    for i, chapter in enumerate(["学记", "礼运", "仲尼燕居", "孔子闲居", "儒行"], 1):
        title = "《礼记" + chapter + "》"
        start = liji.index(title) + len(title)
        match = re.search(r"《礼记[^》]+》", liji[start:])
        end = start + match.start() if match else len(liji)
        body = re.sub(r"\s+", "", liji[start:end])
        assert len(body) > 100
        for j, part in enumerate(chunks(body), 1):
            add(f"lj-{i:02}-{j:03}", "礼记", chapter, j, part, "儒家经典", "liji.txt")
    assert len({x["id"] for x in rows}) == len(rows)
    assert set(notes).issubset({x["id"] for x in rows})
    (ROOT / "data/passages.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    for s in manifest:
        s["sha256"] = hashlib.sha256((ROOT / "data/raw" / s["file"]).read_bytes()).hexdigest()
    (ROOT / "data/sources.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Imported {len(rows)} passages, {len(notes)} study notes, {len(set(x['book'] for x in rows))} books")

if __name__ == "__main__":
    build()
