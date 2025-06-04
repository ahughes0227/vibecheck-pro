const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function run(cmd) {
  execSync(cmd, { stdio: 'inherit' });
}

function removeDevFiles(dir) {
  for (const item of fs.readdirSync(dir)) {
    const full = path.join(dir, item);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      if (["tests", "__tests__", "scripts", ".vscode"].includes(item)) {
        fs.rmSync(full, { recursive: true, force: true });
        continue;
      }
      removeDevFiles(full);
    } else {
      if (/\.spec\.js$/.test(item) || /\.test\.js$/.test(item) || /\.ts$/.test(item)) {
        fs.rmSync(full, { force: true });
      }
    }
  }
}

function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;
  fs.mkdirSync(dest, { recursive: true });
  for (const item of fs.readdirSync(src)) {
    const srcPath = path.join(src, item);
    const destPath = path.join(dest, item);
    const stat = fs.statSync(srcPath);
    if (stat.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.mkdirSync(path.dirname(destPath), { recursive: true });
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function copy(src, dest) {
  if (!fs.existsSync(src)) return;
  const stat = fs.statSync(src);
  if (stat.isDirectory()) {
    copyDir(src, dest);
  } else {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.copyFileSync(src, dest);
  }
}

function cleanPackageJson(destDir) {
  const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  delete pkg.devDependencies;
  fs.writeFileSync(path.join(destDir, 'package.json'), JSON.stringify(pkg, null, 2));
}

function createRelease() {
  const releaseDir = path.join(process.cwd(), 'release');
  fs.rmSync(releaseDir, { recursive: true, force: true });
  fs.mkdirSync(releaseDir);

  const runtimeItems = ['dist', 'index.html', 'main.js', 'assets', 'vibecheck', 'user_guide.html'];
  runtimeItems.forEach(item => {
    if (fs.existsSync(item)) copy(item, path.join(releaseDir, item));
  });

  if (fs.existsSync('README.md')) copy('README.md', path.join(releaseDir, 'README.md'));
  if (fs.existsSync('LICENSE')) copy('LICENSE', path.join(releaseDir, 'LICENSE'));

  cleanPackageJson(releaseDir);
  removeDevFiles(releaseDir);
}

function zipRelease() {
  run('zip -r release.zip release');
}

function main() {
  run('npm run build');
  createRelease();
  if (process.argv.includes('--zip')) {
    zipRelease();
  }
}

main();
