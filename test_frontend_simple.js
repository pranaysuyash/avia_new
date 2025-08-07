#!/usr/bin/env node
/**
 * Simple Frontend Test
 * Test React component syntax and structure
 */

const fs = require('fs');
const path = require('path');

function testComponentSyntax(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Basic React/TypeScript patterns
    const patterns = {
      'React Import': /import.*React.*from.*['"]react['"]/.test(content),
      'TypeScript Interface': /interface\s+\w+/.test(content),
      'JSX/TSX Elements': /<[A-Z]\w*/.test(content),
      'Export Default': /export\s+default/.test(content),
      'useState Hook': /useState/.test(content),
      'useEffect Hook': /useEffect/.test(content),
    };
    
    return patterns;
  } catch (error) {
    return { error: error.message };
  }
}

function testFrontendComponents() {
  console.log('🔍 Testing Frontend React Components...\n');
  
  // Get current working directory
  const cwd = process.cwd();
  console.log(`Working directory: ${cwd}`);
  
  const componentPaths = [
    path.join(cwd, 'frontend/src/components/i18n/InternationalizationProvider.tsx'),
    path.join(cwd, 'frontend/src/components/i18n/TranslationManager.tsx'), 
    path.join(cwd, 'frontend/src/components/transcription/InteractiveTranscript.tsx'),
    path.join(cwd, 'frontend/src/components/upload/FileUploader.tsx'),
    path.join(cwd, 'frontend/src/components/dashboard/MainDashboard.tsx')
  ];
  
  const results = {};
  let totalComponents = 0;
  let validComponents = 0;
  
  for (const componentPath of componentPaths) {
    const componentName = path.basename(componentPath, '.tsx');
    totalComponents++;
    
    if (fs.existsSync(componentPath)) {
      console.log(`📄 Testing ${componentName}...`);
      
      const patterns = testComponentSyntax(componentPath);
      
      if (patterns.error) {
        console.log(`  ❌ Error: ${patterns.error}`);
        results[componentName] = { exists: true, error: patterns.error };
      } else {
        const validPatterns = Object.entries(patterns).filter(([_, found]) => found).length;
        const totalPatterns = Object.keys(patterns).length;
        
        console.log(`  ✅ React patterns: ${validPatterns}/${totalPatterns}`);
        
        // List found patterns
        for (const [pattern, found] of Object.entries(patterns)) {
          const status = found ? '✅' : '❌';
          console.log(`    ${status} ${pattern}`);
        }
        
        if (validPatterns >= 3) { // Minimum valid patterns
          validComponents++;
          results[componentName] = { exists: true, valid: true, patterns: validPatterns };
        } else {
          results[componentName] = { exists: true, valid: false, patterns: validPatterns };
        }
      }
    } else {
      console.log(`❌ ${componentName}: File not found`);
      results[componentName] = { exists: false };
    }
    
    console.log('');
  }
  
  // Test desktop app structure
  console.log('🖥️  Testing Desktop App Structure...');
  const desktopPaths = [
    path.join(cwd, 'desktop_app/src/renderer/src/components/i18n/InternationalizationDesktop.tsx'),
    path.join(cwd, 'desktop_app/package.json'),
    path.join(cwd, 'desktop_app/src/main.js')
  ];
  
  let desktopValid = 0;
  for (const desktopPath of desktopPaths) {
    if (fs.existsSync(desktopPath)) {
      console.log(`  ✅ ${path.basename(desktopPath)}: Found`);
      desktopValid++;
    } else {
      console.log(`  ❌ ${path.basename(desktopPath)}: Missing`);
    }
  }
  
  // Test mobile app structure  
  console.log('\n📱 Testing Mobile App Structure...');
  const mobilePaths = [
    path.join(cwd, 'mobile/src/components/i18n/InternationalizationMobile.tsx'),
    path.join(cwd, 'mobile/package.json'),
    path.join(cwd, 'mobile/src/App.tsx')
  ];
  
  let mobileValid = 0;
  for (const mobilePath of mobilePaths) {
    if (fs.existsSync(mobilePath)) {
      console.log(`  ✅ ${path.basename(mobilePath)}: Found`);
      mobileValid++;
    } else {
      console.log(`  ❌ ${path.basename(mobilePath)}: Missing`);
    }
  }
  
  // Calculate success rates
  const frontendSuccess = (validComponents / totalComponents) * 100;
  const desktopSuccess = (desktopValid / desktopPaths.length) * 100;
  const mobileSuccess = (mobileValid / mobilePaths.length) * 100;
  const overallSuccess = (frontendSuccess + desktopSuccess + mobileSuccess) / 3;
  
  console.log('\n📊 RESULTS SUMMARY');
  console.log('=' * 50);
  console.log(`⚛️  Frontend Components: ${frontendSuccess.toFixed(1)}% (${validComponents}/${totalComponents})`);
  console.log(`🖥️  Desktop App: ${desktopSuccess.toFixed(1)}% (${desktopValid}/${desktopPaths.length})`);
  console.log(`📱 Mobile App: ${mobileSuccess.toFixed(1)}% (${mobileValid}/${mobilePaths.length})`);
  console.log(`\n🎯 Overall Cross-Platform Success: ${overallSuccess.toFixed(1)}%`);
  
  if (overallSuccess >= 80) {
    console.log('🎉 Excellent! All platforms are well structured!');
  } else if (overallSuccess >= 60) {
    console.log('✅ Good! Most platforms are working well');
  } else {
    console.log('⚠️  Some platforms need improvement');
  }
  
  // Save report
  const report = {
    timestamp: new Date().toISOString(),
    frontend_components: results,
    frontend_success: frontendSuccess,
    desktop_success: desktopSuccess,
    mobile_success: mobileSuccess,
    overall_success: overallSuccess
  };
  
  fs.writeFileSync('frontend_test_report.json', JSON.stringify(report, null, 2));
  console.log('\n📄 Report saved: frontend_test_report.json');
  
  return overallSuccess >= 70;
}

// Run tests
const success = testFrontendComponents();
process.exit(success ? 0 : 1);