"""Keep the recovered Tech post images usable after every Staatic export.

Usage: python scripts/repair_missing_images.py SITE_DIR
The source images live in assets/recovered in the public Tech repository.
"""

from pathlib import Path
import re
import shutil
import sys


ASSETS = Path(__file__).resolve().parents[1] / "assets" / "recovered"
PUBLIC_PREFIX = b"/wp-content/uploads/recovered/"
S3 = b"https://s3.ap-southeast-2.amazonaws.com/tech.neilennis.com/wp-content/uploads/"
REPLACEMENTS = {
    S3 + b"2011/10/14161908/5855930819_8ae836f3a3.jpg": b"nasa-cdfs-black-hole.jpg",
    S3 + b"2011/10/14161908/5855930819_8ae836f3a3-300x200.jpg": b"nasa-cdfs-black-hole.jpg",
    S3 + b"2011/10/14161908/5855930819_8ae836f3a3-150x100.jpg": b"nasa-cdfs-black-hole.jpg",
    S3 + b"2011/10/14161908/5855930819_8ae836f3a3-400x266.jpg": b"nasa-cdfs-black-hole.jpg",
    S3 + b"2016/03/18105022/COU3GBAD_1.jpg": b"comsol-u3gbad-main.jpg",
    b"http://www.sonyericsson.com/images/spgd/GPD_29950high_27_0_4001.jpg": b"sony-ericsson-k800i.jpg",
    b"http://obsrv.com/Images/ObsrvBanner1.jpg": b"ObsrvBanner1.jpg",
}
ALTS = {
    b"nasa-cdfs-black-hole.jpg": b"Illustration of a growing black hole",
    b"comsol-u3gbad-main.jpg": b"Comsol USB 3.0 to Gigabit Ethernet adapter",
    b"sony-ericsson-k800i.jpg": b"Sony Ericsson K800i phone",
    b"ObsrvBanner1.jpg": b"ObSrv logo with an eye in the letter O",
}


def repair_missing_images(site: Path) -> int:
    site = site.resolve()
    if not (site / "index.html").is_file():
        raise ValueError(f"Not a prepared site directory: {site}")

    target_dir = site / "wp-content" / "uploads" / "recovered"
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in set(REPLACEMENTS.values()):
        source = ASSETS / name.decode("ascii")
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, target_dir / source.name)

    changed = 0
    for path in site.rglob("*.html"):
        original = path.read_bytes()
        data = original
        # All four old responsive variants are gone; use the recovered master.
        data = re.sub(rb'\s+srcset="[^"]*5855930819_8ae836f3a3[^"]*"', b"", data)
        for old, name in REPLACEMENTS.items():
            data = data.replace(old, PUBLIC_PREFIX + name)
        # The second Office 365 stock graphic has no recoverable original.
        # Its removal leaves the product photograph and article text intact.
        data = re.sub(
            rb'<br\s*/?>\s*<img\b[^>]*Image_AcrossDevices_558x2721\.png[^>]*>',
            b"",
            data,
        )
        data = re.sub(
            rb'<img\b[^>]*Image_AcrossDevices_558x2721\.png[^>]*>',
            b"",
            data,
        )
        # The original Sony product URL is dead, and obsrv.com is a new service.
        data = re.sub(
            rb'href="http://www\.sonyericsson\.com/spg\.jsp\?[^\"]+"',
            b'href="https://commons.wikimedia.org/wiki/File:SE_K800i_2.jpg"',
            data,
        )
        data = data.replace(
            b'href="http://obsrv.com/"',
            b'href="https://web.archive.org/web/20110201100027/http://obsrv.com/"',
        )

        def add_alt(match: re.Match[bytes]) -> bytes:
            tag = match.group(0)
            for name, alt in ALTS.items():
                if PUBLIC_PREFIX + name in tag and b'alt=""' in tag:
                    return tag.replace(b'alt=""', b'alt="' + alt + b'"', 1)
            return tag

        data = re.sub(rb"<img\b[^>]*>", add_alt, data)
        if data != original:
            path.write_bytes(data)
            changed += 1
    return changed


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/repair_missing_images.py SITE_DIR")
    print(f"Repaired images in {repair_missing_images(Path(sys.argv[1]))} HTML files.")
