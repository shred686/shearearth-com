# Shear Performance EarthWorks redesign

This repository is the working space for the shearearth.com redesign.

The new site is a WordPress + Divi build and lives in
[`wordpress/`](wordpress/README.md) — a Divi child theme carrying the design
system, five Divi page layouts, and a setup plugin that assembles the site in
one step.

The current public site has been preserved in
[`source/live-site/`](source/live-site/README.md) as a design and content
reference. It is an archive only; build work lives outside that folder.

## Layout

```
wordpress/    the new site — child theme, Divi layouts, setup plugin, preview
scripts/      generators for the layouts, media and preview
source/       point-in-time archive of the old site (read-only reference)
```

## Common tasks

```sh
python3 scripts/build-divi.py            # regenerate layouts, Divi JSON, preview
python3 scripts/build-media.py           # optimize supplied photos and trim video clips
python3 scripts/check-layouts.py         # validate the generated Divi layouts
python3 scripts/check-php-syntax.py wordpress
```

## Deploying

The child theme and setup plugin ship to Hostinger over SSH from GitHub
Actions. See [DEPLOY.md](DEPLOY.md) for the pipeline and the one-time server
setup.

Design source: Claude Design project `8954fb5b`, Option A.
