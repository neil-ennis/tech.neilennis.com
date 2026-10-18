# tech.neilennis.com

This repository holds the public static snapshot of [Technical Musings](https://tech.neilennis.com/). The editable source is a separate, private local WordPress installation. Staatic generates the reviewed snapshot in `site/`; Cloudflare Workers Static Assets serves it on the live domain and the `workers.dev` preview.

## Layout

- `site/` contains the public website.
- `wrangler.jsonc` configures Cloudflare Workers Static Assets and the live custom domain.
- `site/postmap.json` and `site/p/index.html` preserve numeric post shortlinks; `site/_redirects` routes `/p/<id>` to the resolver.
- The separate `nbe.me` redirector sends `/t/<id>` to `https://tech.neilennis.com/p/<id>`. Keep the `/p/` resolver and every existing `postmap.json` entry when refreshing the export.
- `site/404.html` provides the static not-found page.
- `scripts/prepare_export.py` repairs Staatic's local font URLs, copies the referenced local fonts and sidebar portrait, maps redirected page IDs to their actual destinations, and omits unneeded GeoIP and REST API inventory files.
- `scripts/repair_missing_images.py` restores four lost post images from `assets/recovered/` and removes one unavailable decorative Office graphic from each new export. Image sources and reuse notes are recorded in `assets/recovered/SOURCES.md`.

## Updating the site

1. Back up the WordPress database and source, then finish a full local Staatic publication.
2. Review its output and compare it with the current published snapshot. Check internal links, media, redirects, shortlinks, and any interactive features.
3. Replace generated content in `site/` with the reviewed export, retaining `site/_redirects`. From this repository, run `python scripts/prepare_export.py site PATH_TO_WORDPRESS_DATA` on the copied snapshot.
4. Check the legacy attachment redirects in `site/_redirects` and confirm every target image still exists. Check a local preview, then commit and push the snapshot. Cloudflare deploys pushes to `main` through its Git integration.

Before changing the live domain, test an old and a recent `nbe.me/t/<id>` link, then open those same `/p/<id>` paths on the Cloudflare preview. The `nbe.me` redirector points at the live domain and does not itself validate that the destination article exists.

Keep WordPress code, databases, logs, backups, credentials, and local configuration out of this public repository. The previous AWS host should remain available until the Cloudflare deployment is reviewed and the live domain is switched.

## Initial migration notes

The initial full export on 16 October 2026 finished with 602 resources. Staatic reported one expected 403 for the non-public WooCommerce upload-directory guard. The reviewed public snapshot contains 632 files after adding 31 referenced fonts, a sidebar portrait, the static 404 page, and `_redirects`, and omitting two unreferenced GeoIP data files, a WordPress REST API inventory file, and the generated WooCommerce 403 page.

Two links were corrected in the private WordPress source after a database backup: the About menu item now points to `/about/`, and the Amber Electric link in “Home Assistant Automations” has a valid `https://` URL. The export-repair script applies the same fixes to the current snapshot. External media on `cdn2.neilennis.com` remains hosted separately.
