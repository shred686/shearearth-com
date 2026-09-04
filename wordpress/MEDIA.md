# Project photography and footage

Source: `wetransfer_videos-and-photos_2026-08-24_1650` in the supplied Windows Downloads folder.
The selected photographs show distinct subjects; near-duplicate team and loader
portraits were left out. Original files remain in Downloads.

| Original | Website asset | Placement / subject |
| --- | --- | --- |
| IMG_7698.jpeg | team-and-mulcher.jpg | About and Gallery; team member with equipment |
| IMG_7699.jpeg | mulching-teeth.jpg | Home strip and Gallery; cutting teeth |
| IMG_7700.jpeg | forestry-equipment.jpg | Home strip, Services, Contact and Gallery |
| IMG_7701.jpeg | mulcher-attachment.jpg | Home strip, About and Gallery |
| IMG_7702.jpeg | hydraulic-detail.jpg | About and Gallery; hydraulic connections |
| IMG_7703.jpeg | tracked-loader.jpg | Gallery; Takeuchi tracked loader |
| IMG_7708.jpeg | woodland-worksite.jpg | Home hero, waterfront service context and Gallery |

| Original | Website clip | Source interval | Placement |
| --- | --- | --- | --- |
| IMG_7706.mov | forestry-mulching.mp4 / forestry-mulching-mobile.mp4 | 00:03–00:21 | Home forestry service |
| IMG_7707.mov | brush-removal.mp4 / brush-removal-mobile.mp4 | 00:00–00:14 | Home and Services brush removal |
| IMG_7710.mov | woodland-edge.mp4 / woodland-edge-mobile.mp4 | 00:03–00:21 | Services forestry section and Gallery |
| IMG_7705.mov | clearing-pass.mp4 / clearing-pass-mobile.mp4 | 00:04–00:20 | Gallery |
| IMG_7709.mov | mulcher-at-work.mp4 / mulcher-at-work-mobile.mp4 | 00:02–00:18 | Gallery |

Every clip has a 640×1138 desktop MP4 and a 480×854 mobile MP4, selected below
640px by the video element. Each desktop MP4 has a matching JPEG poster extracted
one second into the clip. Videos retain their full portrait composition and have no audio. No before/after
or waterfront-project claim is made from this material.

Rebuild media first, then layouts:

```sh
python3 scripts/build-media.py --source /path/to/wetransfer-folder
python3 scripts/build-divi.py
python3 scripts/check-layouts.py
python3 scripts/check-php-syntax.py wordpress
```

The importer registers the photos, posters and MP4s, then resolves each layout's
media URLs to the WordPress uploads. Distinct asset filenames let an existing
installation import these alongside its previous archive photos.
