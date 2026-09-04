<?php
/**
 * Shear Performance EarthWorks — Divi child theme.
 *
 * @package shear-performance
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Version stamp for the child stylesheet.
 *
 * Uses the file's modification time so a re-upload busts the browser cache
 * without anyone having to remember to bump a number.
 */
function spe_asset_version( $relative_path = 'style.css' ) {
	$file = get_stylesheet_directory() . '/' . ltrim( $relative_path, '/' );

	return file_exists( $file ) ? (string) filemtime( $file ) : '1.0.0';
}

/**
 * Load Divi's stylesheet, then the child stylesheet on top of it.
 */
function spe_enqueue_styles() {
	// Divi registers its own stylesheet as "divi-style". Depending on it keeps
	// the child CSS after Divi's in the cascade even when Divi defers loading.
	$parent_handle = wp_style_is( 'divi-style', 'registered' ) ? 'divi-style' : 'parent-style';

	if ( 'parent-style' === $parent_handle ) {
		wp_enqueue_style( 'parent-style', get_template_directory_uri() . '/style.css' );
	}

	wp_enqueue_style(
		'spe-fonts',
		'https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500&display=swap',
		array(),
		null
	);

	wp_enqueue_style(
		'spe-style',
		get_stylesheet_directory_uri() . '/style.css',
		array( $parent_handle, 'spe-fonts' ),
		spe_asset_version()
	);
}
add_action( 'wp_enqueue_scripts', 'spe_enqueue_styles', 20 );

/**
 * Warm up the font connections before the stylesheet is parsed.
 */
function spe_resource_hints( $hints, $relation ) {
	if ( 'preconnect' === $relation ) {
		$hints[] = 'https://fonts.googleapis.com';
		$hints[] = array(
			'href'        => 'https://fonts.gstatic.com',
			'crossorigin' => 'anonymous',
		);
	}

	return $hints;
}
add_filter( 'wp_resource_hints', 'spe_resource_hints', 10, 2 );

/**
 * The site is a single dark theme, so tell the browser to render form
 * controls, scrollbars and autofill accordingly.
 */
function spe_color_scheme_meta() {
	echo '<meta name="color-scheme" content="dark">' . "\n";
	echo '<meta name="theme-color" content="#0d1009">' . "\n";
}
add_action( 'wp_head', 'spe_color_scheme_meta', 1 );

/**
 * Load the child stylesheet inside the Visual Builder too, so editing a page
 * shows the same design the front end does.
 */
function spe_enqueue_builder_styles() {
	wp_enqueue_style(
		'spe-style-vb',
		get_stylesheet_directory_uri() . '/style.css',
		array(),
		spe_asset_version()
	);
}
add_action( 'et_fb_enqueue_assets', 'spe_enqueue_builder_styles', 20 );

/**
 * Divi's Theme Builder header is the site header, so the theme's own
 * navigation and page title do not need to render as well.
 */
function spe_body_classes( $classes ) {
	$classes[] = 'spe-site';

	return $classes;
}
add_filter( 'body_class', 'spe_body_classes' );
