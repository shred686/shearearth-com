# Deploying to Hostinger

This repository is not a WordPress site. It holds a Divi child theme, a
one-shot setup plugin, and the generators that produce both. Only two
directories ever reach the server:

| Repository path | Server path |
| --- | --- |
| `wordpress/themes/shear-performance/` | `wp-content/themes/shear-performance/` |
| `wordpress/plugin/spe-site-importer/` | `wp-content/plugins/spe-site-importer/` |

`scripts/`, `source/`, `wordpress/divi/` and `wordpress/preview/` are
build-time and reference material. They stay in CI.

Three things cannot come from GitHub at all:

- **Divi.** Licensed and paid, so it is not in the repository. Install it once
  through WP admin and enter the licence under Divi → Theme Options → Updates.
- **The site build.** `Tools → Shear Performance Setup` writes pages, menus and
  media to the *database*. One click, once.
- **The Theme Builder header and footer.** Also database, also once. See step 5
  of [wordpress/README.md](wordpress/README.md).

So: a one-time manual setup on the server, then an automated file pipeline for
everything after it.

## One-time setup

Before changing the live site, take a Hostinger backup of its files and
WordPress database. Confirm the production domain: this project uses
`shearearth.com`. DNS setup alone does not install WordPress or Divi.

### 1. Collect the SSH details

In hPanel: **Advanced → SSH Access**. Note the IP, username (`uNNNNNNNNN`) and
port — Hostinger's shared hosting uses `65002`, not 22. Turn SSH on if it is
off.

Find the WordPress root while you are there, usually:

```
/home/uNNNNNNNNN/domains/shearearth.com/public_html
```

### 2. Make a deploy key

Generate a keypair used only by this pipeline:

```sh
ssh-keygen -t ed25519 -f ~/.ssh/shearearth_deploy -N "" -C "github-actions"
```

Put the **public** half on the server:

```sh
ssh-copy-id -i ~/.ssh/shearearth_deploy.pub -p 65002 uNNNNNNNNN@<host>
```

Confirm it works before going further:

```sh
ssh -i ~/.ssh/shearearth_deploy -p 65002 uNNNNNNNNN@<host> 'ls domains'
```

### 3. Add the GitHub secrets

Repository → Settings → Secrets and variables → Actions:

| Secret | Value |
| --- | --- |
| `HOSTINGER_SSH_KEY` | contents of `~/.ssh/shearearth_deploy` (the private half) |
| `HOSTINGER_HOST` | the IP or hostname from hPanel |
| `HOSTINGER_USER` | `uNNNNNNNNN` |
| `HOSTINGER_PORT` | `65002` |
| `HOSTINGER_WP_PATH` | absolute path to the WordPress root, no trailing slash |

### 4. Build the site

1. Install WordPress on the domain (hPanel's auto-installer is fine).
2. Upload and activate Divi, and enter the licence key.
3. Run the deploy workflow manually — Actions → *Deploy to Hostinger* → Run
   workflow, with **deploy the setup plugin** checked. That is the only time
   the plugin needs to ship.
4. Activate **Shear Performance EarthWorks** under Appearance → Themes.
5. Activate **Shear Performance Site Setup**, then run
   **Tools → Shear Performance Setup**.
6. Attach the global header and footer in Divi → Theme Builder.
7. Delete the plugin from the server. Nothing depends on it afterwards.

### Bootstrap through SSH instead of WP admin

After the workflow has deployed both directories, activate the child theme
and importer with WP-CLI. Deactivate the standalone `divi-builder` plugin if
installed, because the Divi parent theme includes the builder itself.
Copy `scripts/bootstrap-wordpress.php` to a private path outside `public_html`
and run from the WordPress root:

```sh
wp eval-file /private/path/bootstrap-wordpress.php --user=<administrator-ID>
wp plugin deactivate spe-site-importer
wp cache flush
wp litespeed-purge all
```

The script runs the importer, sets the site title, and attaches the global
header and footer using the installed Divi 4 Theme Builder API. Re-running
replaces the five page layouts with repository content; back up the database
first if pages have been edited in WordPress. Do not put this CLI script in a
public web directory.

## Production connection

The deployment connection was configured on 2026-10-14 for `shearearth.com`:
SSH host `195.179.239.208`, port `65002`, user `u100732545`, WordPress root
`/home/u100732545/domains/shearearth.com/public_html`. All five GitHub Actions
secrets are configured. The initial file and database backup is stored on the
server outside the web root at
`/home/u100732545/backups/shearearth-prelaunch-20261014/`.

The dedicated local deployment key is ignored by Git in `.deploy-access/`;
its private half is stored as an encrypted GitHub Actions secret. Keep this
directory private.

### Launch verification (2026-10-14)

The redesign is published. All five pages were reviewed in Chrome at 1440px
and 390px: images load, no horizontal overflow or JavaScript exceptions were
observed, and the global header/footer render. The mobile menu and gallery
lightbox work. All ten desktop/mobile video files return HTTP 206 for range
requests. HTTPS is valid, HTTP and `www` redirect to the canonical HTTPS apex,
and `/image-gallery/` redirects permanently to `/gallery/`.

The home hero was subsequently corrected and rechecked at 1440px, 768px and
390px: the logo, heading and supporting text share the viewport's centre,
with consistent spacing and a compact header. The workflow purges WordPress
and LiteSpeed caches after each deployment. The setup plugin is inactive.

Two account settings remain: the contact form targets
`service@shearearth.com`, but the domain currently has no MX records, so an
existing receiving inbox or Hostinger email setup is needed. No test enquiry
has been sent. Divi's theme update username/API key are also not configured;
link the owner's Elegant Themes licence in Divi → Theme Options → Updates.

## Ongoing deploys

Push to `main`. The workflow regenerates the layouts, validates them, and
rsyncs the child theme. Because all the design lives in the theme's
`style.css`, the steady-state payload is around 48 KB and lands in seconds.

The plugin is not deployed on a push. Re-run the workflow manually with the
plugin checkbox if you ever need to re-run the site build — for instance after
adding new photography.

## Upload through WordPress admin

If SSH is not configured yet, create installable ZIPs locally:

```sh
python3 scripts/build-divi.py
python3 scripts/check-layouts.py
python3 scripts/check-php-syntax.py wordpress
python3 scripts/package-wordpress.py
```

With WordPress and licensed Divi installed, upload
`wordpress/dist/shear-performance.zip` under Appearance → Themes → Add New →
Upload Theme, and `wordpress/dist/spe-site-importer.zip` under Plugins → Add
New → Upload Plugin. Then follow steps 4–7 of the server setup above.

The workflow checks that all five secrets are present, validates the private
key, runs PHP's actual syntax checker, and confirms WordPress and the Divi
parent theme exist at the configured server path before syncing files.
The local Python PHP check is structural only; it does not execute PHP.

## Verify after launch

- Confirm HTTPS works for the apex and `www` domain, with one redirecting to
  the chosen canonical domain.
- Check Home, About, Services, Contact and Gallery on desktop and mobile,
  including the global header/footer, navigation, photos and video playback.
- Submit the Contact form and confirm receipt at `service@shearearth.com`.
- Test the gallery lightbox and preserve or redirect the previous
  `/image-gallery/` URL if it is still used.
- Clear Hostinger/LiteSpeed and Divi caches, then check the public site while
  logged out of WordPress.

### A caveat on `--delete`

The theme sync uses `rsync --delete`, so the server's copy is made to match the
repository exactly. That is intended: the theme is fully repository-managed.
It does mean any edit made directly on the server — through the WP file editor,
say — is erased on the next push. Change `style.css` here, not there.
