const fs = require('fs');
const acorn = require('acorn');
try {
  acorn.parse(fs.readFileSync('rubicon_addons/pdp_frontend/static/src/js/pdp_workspace.js', 'utf8'), {ecmaVersion: 2022, sourceType: 'module'});
  console.log('JS is syntactically valid according to Acorn.');
} catch (e) {
  console.error(e);
}
