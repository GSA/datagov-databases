const { src, dest, series } = require('gulp');
const uswds = require("@uswds/compile");

// Custom task to copy images to public/images
function copyImages() {
  return src('./src/assets/images/**/*')
    .pipe(dest('./public/images'));
}

const defaultTask = series(
  uswds.copyAssets,
  uswds.compile,
  copyImages
)

uswds.settings.version = 3;

uswds.paths.dist.css = "./public/styles";
uswds.paths.dist.js = "./public/js";
uswds.paths.dist.img = "./public/images";
uswds.paths.dist.fonts = "./public/fonts";
uswds.paths.dist.components = "./public/components";
uswds.paths.dist.theme = "./src/styles";

exports.compile = uswds.compile;
exports.watch = uswds.watch;
exports.init = uswds.init;
exports.update = uswds.updateUswds;
exports.copyAll = uswds.copyAll;
exports.copyAssets = uswds.copyAssets;
exports.updateUswds = uswds.updateUswds;
exports.copyImages = copyImages; // Export the custom images task
exports.default = defaultTask;
