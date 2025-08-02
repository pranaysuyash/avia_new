# React Module Resolution Fix

## Problem
The error "Cannot find module 'react' or its corresponding type declarations" occurs when:

1. Dependencies are not properly installed
2. TypeScript configuration is incorrect
3. Node modules are corrupted or missing
4. Type declarations are not properly configured

## Solution Steps

### 1. Fix TypeScript Configuration

The `tsconfig.json` has been updated to remove the problematic extends and use a proper React Native configuration:

```json
{
  "compilerOptions": {
    "target": "esnext",
    "lib": ["es2017", "es2018", "es2019", "es2020"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "declaration": false,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@api/*": ["src/api/*"],
      "@utils/*": ["src/utils/*"]
    },
    "typeRoots": ["node_modules/@types", "src/types"]
  }
}
```

### 2. Install Required Dependencies

Run the following commands in the mobile directory:

```bash
# Navigate to mobile directory
cd mobile

# Install all dependencies
npm install

# If that doesn't work, clean install:
rm -rf node_modules package-lock.json
npm install
```

### 3. Verify Dependencies

The following dependencies should be installed:

**Core Dependencies:**
- react@18.2.0
- react-native@0.72.6
- react-native-video@^6.0.0
- react-native-document-picker@^9.0.0
- react-native-fs@^2.20.0
- @react-native-community/slider@^4.4.0
- react-native-vector-icons@^10.0.0

**Type Dependencies:**
- @types/react@^18.0.24
- @types/react-native@^0.72.0
- typescript@4.8.4

### 4. Use the Fix Script

Run the diagnostic script to identify and fix issues:

```bash
# Check for issues
node fix-react-modules.js

# Auto-fix issues
node fix-react-modules.js --fix
```

### 5. Clear Caches

If issues persist, clear all caches:

```bash
# Clear npm cache
npm cache clean --force

# Clear Metro cache
npx react-native start --reset-cache

# Clear React Native cache
npx react-native start --reset-cache
```

### 6. Platform-Specific Setup

#### iOS
```bash
cd ios
pod install
cd ..
```

#### Android
Make sure Android SDK is properly configured.

## File Structure

Ensure your project has this structure:

```
mobile/
├── src/
│   ├── App.tsx                    # Main app component
│   ├── components/
│   │   └── video/
│   │       └── VideoProcessor.tsx # Video processing component
│   └── types/
│       ├── index.d.ts            # Type declarations
│       └── react-native-video.d.ts
├── index.js                      # App entry point
├── package.json                  # Dependencies
├── tsconfig.json                 # TypeScript config
└── node_modules/                 # Installed packages
```

## Testing the Fix

1. **Check TypeScript compilation:**
```bash
npx tsc --noEmit
```

2. **Start Metro bundler:**
```bash
npm start
```

3. **Run the app:**
```bash
# iOS
npm run ios

# Android
npm run android
```

## Common Issues and Solutions

### Issue: "Module not found" errors
**Solution:** Ensure all dependencies are installed and node_modules exists.

### Issue: TypeScript errors
**Solution:** Check tsconfig.json configuration and type declarations.

### Issue: Metro bundler issues
**Solution:** Clear Metro cache with `--reset-cache` flag.

### Issue: Platform-specific build errors
**Solution:** Follow platform-specific setup in SETUP_INSTRUCTIONS.md.

## Verification

After applying these fixes, you should be able to:

1. Import React without errors
2. Use all React Native components
3. Use the VideoProcessor component
4. Build and run the app successfully

## Additional Resources

- [React Native Troubleshooting](https://reactnative.dev/docs/troubleshooting)
- [TypeScript with React Native](https://reactnative.dev/docs/typescript)
- [Metro Configuration](https://facebook.github.io/metro/docs/configuration)

If you continue to experience issues after following these steps, please check the SETUP_INSTRUCTIONS.md file for more detailed setup information.