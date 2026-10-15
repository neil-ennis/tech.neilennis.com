"""Apply repeatable static-site repairs after a full Staatic export.

Usage: python scripts/prepare_export.py SITE_DIR WORDPRESS_DIR
Run this only on a copied export, never on WordPress or Staatic's staging area.
"""

from pathlib import Path
import json
import re
import shutil
import sys

site = Path(sys.argv[1]).resolve()
wordpress = Path(sys.argv[2]).resolve()
if not (site / "index.html").is_file() or not (wordpress / "wp-content").is_dir():
    raise SystemExit("Expected a copied Staatic site and a WordPress source directory")
if site == wordpress or wordpress in site.parents:
    raise SystemExit("The copied site must be outside the WordPress source")

not_found = site / "404_not_found" / "index.html"
if not_found.is_file():
    shutil.copy2(not_found, site / "404.html")

removed_tags = re.compile(r"<link\b[^>]*(?:/wp-json/|/xmlrpc\.php)[^>]*>", re.I)
protected_tags = re.compile(
    r"<(?:link|meta)\b[^>]*(?:rel=['\"]canonical['\"]|property=['\"]og:url['\"])[^>]*>",
    re.I,
)
old_site_url = re.compile(r"https?://tech\.neilennis\.com(?=/|[\"'\s<]|$)", re.I)
html_files_changed = 0
for path in site.rglob("*.html"):
    original = path.read_text(encoding="utf-8", errors="replace")
    text = removed_tags.sub("", original)
    protected = []

    def hold_tag(match):
        protected.append(match.group(0))
        return f"__TECH_CANONICAL_{len(protected) - 1}__"

    text = protected_tags.sub(hold_tag, text)
    # Bare origins are Home links; replacing them with an empty value would
    # point to the current article instead of the site root.
    text = old_site_url.sub(
        lambda match: "" if text[match.end() : match.end() + 1] == "/" else "/",
        text,
    )
    text = text.replace("https:/amber.com.au", "https://amber.com.au")
    # WordPress redirects the former About Me page to the published About page.
    text = text.replace("/index.php/about/about-me/", "/about/")
    text = text.replace("/about/about-me/", "/about/")
    for number, tag in enumerate(protected):
        text = text.replace(f"__TECH_CANONICAL_{number}__", tag)
    if text != original:
        path.write_text(text, encoding="utf-8")
        html_files_changed += 1

font_files_copied = 0
css_files_changed = 0
for path in site.rglob("*.css"):
    original = path.read_text(encoding="utf-8", errors="replace")
    text = original.replace("/:8088/wp-content/fonts/", "/wp-content/fonts/")
    if text != original:
        path.write_text(text, encoding="utf-8")
        css_files_changed += 1
    for relative in set(re.findall(r"/wp-content/fonts/[^)'\"\s]+\.woff2?", text, re.I)):
        source = wordpress / relative.lstrip("/")
        target = site / relative.lstrip("/")
        if not source.is_file():
            raise SystemExit(f"Referenced font is absent from WordPress: {source}")
        if not target.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            font_files_copied += 1

portrait = Path("wp-content/gallery/neil/neilsmall2.jpg")
portrait_source = wordpress / portrait
if not portrait_source.is_file():
    raise SystemExit(f"Referenced portrait is absent from WordPress: {portrait_source}")
(site / portrait).parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(portrait_source, site / portrait)

for relative in (
    "wp-content/uploads/GeoIP.dat",
    "wp-content/uploads/GeoIPv6.dat",
    "wp-json/index.html",
    "wp-content/uploads/woocommerce_uploads/index.html",
):
    path = site / relative
    if path.is_file():
        path.unlink()
api_dir = site / "wp-json"
if api_dir.is_dir() and not any(api_dir.iterdir()):
    api_dir.rmdir()

# WordPress's plain postmap uses only post_name. Some published pages redirect
# elsewhere or sit beneath a parent; their shortlinks need the real destination.
postmap = site / "postmap.json"
data = json.loads(postmap.read_text(encoding="utf-8"))
mapping = data.get("map", data)
mapping.update(
    {
        "156": "http://blog.neilennis.com/",
        "159": "http://music.NeilEnnis.com/",
        "161": "http://www.flickr.com/photos/magictyger/sets/",
        "163": "http://ShipWatcher.com/",
        "165": "http://pol.neilennis.com/",
        "174": "http://tenpoundpoms.com/",
        "176": "http://postcards.neilennis.com/",
        "178": "http://youtube.com/MagicTyger/",
        "185": "http://blog.neilennis.com/",
        "188": "http://expert1.net/",
        "191": "http://Shipwatcher.com/",
        "194": "http://blog.shipwatcher.com/",
        "196": "http://shipwatcher.com/photos/",
        "241": "/about/credits/",
        "250": "/about/",
        "350": "http://ObSrv.com/",
        "591": "/",
        "594": "/about/contact/",
    }
)
postmap.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

resolver = site / "p" / "index.html"
resolver_html = resolver.read_text(encoding="utf-8")
old_redirect = 'const dest = "/" + slug.replace(/^\\/+/, "").replace(/\\/?$/, "/");'
new_redirect = (
    'const dest = /^https?:\\/\\//i.test(slug) ? slug : '
    '"/" + slug.replace(/^\\/+/, "").replace(/\\/?$/, "/");'
)
if old_redirect in resolver_html:
    resolver.write_text(resolver_html.replace(old_redirect, new_redirect), encoding="utf-8")
elif new_redirect not in resolver_html:
    raise SystemExit("Unrecognized numeric shortlink resolver; review site/p/index.html")

# Old WordPress links such as /?p=559 and the sidebar's /?page_id=2 must
# resolve on a static host. Keep this tiny redirect in the home page's head.
home = site / "index.html"
home_html = home.read_text(encoding="utf-8")
legacy_query_redirect = (
    "<script>" 
    "(function(){const q=new URLSearchParams(location.search);"
    "const id=q.get('p')||q.get('page_id');"
    "if(id&&/^\\d+$/.test(id))location.replace('/p/?id='+id);})()"
    "</script>"
)
if legacy_query_redirect not in home_html:
    if "<head>" not in home_html:
        raise SystemExit("Home page has no head element for legacy query redirects")
    home.write_text(home_html.replace("<head>", "<head>" + legacy_query_redirect, 1), encoding="utf-8")

print(
    f"Prepared {html_files_changed} HTML files; corrected {css_files_changed} CSS files; "
    f"copied {font_files_copied} fonts and the referenced portrait."
)
