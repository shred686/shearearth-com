#!/usr/bin/env python3
"""Build the Divi layouts for shearearth.com from a single source of truth.

Everything the site ships is generated here:

  wordpress/plugin/spe-site-importer/layouts/*.txt  Divi shortcode, tokenised
  wordpress/divi/pages/*.json                       per-page Divi exports
  wordpress/divi/shear-performance-library.json     Divi Library export
  wordpress/preview/*.html                          static render, for review

The layout files still contain tokens ({{URL:…}}, {{PAGE:…}}, {{MENU:…}}) that
the importer plugin resolves against the real WordPress install. The JSON and
preview builds resolve them to placeholder values so the files are usable
standalone.
"""

import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "wordpress/plugin/spe-site-importer")
LAYOUT_DIR = os.path.join(PLUGIN, "layouts")
DIVI_DIR = os.path.join(ROOT, "wordpress/divi")
PREVIEW_DIR = os.path.join(ROOT, "wordpress/preview")

DV = "4.27.4"  # _builder_version stamped on every module

PHONE_HREF = "tel:+13142981980"
PHONE_TEXT = "(314) 298-1980"
EMAIL = "service@shearearth.com"


# ---------------------------------------------------------------------------
# Shortcode helpers
# ---------------------------------------------------------------------------

def attrs(**kw):
    """Render shortcode attributes, dropping empties and normalising names."""
    out = []
    for key, value in kw.items():
        if value in (None, ""):
            continue
        out.append(f'{key.rstrip("_")}="{value}"')
    return (" " + " ".join(out)) if out else ""


def module(name, inner="", self_closing=False, **kw):
    base = f'[{name} _builder_version="{DV}" _module_preset="default"{attrs(**kw)} global_colors_info="{{}}"]'
    return base + inner + f"[/{name}]"


def section(*rows, cls="", module_id=None):
    # Every section carries `spe-section`; the child theme keys its layout
    # reset off that one class so component rules can override it cleanly.
    #
    # Spacing deliberately stays out of the shortcode: Divi compiles padding
    # attributes into `!important` rules, which the stylesheet could not then
    # override. All spacing lives in the child theme instead.
    cls = ("spe-section " + cls).strip()
    open_tag = (
        f'[et_pb_section fb_built="1" _builder_version="{DV}" _module_preset="default"'
        f'{attrs(module_id=module_id, module_class=cls)}'
        ' global_colors_info="{}"]'
    )
    return open_tag + "".join(rows) + "[/et_pb_section]"


def row(*columns, structure=None, cls=""):
    open_tag = (
        f'[et_pb_row _builder_version="{DV}" _module_preset="default"'
        f'{attrs(column_structure=structure, module_class=cls)}'
        ' global_colors_info="{}"]'
    )
    return open_tag + "".join(columns) + "[/et_pb_row]"


def column(*modules, kind="4_4", cls=""):
    open_tag = (
        f'[et_pb_column type="{kind}" _builder_version="{DV}" _module_preset="default"'
        f'{attrs(module_class=cls)} global_colors_info="{{}}"]'
    )
    return open_tag + "".join(modules) + "[/et_pb_column]"


def text(inner, cls=""):
    return module("et_pb_text", inner, module_class=cls)


def code(inner, cls=""):
    return module("et_pb_code", inner, module_class=cls)


def image(src, alt, cls=""):
    return module("et_pb_image", module_class=cls, src=src, alt=alt, title_text=alt)


def button(url, label, cls):
    return module("et_pb_button", module_class=cls, button_url=url, button_text=label)


def video_markup(name, title):
    return (
        '<figure class="spe-film">'
        f'<video controls playsinline preload="none" poster="{{{{URL:{name}.jpg}}}}" '
        f'width="640" height="1138" aria-label="{title}">'
        f'<source media="(max-width: 640px)" src="{{{{URL:{name}-mobile.mp4}}}}" type="video/mp4">'
        f'<source src="{{{{URL:{name}.mp4}}}}" type="video/mp4">'
        f'<a href="{{{{URL:{name}.mp4}}}}">Watch {title.lower()}</a></video>'
        f'<figcaption>{title}<span>On site · Silent clip</span></figcaption></figure>'
    )


def photo_markup(name, alt, caption):
    return (
        '<figure class="spe-photo-story">'
        f'<img src="{{{{URL:{name}}}}}" alt="{alt}" loading="lazy" decoding="async">'
        f'<figcaption>{caption}</figcaption></figure>'
    )


def prose(heading, lede, paragraphs, link=None, cls="", module_id=None, visual=None):
    """A centred long-form block: heading, opening line, body, optional link."""
    body = f"<h2>{heading}</h2><p class=\"spe-lede\">{lede}</p>"
    body += "".join(f"<p>{p}</p>" for p in paragraphs)
    if link:
        body += f'<a class="spe-more" href="{link[0]}">{link[1]}</a>'
    classes = " ".join(filter(None, ["spe-prose", cls]))
    if visual:
        return section(row(column(text(body), kind="1_2"), column(code(visual), kind="1_2"),
                           structure="1_2,1_2"), cls=classes + " spe-story", module_id=module_id)
    return section(row(column(text(body))), cls=classes, module_id=module_id)


def cta_band(panel=True, copy=None):
    """The "Have any questions?" block that closes most pages."""
    copy = copy or (
        "We are always open to talk about your business, new projects, "
        "creative opportunities and how we can help you."
    )
    classes = "spe-cta spe-duo"
    if panel:
        classes += " spe-panel"
    return section(
        row(
            column(text(
                '<div class="spe-eyebrow">Talk to us</div>'
                "<h2>Have any questions?</h2>"
                f"<p>{copy}</p>"
            ), kind="1_2"),
            column(
                button("{{PAGE:contact}}", "Get in touch", "spe-btn-primary"),
                button(PHONE_HREF, PHONE_TEXT, "spe-btn-ghost"),
                kind="1_2",
                cls="spe-actions",
            ),
            structure="1_2,1_2",
        ),
        cls=classes,
    )


def page_head(eyebrow, title, extra=None):
    """The title band at the top of every interior page."""
    head = text(f'<div class="spe-eyebrow">{eyebrow}</div><h1>{title}</h1>')
    if extra is None:
        return section(row(column(head)), cls="spe-page-head")
    return section(
        row(
            column(head, kind="1_2"),
            column(extra, kind="1_2"),
            structure="1_2,1_2",
        ),
        cls="spe-page-head spe-page-head--split",
    )


# ---------------------------------------------------------------------------
# Global header and footer (Divi Theme Builder)
# ---------------------------------------------------------------------------

BRAND_HEADER = (
    '<a class="spe-brand" href="{{HOME}}">'
    '<img src="{{URL:logo-mark.png}}" width="260" height="255" alt="Shear Performance EarthWorks">'
    "<span>"
    '<span class="spe-brand__name">Shear Performance</span>'
    '<span class="spe-brand__sub">EarthWorks</span>'
    "</span></a>"
)

BRAND_FOOTER = (
    '<a class="spe-brand" href="{{HOME}}">'
    '<img src="{{URL:logo-mark.png}}" width="260" height="255" alt="">'
    '<span class="spe-brand__name">Shear Performance EarthWorks</span></a>'
)

HEADER = section(
    row(
        column(code(BRAND_HEADER), kind="1_4", cls="spe-header-brand"),
        column(
            module(
                "et_pb_menu",
                menu_id="{{MENU:primary}}",
                module_class="spe-header-menu",
                background_color="RGBA(255,255,255,0)",
                submenu_direction="downwards",
            ),
            kind="1_2",
            cls="spe-header-nav",
        ),
        column(button(PHONE_HREF, PHONE_TEXT, "spe-phone"), kind="1_4", cls="spe-header-cta"),
        structure="1_4,1_2,1_4",
    ),
    cls="spe-header",
)

FOOTER = section(
    row(
        column(code(BRAND_FOOTER), kind="1_3", cls="spe-footer-brand"),
        column(
            module(
                "et_pb_menu",
                menu_id="{{MENU:footer}}",
                module_class="spe-footer-menu",
                background_color="RGBA(255,255,255,0)",
            ),
            kind="1_3",
            cls="spe-footer-nav",
        ),
        column(
            text("<p>©{{YEAR}} Shear Performance EarthWorks</p>", cls="spe-copyright"),
            kind="1_3",
            cls="spe-footer-legal",
        ),
        structure="1_3,1_3,1_3",
    ),
    cls="spe-footer",
)


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

HOME = "".join([
    section(
        row(column(code('<img class="spe-hero-background" src="{{URL:woodland-worksite.jpg}}" alt="" fetchpriority="high">')), cls="spe-hero-backdrop"),
        row(column(
            image("{{URL:logo.png}}", "Shear Performance EarthWorks", cls="spe-hero-logo"),
            text(
                "<h1>Environmentally responsible forestry mulching and land management.</h1>"
                '<p class="spe-hero-sub">Locally owned and operated in St.&nbsp;Louis.</p>'
            ),
        )),
        row(
            column(
                button("{{PAGE:contact}}", "Get in touch", "spe-btn-primary"),
                button("{{PAGE:services}}", "Our services", "spe-btn-ghost"),
                cls="spe-actions spe-actions--center",
            ),
            cls="spe-hero-actions",
        ),
        cls="spe-hero",
    ),

    section(
        row(column(
            image("{{URL:mulching-teeth.jpg}}", "Close-up of the forestry mulcher cutting teeth"),
            image("{{URL:woodland-worksite.jpg}}", "Tracked mulcher at the edge of a wooded property"),
            image("{{URL:mulcher-attachment.jpg}}", "Forestry mulching attachment on the tracked loader"),
            image("{{URL:forestry-equipment.jpg}}", "Tracked loader and forestry mulching head"),
        )),
        cls="spe-strip",
    ),

    prose(
        "Forestry Mulching",
        "Take the first step towards creating a beautiful and sustainable forest ecosystem.",
        [
            "Our forestry mulching services not only reduce fuel costs but also promote healthy "
            "tree growth, improve soil quality, and increase biodiversity. We use eco-friendly "
            "equipment to chop your trees into manageable pieces, leaving behind a tidy and "
            "attractive landscape that&#8217;s perfect for wildlife habitats or outdoor "
            "recreational areas.",
            "Trust us to handle your forestry mulching needs and enjoy the benefits of a thriving "
            "forest for years to come.",
        ],
        link=("{{PAGE:services}}", "Learn more →"),
        cls="spe-pad-top-96",
        visual=video_markup("forestry-mulching", "Forestry mulching in action"),
    ),


    prose(
        "Waterfront Land Clearing",
        "Imagine waking up every morning to the serene beauty of your own waterfront property, "
        "free from debris and obstacles.",
        [
            "Our waterfront land clearing services help you achieve this vision by safely removing "
            "unwanted vegetation, trees, and other obstructions that may be hindering your "
            "property&#8217;s full potential. We&#8217;ll work with you to create a seamless and "
            "functional space that showcases the natural beauty of your waterfront location.",
            "Let us handle the hard work, so you can enjoy the rewards.",
        ],
        link=("{{PAGE:services}}", "Learn more →"),
        cls="spe-pad-top-88",
        visual=photo_markup("woodland-worksite.jpg", "Mulcher working along a wooded property edge", "Careful clearing begins with understanding your property."),
    ),


    prose(
        "Brush Removal",
        "Are dense brush and overgrown vegetation getting in the way of your outdoor recreation "
        "or property maintenance?",
        [
            "Our brush removal services are designed to help you clear unwanted vegetation and "
            "create a safe, accessible space for you and your loved ones. Whether it&#8217;s for "
            "firewood, mulch, or simply a more manageable landscape, we&#8217;ll work with you to "
            "develop a customized solution that meets your needs and budget.",
            "Trust us to handle the tough job, so you can enjoy a stress-free outdoor experience.",
        ],
        link=("{{PAGE:services}}", "Learn more →"),
        cls="spe-pad-top-88",
        visual=video_markup("brush-removal", "Working through dense brush"),
    ),


    section(
        row(
            column(text(
                '<div class="spe-eyebrow">About us</div>'
                "<h2>Sustainable practices, from small projects to large-scale clearing.</h2>"
            ), kind="1_2"),
            column(text(
                "<p>At Shear Performance EarthWorks, we&#8217;re dedicated to providing "
                "environmentally responsible forestry mulching and land management services that "
                "meet the unique needs of your property. With a focus on sustainable practices, we "
                "handle all types of forestry projects, from small-scale vegetation management to "
                "large-scale land clearing.</p>"
                "<p>As a locally owned and operated company in St. Louis, our team of experienced "
                "professionals has the expertise and equipment necessary to tackle even the most "
                "complex projects. We take pride in delivering exceptional service, working closely "
                "with you to ensure that your property receives the care it deserves.</p>"
                "<p>Contact us today or call to schedule a consultation and let&#8217;s work "
                "together to achieve your land management goals.</p>"
                '<a class="spe-more" href="{{PAGE:about}}">More about us</a>',
                cls="spe-body-copy",
            ), kind="1_2"),
            structure="1_2,1_2",
        ),
        cls="spe-band-about spe-duo spe-duo--top spe-duo--wide",
    ),

    cta_band(panel=False),
])


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------

ABOUT = "".join([
    page_head("About", "Who are we?"),
    section(
        row(
            column(text(
                "<h2>Our mission</h2>"
                '<p class="spe-lede">At Shear Performance EarthWorks, we are dedicated to clearing '
                "the way for sustainable land management practices.</p>"
                "<p>We believe that responsible forestry practices are essential for maintaining "
                "healthy ecosystems and preserving natural resources for future generations.</p>"
                "<p>With years of experience in land clearing and forestry mulching, we&#8217;re "
                "committed to delivering exceptional results while minimizing our impact on the "
                "environment.</p>"
            ), kind="1_2", cls="spe-about-copy"),
            column(
                image("{{URL:team-and-mulcher.jpg}}", "Shear Performance team member beside the forestry mulcher"),
                image("{{URL:hydraulic-detail.jpg}}", "Hydraulic connections on the mulching attachment"),
                image("{{URL:mulcher-attachment.jpg}}", "Forestry mulching attachment on the tracked loader"),
                kind="1_2",
                cls="spe-about-media",
            ),
            structure="1_2,1_2",
        ),
        cls="spe-duo spe-duo--top spe-duo--wide spe-pad-top-80 spe-pad-bot-80",
    ),
    cta_band(),
])


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

ANCHOR_NAV = (
    '<nav class="spe-anchor-nav">'
    '<a href="#forestry-mulching">Forestry Mulching</a>'
    '<a href="#waterfront-land-clearing">Waterfront Land Clearing</a>'
    '<a href="#brush-removal">Brush Removal</a>'
    "</nav>"
)

SERVICES = "".join([
    page_head("What we do", "Services", extra=code(ANCHOR_NAV)),

    prose(
        "Forestry Mulching",
        "Take the first step towards creating a beautiful and sustainable forest ecosystem with "
        "our Forestry Mulching services.",
        [
            "Not only do our expertly managed mulch programs reduce fuel costs and promote healthy "
            "tree growth, but they also improve soil quality, increase biodiversity, and enhance "
            "the overall aesthetic appeal of your property. Our eco-friendly equipment is designed "
            "to chop your trees into manageable pieces, leaving behind a tidy and attractive "
            "landscape that&#8217;s perfect for wildlife habitats, outdoor recreational areas, or "
            "simply enjoying nature.",
            "You&#8217;ll not only be investing in a more sustainable future, but also ensuring "
            "that your investment is guided by our years of expertise and commitment to "
            "environmental stewardship.",
        ],
        cls="spe-prose--sm spe-pad-top-80 spe-anchor",
        module_id="forestry-mulching",
        visual=video_markup("woodland-edge", "Mulching along the woodland edge"),
    ),

    prose(
        "Waterfront Land Clearing",
        "Imagine waking up every morning to the serene beauty of your own waterfront property, "
        "free from debris and obstacles.",
        [
            "Our Waterfront Land Clearing services help you achieve this vision by safely removing "
            "unwanted vegetation, trees, and other obstructions that may be hindering your "
            "property&#8217;s full potential. But it&#8217;s not just about aesthetics – our expert "
            "team also understands the importance of ensuring safe and stable shorelines. "
            "We&#8217;ll work with you to create a comprehensive plan that addresses any shoreline "
            "stabilization needs, from gentle slopes to steep banks.",
            "We&#8217;ll work closely with you to bring your waterfront vision to life. Our years "
            "of experience in waterfront land clearing has given us the expertise to navigate "
            "complex terrain and ensure seamless integration of our services with your existing "
            "infrastructure.",
            "Have a beautiful and functional waterfront space that not only enhances your quality "
            "of life but also protects your investment for generations to come.",
        ],
        cls="spe-prose--sm spe-pad-top-72 spe-anchor",
        module_id="waterfront-land-clearing",
        visual=photo_markup("forestry-equipment.jpg", "Tracked loader with forestry mulching attachment", "The equipment behind our land clearing services."),
    ),

    prose(
        "Brush Removal",
        "Are dense brush and overgrown vegetation getting in the way of your outdoor recreation "
        "or property maintenance?",
        [
            "Our Brush Removal services are designed to help you clear unwanted vegetation and "
            "create a safe, accessible space for you and your loved ones. But it&#8217;s not just "
            "about removing the brush – we&#8217;ll also assess the underlying conditions that led "
            "to its growth in the first place. Our team of experts will identify the root causes of "
            "overgrowth, whether it&#8217;s due to erosion, poor soil quality, or other factors.",
            "We&#8217;ll work with you to develop a customized solution that meets your needs and "
            "budget. From firewood production to mulch delivery, we&#8217;ll provide you with a "
            "variety of options for utilizing your cleared brush. And, if needed, our team will "
            "also perform any necessary habitat restoration or erosion control measures to ensure "
            "the long-term health of your property.",
            "Enjoy a safer, more accessible outdoor space that&#8217;s perfect for recreation, "
            "relaxation, or simply enjoying nature.",
        ],
        cls="spe-prose--sm spe-pad-top-72 spe-pad-bot-88 spe-anchor",
        module_id="brush-removal",
        visual=video_markup("brush-removal", "Brush removal in action"),
    ),

    cta_band(copy="We are always open to discussing your business, new projects, creative "
                  "opportunities, and how we can help you."),
])


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

CONTACT_FIELDS = "".join(
    module(
        "et_pb_contact_field",
        field_id=fid,
        field_title=title,
        field_type=ftype,
        fullwidth_field="on",
        required_mark="on" if required else "off",
    )
    for fid, title, ftype, required in [
        ("Name", "Your name", "input", True),
        ("Phone", "Phone number", "input", True),
        ("Email", "Email", "email", False),
        ("Message", "Message", "text", True),
    ]
)

CONTACT_FORM = module(
    "et_pb_contact_form",
    CONTACT_FIELDS,
    module_class="spe-form",
    captcha="off",
    email=EMAIL,
    title="",
    custom_message="Name: %%Name%%||Phone: %%Phone%%||Email: %%Email%%||Message: %%Message%%",
    success_message="Thank you — your message is on its way. We&#8217;ll be in touch shortly. "
                    "For anything urgent, call (314) 298-1980.",
    submit_button_text="Send now",
)

CONTACT_DETAILS = (
    '<div class="spe-contact-row">'
    '<div class="spe-contact-row__label">Email</div>'
    f'<div class="spe-contact-row__value"><a href="mailto:{EMAIL}">{EMAIL}</a></div></div>'
    '<div class="spe-contact-row">'
    '<div class="spe-contact-row__label">Phone number</div>'
    '<div class="spe-contact-row__value spe-contact-row__value--lg">'
    f'<a href="{PHONE_HREF}">314-298-1980</a></div></div>'
    '<div class="spe-contact-row">'
    '<div class="spe-contact-row__label">Address</div>'
    '<div class="spe-contact-row__value">Saint Louis, MO 63135</div></div>'
)

CONTACT = "".join([
    page_head("Contact us", "Get in touch"),
    section(
        row(
            column(CONTACT_FORM, kind="1_2"),
            column(
                text("<h2>Talk to us</h2>"),
                code(CONTACT_DETAILS),
                image("{{URL:forestry-equipment.jpg}}", "Tracked loader and forestry mulching head",
                      cls="spe-contact-photo"),
                kind="1_2",
                cls="spe-contact-details",
            ),
            structure="1_2,1_2",
        ),
        cls="spe-contact",
    ),
])


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------

GALLERY_PHOTOS = {
    "team-and-mulcher.jpg": "Our team and forestry mulcher",
    "forestry-equipment.jpg": "Tracked loader with forestry mulching head",
    "mulching-teeth.jpg": "A closer look at the mulching teeth",
    "woodland-worksite.jpg": "Working at the woodland edge",
    "mulcher-attachment.jpg": "Forestry mulching attachment",
    "hydraulic-detail.jpg": "Hydraulic connections on the attachment",
    "tracked-loader.jpg": "Takeuchi tracked loader on site",
}
GALLERY_IDS = ",".join("{{ID:%s}}" % name for name in GALLERY_PHOTOS)

GALLERY = "".join([
    page_head("Our work", "Out in the field"),
    section(row(column(text('<p class="spe-lede">Meet the people and equipment behind the work. '
                            'Explore our photos, then watch short clips from the field.</p>'))), cls="spe-gallery-intro"),
    section(
        row(column(module(
            "et_pb_gallery",
            gallery_ids=GALLERY_IDS,
            module_class="spe-gallery",
            fullwidth="off",
            posts_number="12",
            orientation="landscape",
            show_title_and_caption="off",
            show_pagination="off",
        ))),
        cls="spe-gallery-section spe-pad-top-56 spe-pad-bot-88",
    ),
    section(row(column(text('<div class="spe-eyebrow">See the process</div><h2>Land clearing in motion</h2>'),
        code('<div class="spe-film-grid">' +
             video_markup("clearing-pass", "A clearing pass through the trees") +
             video_markup("mulcher-at-work", "The mulcher at work") +
             video_markup("woodland-edge", "Opening up the woodland edge") + '</div>'))),
        cls="spe-motion-gallery spe-pad-bot-88"),
    cta_band(),
])


PAGES = {
    "home": ("Home", "home", HOME),
    "about": ("About", "about", ABOUT),
    "services": ("Services", "services", SERVICES),
    "contact": ("Contact", "contact", CONTACT),
    "gallery": ("Gallery", "gallery", GALLERY),
}

TEMPLATES = {
    "header": ("SPE Global Header", HEADER),
    "footer": ("SPE Global Footer", FOOTER),
}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_layouts():
    os.makedirs(LAYOUT_DIR, exist_ok=True)
    for slug, (_title, _slug, content) in PAGES.items():
        with open(os.path.join(LAYOUT_DIR, f"{slug}.txt"), "w") as fh:
            fh.write(content)
    for slug, (_title, content) in TEMPLATES.items():
        with open(os.path.join(LAYOUT_DIR, f"{slug}.txt"), "w") as fh:
            fh.write(content)
    print(f"layouts  -> {LAYOUT_DIR} ({len(PAGES) + len(TEMPLATES)} files)")


def resolve(content, media_base, page_base="/", year="2026"):
    """Swap the importer's tokens for concrete values."""
    content = content.replace("{{HOME}}", page_base)
    content = content.replace("{{YEAR}}", year)
    content = re.sub(r"\{\{URL:([^}]+)\}\}", lambda m: media_base + m.group(1), content)
    content = re.sub(r"\{\{PAGE:([^}]+)\}\}",
                     lambda m: page_base + ("" if m.group(1) == "home" else m.group(1) + "/"),
                     content)
    # Placeholder attachment ids; the Divi Library importer remaps these when
    # the gallery is opened, and the plugin never sees them.
    ids = iter(range(101, 200))
    content = re.sub(r"\{\{ID:[^}]+\}\}", lambda m: str(next(ids)), content)
    content = re.sub(r"\{\{MENU:[^}]+\}\}", "0", content)
    return content


def write_page_exports():
    """Per-page exports, importable from a page's builder Portability panel."""
    out_dir = os.path.join(DIVI_DIR, "pages")
    os.makedirs(out_dir, exist_ok=True)
    media_base = "https://www.shearearth.com/wp-content/uploads/spe/"
    for index, (slug, (_title, _s, content)) in enumerate(PAGES.items(), start=1):
        payload = {
            "context": "et_builder",
            "data": {str(index): resolve(content, media_base)},
            "presets": {},
            "global_colors": [],
            "images": {},
            "thumbnails": [],
        }
        with open(os.path.join(out_dir, f"{slug}.json"), "w") as fh:
            json.dump(payload, fh, ensure_ascii=False)
    print(f"pages    -> {out_dir} ({len(PAGES)} files)")


def library_item(post_id, title, content):
    """One entry in a Divi Library (et_builder_layouts) export."""
    stamp = "2026-08-26 12:00:00"
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return {
        "ID": post_id,
        "post_date": stamp,
        "post_date_gmt": stamp,
        "post_content": content,
        "post_title": title,
        "post_excerpt": "",
        "post_status": "publish",
        "comment_status": "closed",
        "ping_status": "closed",
        "post_password": "",
        "post_name": slug,
        "to_ping": "",
        "pinged": "",
        "post_modified": stamp,
        "post_modified_gmt": stamp,
        "post_content_filtered": "",
        "post_parent": 0,
        "menu_order": 0,
        "post_type": "et_pb_layout",
        "post_mime_type": "",
        "comment_count": "0",
        "filter": "raw",
        "post_meta": {"_et_pb_built_for_post_type": ["page"]},
        "terms": {
            "2": {"name": "layout", "slug": "layout", "taxonomy": "layout_type",
                  "parent": 0, "all_parents": [], "description": ""},
            "8": {"name": "not_global", "slug": "not_global", "taxonomy": "scope",
                  "parent": 0, "all_parents": [], "description": ""},
            "9": {"name": "regular", "slug": "regular", "taxonomy": "module_width",
                  "parent": 0, "all_parents": [], "description": ""},
            "4": {"name": "Shear Performance", "slug": "shear-performance",
                  "taxonomy": "layout_category", "parent": 0, "all_parents": [],
                  "description": ""},
        },
    }


def write_library_export():
    """One file holding the header, the footer and all five page layouts.

    Imported from Divi → Divi Library, this is what the Theme Builder's
    "Add From Library" picker reads the global header and footer from.
    """
    os.makedirs(DIVI_DIR, exist_ok=True)
    media_base = "https://www.shearearth.com/wp-content/uploads/spe/"
    data = {}
    post_id = 1001
    for _slug, (title, content) in TEMPLATES.items():
        data[str(post_id)] = library_item(post_id, title, resolve(content, media_base))
        post_id += 1
    for _slug, (title, _s, content) in PAGES.items():
        data[str(post_id)] = library_item(post_id, f"SPE {title}", resolve(content, media_base))
        post_id += 1

    payload = {
        "context": "et_builder_layouts",
        "data": data,
        "defaults": "",
        "images": [],
    }
    path = os.path.join(DIVI_DIR, "shear-performance-library.json")
    with open(path, "w") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    print(f"library  -> {path} ({len(data)} layouts)")


# ---------------------------------------------------------------------------
# Static preview — renders the shortcode the way Divi does, so the child
# theme CSS can be checked in a browser without a WordPress install.
# ---------------------------------------------------------------------------

SHORTCODE_RE = re.compile(r"\[(/?)([a-z_]+)([^\]]*)\]")
ATTR_RE = re.compile(r'([a-z_0-9]+)="([^"]*)"')

NAV_ITEMS = [("Home", "home"), ("About", "about"), ("Services", "services"),
             ("Contact", "contact"), ("Gallery", "gallery")]


def parse_attrs(raw):
    return dict(ATTR_RE.findall(raw))


def render_menu(a, current, extra_class):
    items = []
    for label, slug in NAV_ITEMS:
        href = "index.html" if slug == "home" else f"{slug}.html"
        cls = "current-menu-item" if slug == current else ""
        items.append(f'<li class="menu-item {cls}"><a href="{href}">{label}</a></li>')
    return (
        f'<div class="et_pb_module et_pb_menu {extra_class}">'
        '<div class="et_pb_menu_inner_container"><div class="et_pb_menu__wrap">'
        '<div class="et_pb_menu__menu"><nav class="et-menu-nav"><ul class="et-menu">'
        + "".join(items) +
        '</ul></nav></div>'
        '<div class="et_mobile_nav_menu"><details class="spe-preview-menu"><summary>Menu</summary>'
        '<nav aria-label="Mobile navigation"><ul>' + "".join(items) + '</ul></nav></details></div>'
        "</div></div></div>"
    )


def render_gallery(a):
    items = "".join(
        '<div class="et_pb_gallery_item et_pb_grid_item">'
        f'<div class="et_pb_gallery_image"><a href="media/{n}" aria-label="View {alt.lower()}">'
        f'<img src="media/{n}" alt="{alt}" loading="lazy" decoding="async">'
        '<span class="et_overlay"></span></a></div></div>'
        for n, alt in GALLERY_PHOTOS.items()
    )
    return (
        f'<div class="et_pb_module et_pb_gallery {a.get("module_class", "")}">'
        '<div class="et_pb_gallery_items et_post_gallery clearfix">' + items + "</div></div>"
    )


def render_contact_form(a, fields):
    rows = []
    for f in fields:
        fid = f.get("field_id", "")
        title = f.get("field_title", "")
        mark = ' <span class="required">*</span>' if f.get("required_mark") == "on" else ""
        control = (
            f'<textarea class="et_pb_contact_message" id="{fid}" name="{fid}" placeholder="{title}"></textarea>'
            if f.get("field_type") == "text"
            else f'<input type="{"email" if f.get("field_type") == "email" else "tel" if fid == "Phone" else "text"}" '
                 f'id="{fid}" name="{fid}" class="input" placeholder="{title}">'
        )
        rows.append(
            f'<p class="et_pb_contact_field et_pb_contact_field_last" data-id="{fid}">'
            f'<label class="et_pb_contact_form_label" for="{fid}">{title}{mark}</label>'
            f"{control}</p>"
        )
    return (
        f'<div class="et_pb_module et_pb_contact_form_container clearfix {a.get("module_class", "")}">'
        '<div class="et-pb-contact-message"></div>'
        '<div class="et_pb_contact"><form class="et_pb_contact_form clearfix">'
        + "".join(rows) +
        '<div class="et_contact_bottom_container">'
        f'<button type="submit" class="et_pb_contact_submit et_pb_button">'
        f'{a.get("submit_button_text", "Submit")}</button></div>'
        "</form></div></div>"
    )


def render_preview_body(content, current):
    """Walk the shortcode and emit the DOM Divi would emit for these modules."""
    out = []
    stack = []
    pos = 0
    pending_fields = []
    form_attrs = None

    for m in SHORTCODE_RE.finditer(content):
        inner = content[pos:m.start()]
        pos = m.end()
        closing, tag, raw = m.group(1), m.group(2), m.group(3)
        a = parse_attrs(raw)

        if closing:
            if tag == "et_pb_contact_form":
                out.append(render_contact_form(form_attrs, pending_fields))
                pending_fields, form_attrs = [], None
            elif tag == "et_pb_contact_field":
                pass
            elif tag in ("et_pb_text", "et_pb_code"):
                out.append(inner)
                out.append("</div></div>" if tag == "et_pb_text" else "</div>")
            elif tag == "et_pb_button":
                out.append("</a></div>")
            elif stack and stack[-1] == tag:
                stack.pop()
                out.append("</div>")
            continue

        cls = a.get("module_class", "")
        if tag == "et_pb_section":
            mid = f' id="{a["module_id"]}"' if "module_id" in a else ""
            out.append(f'<div class="et_pb_section {cls}"{mid}>')
            stack.append(tag)
        elif tag == "et_pb_row":
            structure = a.get("column_structure", "4_4").replace(",", "_")
            out.append(f'<div class="et_pb_row et_pb_gutters3 et_pb_row_{structure} {cls}">')
            stack.append(tag)
        elif tag == "et_pb_column":
            kind = a.get("type", "4_4")
            out.append(f'<div class="et_pb_column et_pb_column_{kind} {cls}">')
            stack.append(tag)
        elif tag == "et_pb_text":
            out.append(f'<div class="et_pb_module et_pb_text {cls}"><div class="et_pb_text_inner">')
        elif tag == "et_pb_code":
            out.append(f'<div class="et_pb_module et_pb_code {cls}">')
        elif tag == "et_pb_image":
            src = a.get("src", "")
            alt = html.escape(a.get("alt", ""), quote=True)
            out.append(
                f'<div class="et_pb_module et_pb_image {cls}">'
                f'<span class="et_pb_image_wrap"><img src="{src}" alt="{alt}" decoding="async" loading="lazy"></span></div>'
            )
        elif tag == "et_pb_button":
            out.append(
                f'<div class="et_pb_button_module_wrapper et_pb_module {cls}">'
                f'<a class="et_pb_button" href="{a.get("button_url", "#")}">'
                f'{a.get("button_text", "")}'
            )
        elif tag == "et_pb_menu":
            out.append(render_menu(a, current, cls))
        elif tag == "et_pb_gallery":
            out.append(render_gallery(a))
        elif tag == "et_pb_contact_form":
            form_attrs = a
        elif tag == "et_pb_contact_field":
            pending_fields.append(a)

    return "".join(out)


PREVIEW_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Shear Performance EarthWorks</title>
<link rel="icon" href="media/logo-mark.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="divi-baseline.css">
<link rel="stylesheet" href="style.css">
</head>
<body class="spe-site">
<div id="page-container">
<div id="et-boc" class="et-boc">
<div class="et-l et-l--header">{header}</div>
<div id="et-main-area"><div id="main-content"><article><div class="entry-content">{body}</div></article></div></div>
<div class="et-l et-l--footer">{footer}</div>
</div>
</div>
</body>
</html>
"""

# The slice of Divi's own stylesheet the layouts actually depend on. Without a
# Divi licence we cannot ship the real file, so the preview approximates the
# handful of rules the child theme is written against.
DIVI_BASELINE = """
.spe-preview-menu summary { cursor: pointer; color: #fff; padding: 12px; min-height: 44px; border: 1px solid #3d5a45; border-radius: 4px; }
.spe-preview-menu nav { position: absolute; left: var(--spe-gutter); right: var(--spe-gutter); top: 100%; max-height: 70vh; overflow-y: auto; background: #12160f; padding: 16px; border: 1px solid #3d5a45; }
.spe-preview-menu nav a { color: #fff; display: block; padding: 10px; }
/* Approximation of the Divi base rules the child theme overrides.
   Preview only — the real Divi stylesheet supplies these on the live site. */
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; font-size: 14px; line-height: 1.7em; color: #666; }
img { max-width: 100%; height: auto; }
p { padding-bottom: 1em; margin: 0; }
h1, h2, h3, h4, h5, h6 { color: #333; padding-bottom: 10px; line-height: 1em; font-weight: 500; margin: 0; }
a { text-decoration: none; color: #2ea3f2; }
ul { margin: 0; padding: 0; list-style: none; }
.et_pb_section { position: relative; background-color: #fff; padding: 4% 0; }
.et_pb_row { position: relative; width: 80%; max-width: 1080px; margin: auto; padding: 2% 0; }
.et_pb_row::after { content: ""; display: block; clear: both; }
.et_pb_column { float: left; position: relative; z-index: 9; min-height: 1px; }
.et_pb_row_4_4 .et_pb_column_4_4 { width: 100%; }
.et_pb_row_1_2_1_2 .et_pb_column_1_2 { width: 48.5%; margin-right: 3%; }
.et_pb_row_1_2_1_2 .et_pb_column_1_2:last-child { margin-right: 0; }
.et_pb_row_1_3_1_3_1_3 .et_pb_column_1_3 { width: 31.333%; margin-right: 3%; }
.et_pb_row_1_3_1_3_1_3 .et_pb_column_1_3:last-child { margin-right: 0; }
.et_pb_row_1_4_1_2_1_4 .et_pb_column_1_4 { width: 22.75%; margin-right: 3%; }
.et_pb_row_1_4_1_2_1_4 .et_pb_column_1_2 { width: 48.5%; margin-right: 3%; }
.et_pb_row_1_4_1_2_1_4 .et_pb_column_1_4:last-child { margin-right: 0; }
.et_pb_module { margin-bottom: 30px; }
.et_pb_image { display: block; margin-left: auto; margin-right: auto; }
.et_pb_image .et_pb_image_wrap { display: inline-block; position: relative; }
body #page-container .et_pb_button {
  display: inline-block; color: #2ea3f2; border: 2px solid; border-radius: 3px;
  padding: 0.3em 1em; line-height: 1.7em; background-color: transparent;
  font-size: 20px; position: relative;
}
body #page-container .et_pb_button:after {
  font-family: ETmodules; content: "5"; position: absolute; opacity: 0;
}
.et_pb_menu { background-color: #fff; }
.et_pb_menu__wrap { display: flex; flex: 1 1 auto; align-items: center; }
.et_pb_menu__menu { flex-grow: 1; display: flex; }
.et_pb_menu__menu > nav > ul { display: flex; flex-wrap: wrap; }
.et_pb_menu .et-menu > li { padding-left: 11px; padding-right: 11px; }
.et_pb_menu .et-menu > li > a { color: rgba(0,0,0,0.6); display: block; }
.et_mobile_nav_menu { display: none; }
.et_pb_gallery_items::after { content: ""; display: block; clear: both; }
.et_pb_gallery_item { float: left; width: 22.75%; margin: 0 3% 3% 0; }
.et_pb_gallery_image { position: relative; overflow: hidden; }
.et_pb_gallery_image img { display: block; width: 100%; }
.et_overlay { position: absolute; inset: 0; opacity: 0; transition: opacity .3s; }
.et_pb_gallery_image:hover .et_overlay { opacity: 1; }
.et_pb_contact_form_container { margin-bottom: 30px; }
.et_pb_contact_form_label { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
.et_pb_contact_field { padding: 0 3% 3% 0; float: left; width: 100%; }
.et_pb_contact p input, .et_pb_contact p textarea {
  width: 100%; background-color: #eee; border: none; padding: 16px; color: #999;
  font-size: 14px; border-radius: 0;
}
.et_contact_bottom_container { float: right; text-align: right; }
.clearfix::after { content: ""; display: block; clear: both; }
"""


def write_preview():
    """Render the layouts as plain HTML so the CSS can be reviewed in a browser."""
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    media_base = "media/"

    with open(os.path.join(PREVIEW_DIR, "divi-baseline.css"), "w") as fh:
        fh.write(DIVI_BASELINE.lstrip())

    # The preview loads the real child-theme stylesheet, unmodified.
    theme_css = os.path.join(ROOT, "wordpress/themes/shear-performance/style.css")
    with open(theme_css) as src, open(os.path.join(PREVIEW_DIR, "style.css"), "w") as dst:
        dst.write(src.read())

    media_out = os.path.join(PREVIEW_DIR, "media")
    os.makedirs(media_out, exist_ok=True)
    for name in os.listdir(os.path.join(PLUGIN, "media")):
        with open(os.path.join(PLUGIN, "media", name), "rb") as src, \
                open(os.path.join(media_out, name), "wb") as dst:
            dst.write(src.read())

    def to_local(markup):
        for slug in ("contact", "services", "about", "gallery"):
            markup = markup.replace(f'href="{slug}/"', f'href="{slug}.html"')
        return markup.replace('href=""', 'href="index.html"')

    for slug, (title, _s, content) in PAGES.items():
        page_header = render_preview_body(
            to_local(resolve(HEADER, media_base, page_base="")), slug)
        page_footer = render_preview_body(
            to_local(resolve(FOOTER, media_base, page_base="")), slug)
        body = render_preview_body(to_local(resolve(content, media_base, page_base="")), slug)
        filename = "index.html" if slug == "home" else f"{slug}.html"
        with open(os.path.join(PREVIEW_DIR, filename), "w") as fh:
            fh.write(PREVIEW_SHELL.format(title=title, header=page_header,
                                          footer=page_footer, body=body))
    print(f"preview  -> {PREVIEW_DIR} ({len(PAGES)} pages)")


if __name__ == "__main__":
    write_layouts()
    write_page_exports()
    write_library_export()
    write_preview()
