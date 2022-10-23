var gulp = require('gulp')
var sass = require('gulp-sass')(require('sass'))
var postcss = require('gulp-postcss')
var path = require('path');
var exec = require('child_process').exec

const SRC_DIR = './src/'
const BUILD_DIR = './build/'

// Globs for compiled stylesheets.
const STYLESHEETS = [
    path.join(SRC_DIR, '**/*.scss')
]

// Globs for stylesheets prerequisites.
const STYLESHEETS_PREREQS = [
    path.join(SRC_DIR, '**/*.{html, html-src}')
]
STYLESHEETS_PREREQS.push(...STYLESHEETS)

// Globs for non-compiled (ie. directly installed) files.
const STATIC_FILES = [
    path.join(SRC_DIR, '**/*'),
    path.join(SRC_DIR, '**/.env'),
    path.join('!' + SRC_DIR, '**/*.pyc')
]
STATIC_FILES.push(
    ...STYLESHEETS.map(x => '!' + x),
)

/**
 * Incrementally copy static files from SRC_DIR to BUILD_DIR.
 */
function do_install_files() {
    return gulp.src(STATIC_FILES, { since: gulp.lastRun(do_install_files) })
        .pipe(gulp.dest(BUILD_DIR))
}
exports.files = do_install_files

/**
 * Compile SASS stylesheets.
 */
function do_compile_stylesheets() {
    return gulp.src(STYLESHEETS)
        .pipe(sass.sync({includePaths: [SRC_DIR]}).on('error', sass.logError))
        .pipe(gulp.dest(BUILD_DIR))
        .pipe(postcss())
        .pipe(gulp.dest(BUILD_DIR))
}
exports.stylesheets = do_compile_stylesheets

/**
 * Watch files for changes and recompile when needed.
 */
function do_watch() {
    gulp.watch(STYLESHEETS_PREREQS, do_compile_stylesheets);
    gulp.watch(STATIC_FILES, do_install_files)
}
exports.watch = do_watch

/**
 * Clean all build artifacts.
 */
function do_clean(cb) {
    exec(
        `rm -rf ${BUILD_DIR}`,
        (err, stdout, stderr) => {
            if (stdout) { console.log(stdout); }
            if (stderr) { console.log(stderr); }
            cb(err)
        }
    )
}
exports.clean = do_clean

/*
 * Run all build steps.
 */
exports.all = gulp.series(
    exports.clean,
    exports.files,
    exports.stylesheets
)
