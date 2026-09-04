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

## Ongoing deploys

Push to `main`. The workflow regenerates the layouts, validates them, and
rsyncs the child theme. Because all the design lives in the theme's
`style.css`, the steady-state payload is around 48 KB and lands in seconds.

The plugin is not deployed on a push. Re-run the workflow manually with the
plugin checkbox if you ever need to re-run the site build — for instance after
adding new photography.

### A caveat on `--delete`

The theme sync uses `rsync --delete`, so the server's copy is made to match the
repository exactly. That is intended: the theme is fully repository-managed.
It does mean any edit made directly on the server — through the WP file editor,
say — is erased on the next push. Change `style.css` here, not there.
