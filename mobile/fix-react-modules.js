#!/usr/bin/env node

/**
 * Fix React Module Resolution Issues
 * This script helps diagnose and fix common React Native module resolution problems
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🔧 React Native Module Fix Script');
console.log('================================\n');

// Check if we're in the right directory
if (!fs.existsSync('package.json')) {
  console.error('❌ Error: package.json not found. Please run this script from the mobile directory.');
  process.exit(1);
}

// Read package.json
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));

console.log('📦 Project:', packageJson.name);
console.log('📦 Version:', packageJson.version);

// Check if React is installed
function checkDependency(depName, type = 'dependencies') {
  const deps = packageJson[type] || {};
  if (deps[depName]) {
    console.log(`✅ ${depName}: ${deps[depName]} (${type})`);
    return true;
  }
  return false;
}

console.log('\n🔍 Checking Dependencies:');
console.log('------------------------');

const requiredDeps = [
  'react',
  'react-native',
  'react-native-video',
  'react-native-document-picker',
  'react-native-fs',
  '@react-native-community/slider',
  'react-native-vector-icons'
];

const requiredDevDeps = [
  '@types/react',
  '@types/react-native',
  'typescript'
];

let missingDeps = [];
let missingDevDeps = [];

requiredDeps.forEach(dep => {
  if (!checkDependency(dep)) {
    missingDeps.push(dep);
    console.log(`❌ Missing: ${dep}`);
  }
});

requiredDevDeps.forEach(dep => {
  if (!checkDependency(dep, 'devDependencies')) {
    missingDevDeps.push(dep);
    console.log(`❌ Missing dev dependency: ${dep}`);
  }
});

// Check node_modules
console.log('\n📁 Checking node_modules:');
console.log('-------------------------');

if (!fs.existsSync('node_modules')) {
  console.log('❌ node_modules directory not found');
  console.log('💡 Run: npm install');
} else {
  console.log('✅ node_modules directory exists');
  
  // Check if React is actually installed
  const reactPath = path.join('node_modules', 'react');
  if (fs.existsSync(reactPath)) {
    console.log('✅ React module found in node_modules');
    
    // Check React version
    try {
      const reactPackageJson = JSON.parse(fs.readFileSync(path.join(reactPath, 'package.json'), 'utf8'));
      console.log(`✅ React version: ${reactPackageJson.version}`);
    } catch (e) {
      console.log('⚠️  Could not read React version');
    }
  } else {
    console.log('❌ React module not found in node_modules');
  }
}

// Check TypeScript configuration
console.log('\n⚙️  Checking TypeScript Configuration:');
console.log('-------------------------------------');

if (fs.existsSync('tsconfig.json')) {
  console.log('✅ tsconfig.json exists');
  
  try {
    const tsConfig = JSON.parse(fs.readFileSync('tsconfig.json', 'utf8'));
    
    if (tsConfig.compilerOptions) {
      console.log('✅ compilerOptions found');
      
      if (tsConfig.compilerOptions.typeRoots) {
        console.log('✅ typeRoots configured');
      } else {
        console.log('⚠️  typeRoots not configured');
      }
      
      if (tsConfig.compilerOptions.jsx) {
        console.log(`✅ JSX mode: ${tsConfig.compilerOptions.jsx}`);
      } else {
        console.log('⚠️  JSX mode not configured');
      }
    }
  } catch (e) {
    console.log('❌ Error reading tsconfig.json:', e.message);
  }
} else {
  console.log('❌ tsconfig.json not found');
}

// Check type declarations
console.log('\n📝 Checking Type Declarations:');
console.log('------------------------------');

const typeFiles = [
  'src/types/index.d.ts',
  'src/types/react-native-video.d.ts'
];

typeFiles.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`✅ ${file} exists`);
  } else {
    console.log(`❌ ${file} not found`);
  }
});

// Provide fix suggestions
console.log('\n🔧 Fix Suggestions:');
console.log('-------------------');

if (missingDeps.length > 0) {
  console.log('1. Install missing dependencies:');
  console.log(`   npm install ${missingDeps.join(' ')}`);
}

if (missingDevDeps.length > 0) {
  console.log('2. Install missing dev dependencies:');
  console.log(`   npm install --save-dev ${missingDevDeps.join(' ')}`);
}

if (!fs.existsSync('node_modules') || !fs.existsSync('node_modules/react')) {
  console.log('3. Reinstall all dependencies:');
  console.log('   rm -rf node_modules package-lock.json');
  console.log('   npm install');
}

console.log('4. Clear Metro cache:');
console.log('   npx react-native start --reset-cache');

console.log('5. If issues persist, try:');
console.log('   npm cache clean --force');
console.log('   rm -rf node_modules package-lock.json');
console.log('   npm install');

// Auto-fix option
console.log('\n🚀 Auto-fix Options:');
console.log('--------------------');

if (process.argv.includes('--fix')) {
  console.log('Running auto-fix...');
  
  try {
    if (missingDeps.length > 0) {
      console.log('Installing missing dependencies...');
      execSync(`npm install ${missingDeps.join(' ')}`, { stdio: 'inherit' });
    }
    
    if (missingDevDeps.length > 0) {
      console.log('Installing missing dev dependencies...');
      execSync(`npm install --save-dev ${missingDevDeps.join(' ')}`, { stdio: 'inherit' });
    }
    
    console.log('✅ Auto-fix completed!');
  } catch (error) {
    console.log('❌ Auto-fix failed:', error.message);
  }
} else {
  console.log('To run auto-fix: node fix-react-modules.js --fix');
}

console.log('\n✨ Done! Check the output above for any issues to resolve.');