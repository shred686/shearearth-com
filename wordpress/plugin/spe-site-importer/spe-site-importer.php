<?php
/**
 * Plugin Name: Shear Performance Site Setup
 * Description: Builds the Shear Performance EarthWorks site — uploads the photography, creates the five Divi pages, wires up the menus, and adds the global header and footer to the Divi Library.
 * Version:     1.0.0
 * Author:      Shear Performance EarthWorks
 * License:     GPL-2.0-or-later
 *
 * Run it once from Tools → Shear Performance Setup. Running it again is safe:
 * media is matched by filename, pages by slug, and menus are only filled when
 * empty, so a second run updates rather than duplicates.
 *
 * @package spe-site-importer
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'SPE_IMPORTER_DIR', plugin_dir_path( __FILE__ ) );

/**
 * The five pages, in menu order. Keys match the layout filenames.
 */
function spe_pages() {
	return array(
		'home'     => 'Home',
		'about'    => 'About',
		'services' => 'Services',
		'contact'  => 'Contact',
		'gallery'  => 'Gallery',
	);
}

/**
 * Images shipped with the plugin, with the alt text the layouts expect.
 */
function spe_media() {
	return array(
		'logo.png'            => 'Shear Performance EarthWorks',
		'logo-mark.png'       => 'Shear Performance EarthWorks',
		'team-and-mulcher.jpg' => 'Shear Performance team member beside the forestry mulcher',
		'mulching-teeth.jpg' => 'Close-up of the forestry mulcher cutting teeth',
		'forestry-equipment.jpg' => 'Tracked loader and forestry mulching head',
		'mulcher-attachment.jpg' => 'Forestry mulching attachment on the tracked loader',
		'hydraulic-detail.jpg' => 'Hydraulic connections on the mulching attachment',
		'tracked-loader.jpg' => 'Takeuchi tracked loader on site',
		'woodland-worksite.jpg' => 'Tracked mulcher at the edge of a wooded property',
		'forestry-mulching.jpg' => 'Forestry mulching in action',
		'forestry-mulching.mp4' => 'Forestry mulching in action - silent clip',
		'forestry-mulching-mobile.mp4' => 'Forestry mulching in action - mobile silent clip',
		'brush-removal.jpg' => 'Working through dense brush',
		'brush-removal.mp4' => 'Working through dense brush - silent clip',
		'brush-removal-mobile.mp4' => 'Working through dense brush - mobile silent clip',
		'woodland-edge.jpg' => 'Mulching along the woodland edge',
		'woodland-edge.mp4' => 'Mulching along the woodland edge - silent clip',
		'woodland-edge-mobile.mp4' => 'Mulching along the woodland edge - mobile silent clip',
		'clearing-pass.jpg' => 'A clearing pass through the trees',
		'clearing-pass.mp4' => 'A clearing pass through the trees - silent clip',
		'clearing-pass-mobile.mp4' => 'A clearing pass through the trees - mobile silent clip',
		'mulcher-at-work.jpg' => 'The mulcher at work',
		'mulcher-at-work.mp4' => 'The mulcher at work - silent clip',
		'mulcher-at-work-mobile.mp4' => 'The mulcher at work - mobile silent clip',
	);
}


/* -------------------------------------------------------------------------
 * Admin screen
 * ---------------------------------------------------------------------- */

add_action( 'admin_menu', 'spe_register_admin_page' );

function spe_register_admin_page() {
	add_management_page(
		'Shear Performance Setup',
		'Shear Performance Setup',
		'manage_options',
		'spe-site-setup',
		'spe_render_admin_page'
	);
}

function spe_render_admin_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		wp_die( 'You do not have permission to run this.' );
	}

	$report = null;
	if ( isset( $_POST['spe_run'] ) && check_admin_referer( 'spe_run_import' ) ) {
		$report = spe_run_import();
	}

	$divi_active = spe_divi_is_active();

	echo '<div class="wrap"><h1>Shear Performance Site Setup</h1>';

	if ( ! $divi_active ) {
		echo '<div class="notice notice-error"><p><strong>Divi is not the active theme.</strong> '
			. 'Install and activate Divi (and the Shear Performance child theme) before running this.</p></div>';
	}

	if ( $report ) {
		echo '<div class="notice notice-success"><p>Done.</p></div><ul style="list-style:disc;padding-left:20px">';
		foreach ( $report as $line ) {
			echo '<li>' . esc_html( $line ) . '</li>';
		}
		echo '</ul>';
		echo '<h2>Two things left to do by hand</h2><ol style="list-style:decimal;padding-left:20px">'
			. '<li>Go to <strong>Divi → Theme Builder</strong>. On the default website template, '
			. 'click <em>Add Global Header → Add From Library</em> and pick <strong>SPE Global Header</strong>. '
			. 'Do the same for <em>Add Global Footer</em> with <strong>SPE Global Footer</strong>, then Save Changes.</li>'
			. '<li>Check <strong>Divi → Theme Options → General</strong> and make sure the contact form '
			. 'email address is one you monitor.</li></ol>';
	}

	echo '<p>This creates the pages, uploads the photography and wires up the navigation. '
		. 'It is safe to run more than once — existing pages are updated in place rather than duplicated.</p>';

	echo '<form method="post">';
	wp_nonce_field( 'spe_run_import' );
	submit_button( 'Build the site', 'primary', 'spe_run', false,
		$divi_active ? array() : array( 'disabled' => 'disabled' ) );
	echo '</form></div>';
}

/**
 * Divi may be running as the parent of the child theme.
 */
function spe_divi_is_active() {
	$theme = wp_get_theme();

	return 'Divi' === $theme->get( 'Name' ) || 'Divi' === $theme->get( 'Template' );
}


/* -------------------------------------------------------------------------
 * The import itself
 * ---------------------------------------------------------------------- */

function spe_run_import() {
	$report = array();

	$attachments = spe_import_media( $report );
	$pages       = spe_ensure_pages( $report );
	$menus       = spe_ensure_menus( $pages, $report );

	// Page content is written second: the layouts link to sibling pages, so
	// every page has to exist before any of them can be resolved.
	spe_write_page_layouts( $pages, $attachments, $menus, $report );
	spe_write_library_layouts( $attachments, $menus, $report );
	spe_set_front_page( $pages, $report );

	return $report;
}

/**
 * Copy the bundled photography into the media library.
 *
 * @return array filename => attachment ID
 */
function spe_import_media( &$report ) {
	require_once ABSPATH . 'wp-admin/includes/image.php';

	$ids   = array();
	$added = 0;

	foreach ( spe_media() as $filename => $alt ) {
		$existing = spe_find_attachment( $filename );
		if ( $existing ) {
			$ids[ $filename ] = $existing;
			continue;
		}

		$source = SPE_IMPORTER_DIR . 'media/' . $filename;
		if ( ! file_exists( $source ) ) {
			$report[] = "Missing bundled media: {$filename}";
			continue;
		}

		$upload = wp_upload_bits( $filename, null, file_get_contents( $source ) );
		if ( ! empty( $upload['error'] ) ) {
			$report[] = "Could not upload {$filename}: {$upload['error']}";
			continue;
		}

		$type = wp_check_filetype( $filename, null );
		$id   = wp_insert_attachment(
			array(
				'post_mime_type' => $type['type'],
				'post_title'     => $alt,
				'post_content'   => '',
				'post_status'    => 'inherit',
			),
			$upload['file']
		);

		if ( is_wp_error( $id ) || ! $id ) {
			$report[] = "Could not register {$filename} in the media library.";
			continue;
		}

		wp_update_attachment_metadata( $id, wp_generate_attachment_metadata( $id, $upload['file'] ) );
		update_post_meta( $id, '_wp_attachment_image_alt', $alt );
		update_post_meta( $id, '_spe_source', $filename );

		$ids[ $filename ] = $id;
		$added++;
	}

	$report[] = sprintf( 'Media: %d uploaded, %d already present.', $added, count( $ids ) - $added );

	return $ids;
}

/**
 * Find a previously imported image so re-runs do not duplicate uploads.
 */
function spe_find_attachment( $filename ) {
	$found = get_posts(
		array(
			'post_type'      => 'attachment',
			'post_status'    => 'inherit',
			'posts_per_page' => 1,
			'fields'         => 'ids',
			'meta_key'       => '_spe_source',
			'meta_value'     => $filename,
		)
	);

	return $found ? (int) $found[0] : 0;
}

/**
 * Create the five pages (empty for now) and return slug => ID.
 */
function spe_ensure_pages( &$report ) {
	$ids     = array();
	$created = 0;

	foreach ( spe_pages() as $slug => $title ) {
		$existing = get_page_by_path( $slug, OBJECT, 'page' );
		if ( $existing ) {
			$ids[ $slug ] = (int) $existing->ID;
			continue;
		}

		$id = wp_insert_post(
			array(
				'post_type'    => 'page',
				'post_status'  => 'publish',
				'post_title'   => $title,
				'post_name'    => $slug,
				'post_content' => '',
			)
		);

		if ( is_wp_error( $id ) ) {
			$report[] = "Could not create the {$title} page.";
			continue;
		}

		$ids[ $slug ] = (int) $id;
		$created++;
	}

	$report[] = sprintf( 'Pages: %d created, %d already present.', $created, count( $ids ) - $created );

	return $ids;
}

/**
 * Build the header and footer menus and hand them to Divi's menu locations.
 *
 * @return array location key => menu term ID
 */
function spe_ensure_menus( $pages, &$report ) {
	$menus = array();

	foreach ( array( 'primary' => 'Main Menu', 'footer' => 'Footer Menu' ) as $key => $name ) {
		$menu = wp_get_nav_menu_object( $name );

		if ( ! $menu ) {
			$menu_id = wp_create_nav_menu( $name );
			if ( is_wp_error( $menu_id ) ) {
				$report[] = "Could not create the {$name}.";
				continue;
			}
		} else {
			$menu_id = (int) $menu->term_id;
		}

		$menus[ $key ] = (int) $menu_id;

		// Only fill a menu that is empty, so hand edits survive a re-run.
		if ( wp_get_nav_menu_items( $menu_id ) ) {
			continue;
		}

		$position = 1;
		foreach ( spe_pages() as $slug => $title ) {
			if ( empty( $pages[ $slug ] ) ) {
				continue;
			}
			wp_update_nav_menu_item(
				$menu_id,
				0,
				array(
					'menu-item-title'     => $title,
					'menu-item-object'    => 'page',
					'menu-item-object-id' => $pages[ $slug ],
					'menu-item-type'      => 'post_type',
					'menu-item-status'    => 'publish',
					'menu-item-position'  => $position++,
				)
			);
		}
	}

	$locations = get_theme_mod( 'nav_menu_locations', array() );
	if ( isset( $menus['primary'] ) ) {
		$locations['primary-menu'] = $menus['primary'];
	}
	if ( isset( $menus['footer'] ) ) {
		$locations['footer-menu'] = $menus['footer'];
	}
	set_theme_mod( 'nav_menu_locations', $locations );

	$report[] = 'Menus: main and footer navigation ready.';

	return $menus;
}

/**
 * Replace the layout tokens with real URLs, IDs and permalinks.
 */
function spe_resolve_tokens( $content, $pages, $attachments, $menus ) {
	$content = str_replace( '{{HOME}}', home_url( '/' ), $content );
	$content = str_replace( '{{YEAR}}', gmdate( 'Y' ), $content );

	$content = preg_replace_callback(
		'/\{\{URL:([^}]+)\}\}/',
		function ( $m ) use ( $attachments ) {
			$id = isset( $attachments[ $m[1] ] ) ? $attachments[ $m[1] ] : 0;

			return $id ? wp_get_attachment_url( $id ) : '';
		},
		$content
	);

	$content = preg_replace_callback(
		'/\{\{ID:([^}]+)\}\}/',
		function ( $m ) use ( $attachments ) {
			return isset( $attachments[ $m[1] ] ) ? (string) $attachments[ $m[1] ] : '';
		},
		$content
	);

	$content = preg_replace_callback(
		'/\{\{PAGE:([^}]+)\}\}/',
		function ( $m ) use ( $pages ) {
			return isset( $pages[ $m[1] ] ) ? get_permalink( $pages[ $m[1] ] ) : home_url( '/' );
		},
		$content
	);

	$content = preg_replace_callback(
		'/\{\{MENU:([^}]+)\}\}/',
		function ( $m ) use ( $menus ) {
			return isset( $menus[ $m[1] ] ) ? (string) $menus[ $m[1] ] : '';
		},
		$content
	);

	return $content;
}

function spe_read_layout( $name ) {
	$path = SPE_IMPORTER_DIR . 'layouts/' . $name . '.txt';

	return file_exists( $path ) ? file_get_contents( $path ) : '';
}

/**
 * Write the Divi shortcode into each page and flip the builder on.
 */
function spe_write_page_layouts( $pages, $attachments, $menus, &$report ) {
	$written = 0;

	foreach ( spe_pages() as $slug => $title ) {
		if ( empty( $pages[ $slug ] ) ) {
			continue;
		}

		$layout = spe_read_layout( $slug );
		if ( '' === $layout ) {
			$report[] = "Missing layout file for {$title}.";
			continue;
		}

		wp_update_post(
			array(
				'ID'           => $pages[ $slug ],
				'post_content' => spe_resolve_tokens( $layout, $pages, $attachments, $menus ),
			)
		);

		// What tells Divi to render this page with the builder rather than as
		// plain post content.
		update_post_meta( $pages[ $slug ], '_et_pb_use_builder', 'on' );
		update_post_meta( $pages[ $slug ], '_et_pb_built_for_post_type', 'page' );
		update_post_meta( $pages[ $slug ], '_et_pb_page_layout', 'et_no_sidebar' );
		update_post_meta( $pages[ $slug ], '_et_pb_side_nav', 'off' );
		update_post_meta( $pages[ $slug ], '_et_pb_show_title', 'off' );

		$written++;
	}

	$report[] = sprintf( 'Layouts: %d pages built with Divi.', $written );
}

/**
 * Put the global header and footer in the Divi Library.
 *
 * The Theme Builder reads its "Add From Library" list from these, which is how
 * the header and footer get attached to every page.
 */
function spe_write_library_layouts( $attachments, $menus, &$report ) {
	if ( ! post_type_exists( 'et_pb_layout' ) ) {
		$report[] = 'Divi Library not available — skipped the header and footer layouts.';

		return;
	}

	$pages   = array();
	$library = array(
		'header' => 'SPE Global Header',
		'footer' => 'SPE Global Footer',
	);

	foreach ( $library as $name => $title ) {
		$layout = spe_read_layout( $name );
		if ( '' === $layout ) {
			$report[] = "Missing layout file for {$title}.";
			continue;
		}

		$content  = spe_resolve_tokens( $layout, $pages, $attachments, $menus );
		$existing = get_posts(
			array(
				'post_type'      => 'et_pb_layout',
				'post_status'    => 'any',
				'posts_per_page' => 1,
				'fields'         => 'ids',
				'title'          => $title,
			)
		);

		if ( $existing ) {
			$id = (int) $existing[0];
			wp_update_post( array( 'ID' => $id, 'post_content' => $content ) );
		} else {
			$id = wp_insert_post(
				array(
					'post_type'    => 'et_pb_layout',
					'post_status'  => 'publish',
					'post_title'   => $title,
					'post_content' => $content,
				)
			);
		}

		if ( is_wp_error( $id ) || ! $id ) {
			$report[] = "Could not save {$title} to the Divi Library.";
			continue;
		}

		update_post_meta( $id, '_et_pb_built_for_post_type', 'page' );

		// Divi files library items by these taxonomies; without them the
		// layout does not show up in the Theme Builder picker.
		wp_set_object_terms( $id, 'layout', 'layout_type' );
		wp_set_object_terms( $id, 'not_global', 'scope' );
		wp_set_object_terms( $id, 'regular', 'module_width' );
		wp_set_object_terms( $id, 'Shear Performance', 'layout_category' );
	}

	$report[] = 'Divi Library: global header and footer added.';
}

/**
 * Point the site at the new Home page.
 */
function spe_set_front_page( $pages, &$report ) {
	if ( empty( $pages['home'] ) ) {
		return;
	}

	update_option( 'show_on_front', 'page' );
	update_option( 'page_on_front', $pages['home'] );

	$report[] = 'Front page: set to Home.';
}
