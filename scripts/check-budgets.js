/**
 * Performance Budget Checker
 * Validates build outputs against defined budgets
 */

const fs = require('fs');
const path = require('path');
const chalk = require('chalk');

// Import budget configuration
const lighthouseBudgets = require('../lighthouse-budgets.json');

// Asset type mappings
const ASSET_EXTENSIONS = {
  script: ['.js', '.mjs'],
  stylesheet: ['.css'],
  image: ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'],
  font: ['.woff', '.woff2', '.ttf', '.otf', '.eot'],
};

/**
 * Get file size in KB
 */
function getFileSizeInKB(filePath) {
  const stats = fs.statSync(filePath);
  return stats.size / 1024;
}

/**
 * Get asset type from file extension
 */
function getAssetType(filename) {
  const ext = path.extname(filename).toLowerCase();
  
  for (const [type, extensions] of Object.entries(ASSET_EXTENSIONS)) {
    if (extensions.includes(ext)) {
      return type;
    }
  }
  
  return 'other';
}

/**
 * Analyze build directory
 */
function analyzeBuildDirectory(buildPath) {
  const assets = {
    script: [],
    stylesheet: [],
    image: [],
    font: [],
    other: [],
  };
  
  function walkDir(dir) {
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        walkDir(filePath);
      } else {
        const type = getAssetType(file);
        const sizeKB = getFileSizeInKB(filePath);
        
        assets[type].push({
          path: filePath.replace(buildPath, ''),
          size: sizeKB,
          type,
        });
      }
    }
  }
  
  walkDir(buildPath);
  return assets;
}

/**
 * Check assets against budgets
 */
function checkBudgets(assets, budgets) {
  const violations = [];
  const warnings = [];
  
  // Check resource size budgets
  for (const budget of budgets.resourceSizes) {
    const assetType = assets[budget.resourceType];
    
    if (assetType) {
      const totalSize = assetType.reduce((sum, asset) => sum + asset.size, 0);
      
      if (totalSize > budget.budget) {
        violations.push({
          type: 'size',
          resourceType: budget.resourceType,
          actual: totalSize,
          budget: budget.budget,
          assets: assetType.sort((a, b) => b.size - a.size).slice(0, 5),
        });
      } else if (totalSize > budget.budget * 0.9) {
        warnings.push({
          type: 'size',
          resourceType: budget.resourceType,
          actual: totalSize,
          budget: budget.budget,
          percentage: (totalSize / budget.budget) * 100,
        });
      }
    }
  }
  
  // Check resource count budgets
  for (const budget of budgets.resourceCounts) {
    const assetType = assets[budget.resourceType];
    
    if (assetType) {
      const count = assetType.length;
      
      if (count > budget.budget) {
        violations.push({
          type: 'count',
          resourceType: budget.resourceType,
          actual: count,
          budget: budget.budget,
        });
      }
    }
  }
  
  // Check total size
  const totalSizeBudget = budgets.resourceSizes.find(b => b.resourceType === 'total');
  if (totalSizeBudget) {
    const totalSize = Object.values(assets)
      .flat()
      .reduce((sum, asset) => sum + asset.size, 0);
    
    if (totalSize > totalSizeBudget.budget) {
      violations.push({
        type: 'total',
        actual: totalSize,
        budget: totalSizeBudget.budget,
      });
    }
  }
  
  return { violations, warnings };
}

/**
 * Print budget report
 */
function printReport(assets, violations, warnings) {
  console.log('\n' + chalk.bold('📊 Performance Budget Report'));
  console.log('=' + '='.repeat(50));
  
  // Asset summary
  console.log('\n' + chalk.bold('Asset Summary:'));
  for (const [type, typeAssets] of Object.entries(assets)) {
    if (typeAssets.length > 0) {
      const totalSize = typeAssets.reduce((sum, asset) => sum + asset.size, 0);
      console.log(
        `  ${chalk.cyan(type.padEnd(12))} - ` +
        `${typeAssets.length} files, ` +
        `${totalSize.toFixed(1)} KB total`
      );
    }
  }
  
  // Warnings
  if (warnings.length > 0) {
    console.log('\n' + chalk.yellow.bold('⚠️  Warnings:'));
    for (const warning of warnings) {
      console.log(
        chalk.yellow(`  ${warning.resourceType} is at ${warning.percentage.toFixed(0)}% of budget`)
      );
    }
  }
  
  // Violations
  if (violations.length > 0) {
    console.log('\n' + chalk.red.bold('❌ Budget Violations:'));
    for (const violation of violations) {
      if (violation.type === 'size') {
        console.log(
          chalk.red(
            `  ${violation.resourceType}: ${violation.actual.toFixed(1)} KB ` +
            `(budget: ${violation.budget} KB, +${(violation.actual - violation.budget).toFixed(1)} KB)`
          )
        );
        
        // Show largest files
        if (violation.assets) {
          console.log(chalk.red('    Largest files:'));
          for (const asset of violation.assets) {
            console.log(chalk.red(`      ${asset.path} (${asset.size.toFixed(1)} KB)`));
          }
        }
      } else if (violation.type === 'count') {
        console.log(
          chalk.red(
            `  ${violation.resourceType} count: ${violation.actual} ` +
            `(budget: ${violation.budget})`
          )
        );
      } else if (violation.type === 'total') {
        console.log(
          chalk.red(
            `  Total size: ${violation.actual.toFixed(1)} KB ` +
            `(budget: ${violation.budget} KB)`
          )
        );
      }
    }
  } else {
    console.log('\n' + chalk.green.bold('✅ All budgets passed!'));
  }
  
  console.log('\n' + '='.repeat(51) + '\n');
  
  return violations.length === 0;
}

/**
 * Main execution
 */
function main() {
  const buildPaths = [
    path.resolve(__dirname, '../frontend/build'),
    path.resolve(__dirname, '../desktop_app/dist'),
  ];
  
  let allPassed = true;
  
  for (const buildPath of buildPaths) {
    if (fs.existsSync(buildPath)) {
      console.log(chalk.bold(`\nAnalyzing ${path.basename(path.dirname(buildPath))}...`));
      
      const assets = analyzeBuildDirectory(buildPath);
      const { violations, warnings } = checkBudgets(assets, lighthouseBudgets);
      const passed = printReport(assets, violations, warnings);
      
      allPassed = allPassed && passed;
    } else {
      console.log(chalk.yellow(`\nBuild directory not found: ${buildPath}`));
      console.log(chalk.gray('Run build first to check budgets.'));
    }
  }
  
  // Exit with appropriate code
  process.exit(allPassed ? 0 : 1);
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { analyzeBuildDirectory, checkBudgets };