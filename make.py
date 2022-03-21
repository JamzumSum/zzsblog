from datetime import date, datetime
from pathlib import Path

import pytz
import yaml
from myst_parser.main import to_tokens


def changelog(f, paths: dict[Path, float]):
    for p, t in paths.items():
        mod_ts = date.fromtimestamp(t)
        ref = p.as_posix().removeprefix("source/")
        f.write(f"- {mod_ts.strftime(FMT)} []({ref})\n")


def news():
    d: dict[float, Path] = {}
    for p in Path("source").iterdir():
        if not p.is_dir():
            continue
        if p.stem.startswith("_"):
            continue
        for pp in p.rglob("*.md"):
            if pp.stem == "index":
                continue
            if pp.stem.startswith("_"):
                continue
            ts = 0
            with open(pp, encoding="utf8") as f:
                fm = next(filter(lambda t: t.type == "front_matter", to_tokens(f.read())), None)
                if fm:
                    sdate = yaml.safe_load(fm.content).get("date", "")
                    try:
                        ddate = datetime.strptime(sdate, "%Y-%m-%d")
                        ddate.replace(tzinfo=TZ)
                        ts = ddate.timestamp()
                    except ValueError:
                        pass
            if ts == 0:
                ts = pp.stat().st_mtime
            d[ts] = pp

    with open("source/_snippets/news.md", "w", encoding="utf8") as f:
        changelog(f, {d[k]: k for k in sorted(d)[:10]})


if __name__ == "__main__":
    FMT = "%Y年%m月%d日"
    TZ = pytz.timezone("Asia/Shanghai")
    news()
