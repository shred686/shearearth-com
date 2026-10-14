<?php
/**
 * Initial setup through WP-CLI after deploying the child theme and importer.
 * Run as an administrator: wp eval-file /path/to/bootstrap-wordpress.php --user=ID
 * Re-running replaces the five page layouts with the repository's content.
 */
if ( ! defined( 'WP_CLI' ) || ! WP_CLI ) {
	exit;
}

if ( ! current_user_can( 'manage_options' ) || ! function_exists( 'spe_run_import' ) || ! spe_divi_is_active() ) {
	WP_CLI::error( 'Run as a WordPress administrator with the child theme and setup plugin active.' );
}

foreach ( spe_run_import() as $line ) {
	WP_CLI::log( $line );
	if ( preg_match( '/Missing|Could not|not available/', $line ) ) {
		WP_CLI::error( 'Import incomplete; resolve the reported problem before retrying.' );
	}
}

update_option( 'blogname', 'Shear Performance EarthWorks' );
update_option( 'blogdescription', 'Forestry mulching and land management in St. Louis.' );

// Use the installed Divi 4 Theme Builder API instead of editing its database
// format by hand. Library layouts are copied into the dedicated layout types.
if ( ! function_exists( 'et_theme_builder_store_template' ) || ! function_exists( 'et_theme_builder_insert_layout' ) ) {
	WP_CLI::error( 'The installed Divi version does not expose the expected Theme Builder API.' );
}

$builder_id = et_theme_builder_get_theme_builder_post_id( true, true );
$template   = array();
foreach ( et_theme_builder_get_theme_builder_templates( true ) as $candidate ) {
	if ( ! empty( $candidate['default'] ) ) {
		$template = $candidate;
		break;
	}
}

$layouts = array();
foreach ( array( 'header' => 'SPE Global Header', 'footer' => 'SPE Global Footer' ) as $kind => $title ) {
	$library = get_posts( array( 'post_type' => 'et_pb_layout', 'post_status' => 'publish', 'title' => $title, 'numberposts' => 1 ) );
	if ( ! $library ) {
		WP_CLI::error( 'Missing library layout: ' . $title );
	}
	$type = et_theme_builder_get_valid_layout_post_type( $kind );
	$id   = isset( $template['layouts'][ $kind ]['id'] ) ? (int) $template['layouts'][ $kind ]['id'] : 0;
	$data = array( 'post_type' => $type, 'post_title' => $title, 'post_content' => wp_slash( $library[0]->post_content ), 'post_status' => 'publish' );
	if ( $id && get_post_type( $id ) === $type ) {
		$data['ID'] = $id;
		$id = wp_update_post( $data, true );
	} else {
		$id = et_theme_builder_insert_layout( $data );
	}
	if ( is_wp_error( $id ) || ! $id ) {
		WP_CLI::error( 'Could not attach ' . $title );
	}
	$layouts[ $kind ] = array( 'id' => $id, 'enabled' => true );
}

$template['title']     = 'Default Website Template';
$template['default']   = '1';
$template['enabled']   = '1';
$template['layouts']   = array_merge( isset( $template['layouts'] ) ? $template['layouts'] : array(), $layouts );
$template_id           = et_theme_builder_store_template( $builder_id, $template, true );
if ( ! $template_id ) {
	WP_CLI::error( 'Could not save the default website template.' );
}
if ( ! in_array( (string) $template_id, array_map( 'strval', get_post_meta( $builder_id, '_et_template', false ) ), true ) ) {
	add_post_meta( $builder_id, '_et_template', $template_id );
}
foreach ( array( 'header', 'footer' ) as $kind ) {
	update_post_meta( $template_id, '_et_' . $kind . '_layout_global', '1' );
}
et_theme_builder_clear_wp_cache( 'all' );
ET_Core_PageResource::remove_static_resources( 'all', 'all', false, 'dynamic' );
WP_CLI::success( 'Pages, media, menus, front page, and global header/footer are installed.' );
