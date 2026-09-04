# shearearth.com — WordPress + Divi build

This is the Option A redesign, built as a Divi site: a child theme that carries
the design system, five pages built from Divi modules, and a global header and
footer for the Divi Theme Builder.

## What's in here

```
themes/shear-performance/      Divi child theme — the whole design system
  style.css                      tokens, components, responsive rules
  functions.php                  stylesheet + Google Fonts enqueues

plugin/spe-site-importer/      one-click setup plugin
  spe-site-importer.php          uploads media, builds pages, wires menus
  layouts/*.txt                  the Divi shortcode for each page
  media/*                        the photography and logo

divi/                          manual import route (if you'd rather not
  shear-performance-library.json   use the plugin)
  pages/*.json

preview/                       static render of all five pages, for review
```

`preview/` is a build artifact and is not committed. Run
`python3 scripts/build-divi.py` from the repository root to generate it, then
open `preview/index.html`. It loads the real `style.css` alongside an
approximation of Divi's own base rules, so the design can be checked in a
browser without a WordPress install.

## Requirements

- WordPress 6.x
- Divi (Elegant Themes) — an active licence, installed as the parent theme

The layouts are written in Divi 4 shortcode, which Divi 5 reads and converts on
open. If the site is on Divi 5, open each page in the builder once after import
and save, so the conversion is stored rather than repeated on every request.

## Install

1. **Divi.** Upload and activate Divi under Appearance → Themes, and enter the
   licence under Divi → Theme Options → Updates.

2. **Child theme.** Upload `themes/shear-performance` to
   `wp-content/themes/`, then activate **Shear Performance EarthWorks** under
   Appearance → Themes. The site will look unstyled until step 4 — that is
   expected, there is no content yet.

3. **Setup plugin.** Upload `plugin/spe-site-importer` to
   `wp-content/plugins/` and activate **Shear Performance Site Setup**.

4. **Build the site.** Go to **Tools → Shear Performance Setup** and press
   *Build the site*. It uploads the photography, creates Home, About, Services,
   Contact and Gallery as Divi pages, builds the main and footer menus, sets
   Home as the front page, and adds the global header and footer to the Divi
   Library. Running it again is safe — pages are matched by slug and updated in
   place, images by filename.

5. **Attach the header and footer.** Go to **Divi → Theme Builder**. On the
   default website template:
   - *Add Global Header* → **Add From Library** → **SPE Global Header**
   - *Add Global Footer* → **Add From Library** → **SPE Global Footer**

   Then **Save Changes**.

6. **Check the contact form address.** Open the Contact page in the builder and
   confirm the contact form's email is a monitored inbox. It ships as
   `service@shearearth.com`.

Once the plugin has run you can deactivate and delete it — nothing on the site
depends on it afterwards.

### Manual route, without the plugin

Everything the plugin does can be done by hand:

- Import `divi/shear-performance-library.json` from **Divi → Divi Library →
  Import & Export → Import**. That loads the header, the footer and all five
  page layouts into the Library.
- Or, page by page: create the page, open the Divi Builder, and use the page
  settings → Portability → Import with the matching file from `divi/pages/`.
- Then upload `plugin/spe-site-importer/media/*` to the Media Library and
  repoint the images, since the JSON files reference
  `https://www.shearearth.com/wp-content/uploads/spe/…` as a placeholder path.

The plugin route avoids that last step, which is why it is the recommended one.

## Editing the site

**Everything visual lives in the child theme's `style.css`.** The Divi modules
carry structure and content; they deliberately carry almost no design settings,
because Divi compiles module design settings into `!important` rules that the
stylesheet cannot then override. If a colour, size or spacing needs to change,
change the token or component rule in `style.css` rather than the module.

The tokens are at the top of `style.css` under `:root` — palette, fonts, and
the two container widths.

**Text and images** are edited normally in the Visual Builder.

**Photos and videos** come from the August 24 WeTransfer folder. The home page
opens with a worksite photograph; the service sections pair copy with project
photos and playable portrait clips. About introduces the team, Contact shows
the equipment, and Gallery includes seven photos and three additional clips.

**Video players** are HTML5 players inside Divi Code modules. They preserve the
original portrait framing, offer native playback/fullscreen controls, and load
video only when played (`preload="none"`). Each has a poster image. The clips
are intentionally silent and do not autoplay. To replace a clip in the builder,
update both its MP4 source and poster URL in the Code module.

**The gallery** is a Divi Gallery module with native image enlargement. Add or
remove photos through its image picker. The static preview links to the full
images; WordPress supplies Divi's lightbox.

**Navigation** is two normal WordPress menus, *Main Menu* and *Footer Menu*,
under Appearance → Menus. The phone button in the header is a Divi Button
module inside the Theme Builder header, not a menu item.

## Rebuilding the source files

The layouts, the Divi JSON exports and the preview are all generated from
`scripts/build-divi.py` at the repository root:

```sh
python3 scripts/build-divi.py              # layouts, divi/*.json, preview/
python3 scripts/build-media.py             # supplied photos, trimmed clips, archive logo
python3 scripts/check-layouts.py           # shortcode nesting, tokens, media
python3 scripts/check-php-syntax.py wordpress
```

Edit the page copy or structure in `scripts/build-divi.py` and re-run it —
don't hand-edit `plugin/spe-site-importer/layouts/*.txt`, they are overwritten.

## Notes on the build

**Three places where the implementation departs from the comp**, all because
the comp's value would have rendered as invisible text:

- Link hover was specified as `#1f5233`, a dark green that all but disappears
  against the dark background. Hovers use the accent green `#5fae7c` instead.
- The "More about us" link on the home page was specified as `#1f5233` on the
  dark green About band — roughly 1.5:1 contrast. It uses the accent green.
- The contact form's submit button was specified as `#1b1a1d` background with
  `#1b201a` text, which is unreadable. It matches the other primary buttons.

**Media source.** `scripts/build-media.py` reads the supplied folder by default:
`/mnt/c/Users/mkern/Downloads/wetransfer_videos-and-photos_2026-08-24_1650`.
Pass `--source /path/to/folder` on another machine. It requires Pillow and
FFmpeg. The originals are never modified. JPEG exports preserve orientation,
strip metadata, and are never enlarged. Videos are trimmed to 14–18 seconds,
encoded as 640×1138 H.264 MP4s for desktop and 480×854 MP4s for screens up to
640px. Both use fast-start metadata and have no audio or source metadata. The
logo is retained from the site archive.

See [MEDIA.md](MEDIA.md) for source filenames, clip timing, and placement.
No waterfront project is visible in the supplied material; the waterfront
service uses equipment/context photography without claiming a waterfront result.

**Validation.** The generated static pages can be reviewed with
`python3 -m http.server 8765 --directory wordpress/preview` from the repository
root. The preview approximates Divi, including a native mobile menu. Contact
form delivery and the Divi gallery lightbox require the actual WordPress install.
The final WordPress import and Theme Builder attachment still follow the install
steps above.
