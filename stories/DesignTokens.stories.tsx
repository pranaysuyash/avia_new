/**
 * Design Tokens Documentation
 * Visual documentation of the design system tokens
 */

import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import designTokens from '../design-tokens.json';
import { webTheme } from '../shared/theme';

export default {
  title: 'Design System/Tokens',
  parameters: {
    docs: {
      description: {
        component: 'Visual documentation of design tokens used across all platforms',
      },
    },
  },
} as Meta;

// Color Palette Story
export const ColorPalette: StoryObj = {
  render: () => (
    <div>
      <h2 className="text-2xl font-bold mb-6">Color Palette</h2>
      
      {/* Brand Colors */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Brand Colors</h3>
        <div className="grid grid-cols-5 gap-4">
          {Object.entries(designTokens.colors).map(([colorName, colorValue]) => {
            if (typeof colorValue === 'object' && 'DEFAULT' in colorValue) {
              return Object.entries(colorValue).map(([shade, hex]) => (
                <div key={`${colorName}-${shade}`} className="text-center">
                  <div
                    className="w-full h-20 rounded-lg shadow-md mb-2"
                    style={{ backgroundColor: hex as string }}
                  />
                  <p className="text-sm font-medium">{colorName}</p>
                  <p className="text-xs text-gray-500">{shade}</p>
                  <p className="text-xs font-mono text-gray-400">{hex}</p>
                </div>
              ));
            }
            return null;
          })}
        </div>
      </div>

      {/* Semantic Colors */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Semantic Colors</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <h4 className="font-medium mb-2">Text Colors</h4>
            {Object.entries(designTokens.colors.text).map(([name, color]) => (
              <div key={name} className="flex items-center mb-2">
                <div
                  className="w-8 h-8 rounded mr-3"
                  style={{ backgroundColor: color }}
                />
                <span className="text-sm">{name}: {color}</span>
              </div>
            ))}
          </div>
          <div>
            <h4 className="font-medium mb-2">Background Colors</h4>
            {Object.entries(designTokens.colors.background).map(([name, color]) => (
              <div key={name} className="flex items-center mb-2">
                <div
                  className="w-8 h-8 rounded border mr-3"
                  style={{ backgroundColor: color }}
                />
                <span className="text-sm">{name}: {color}</span>
              </div>
            ))}
          </div>
          <div>
            <h4 className="font-medium mb-2">Border Colors</h4>
            {Object.entries(designTokens.colors.border).map(([name, color]) => (
              <div key={name} className="flex items-center mb-2">
                <div
                  className="w-8 h-8 rounded border-2 mr-3"
                  style={{ borderColor: color }}
                />
                <span className="text-sm">{name}: {color}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  ),
};

// Typography Story
export const Typography: StoryObj = {
  render: () => (
    <div>
      <h2 className="text-2xl font-bold mb-6">Typography</h2>
      
      {/* Font Sizes */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Font Sizes</h3>
        {Object.entries(designTokens.typography.fontSize).map(([size, value]) => (
          <div key={size} className="mb-3">
            <p
              className="leading-none"
              style={{ fontSize: value }}
            >
              {size}: The quick brown fox jumps over the lazy dog
            </p>
            <p className="text-xs text-gray-500 mt-1">{value}</p>
          </div>
        ))}
      </div>

      {/* Font Weights */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Font Weights</h3>
        {Object.entries(designTokens.typography.fontWeight).map(([weight, value]) => (
          <div key={weight} className="mb-3">
            <p
              className="text-lg"
              style={{ fontWeight: value }}
            >
              {weight}: The quick brown fox jumps over the lazy dog
            </p>
            <p className="text-xs text-gray-500">Weight: {value}</p>
          </div>
        ))}
      </div>
    </div>
  ),
};

// Spacing Story
export const Spacing: StoryObj = {
  render: () => (
    <div>
      <h2 className="text-2xl font-bold mb-6">Spacing</h2>
      
      <div className="space-y-2">
        {Object.entries(designTokens.spacing).map(([size, value]) => (
          <div key={size} className="flex items-center">
            <span className="w-16 text-sm font-mono">{size}</span>
            <span className="w-20 text-sm text-gray-500">{value}</span>
            <div
              className="bg-blue-500 h-4"
              style={{ width: value }}
            />
          </div>
        ))}
      </div>
    </div>
  ),
};

// Border Radius Story
export const BorderRadius: StoryObj = {
  render: () => (
    <div>
      <h2 className="text-2xl font-bold mb-6">Border Radius</h2>
      
      <div className="grid grid-cols-3 gap-6">
        {Object.entries(designTokens.borderRadius).map(([size, value]) => (
          <div key={size} className="text-center">
            <div
              className="w-24 h-24 bg-blue-500 mx-auto mb-2"
              style={{ borderRadius: value }}
            />
            <p className="font-medium">{size}</p>
            <p className="text-sm text-gray-500">{value}</p>
          </div>
        ))}
      </div>
    </div>
  ),
};

// Shadows Story
export const Shadows: StoryObj = {
  render: () => (
    <div>
      <h2 className="text-2xl font-bold mb-6">Shadows</h2>
      
      <div className="grid grid-cols-2 gap-8">
        {Object.entries(designTokens.boxShadow).map(([size, value]) => {
          if (size === 'none') return null;
          return (
            <div key={size} className="text-center">
              <div
                className="w-32 h-32 bg-white rounded-lg mx-auto mb-3"
                style={{ boxShadow: value }}
              />
              <p className="font-medium">{size}</p>
              <p className="text-xs text-gray-500 font-mono">{value}</p>
            </div>
          );
        })}
      </div>
    </div>
  ),
};

// Component Examples Story
export const ComponentExamples: StoryObj = {
  render: () => (
    <div>
      <h2 className="text-2xl font-bold mb-6">Component Examples</h2>
      
      {/* Buttons */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Buttons</h3>
        <div className="space-x-4">
          <button
            className="px-4 py-2 rounded-md text-white font-medium transition-colors"
            style={{
              backgroundColor: designTokens.colors.primary.DEFAULT,
              boxShadow: designTokens.boxShadow.sm,
            }}
          >
            Primary Button
          </button>
          <button
            className="px-4 py-2 rounded-md font-medium border transition-colors"
            style={{
              color: designTokens.colors.text.primary,
              borderColor: designTokens.colors.border.DEFAULT,
              backgroundColor: designTokens.colors.background.primary,
            }}
          >
            Secondary Button
          </button>
          <button
            className="px-4 py-2 rounded-md font-medium transition-colors"
            style={{
              color: designTokens.colors.primary.DEFAULT,
            }}
          >
            Ghost Button
          </button>
        </div>
      </div>

      {/* Cards */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Cards</h3>
        <div className="grid grid-cols-3 gap-4">
          <div
            className="p-6 rounded-lg"
            style={{
              backgroundColor: designTokens.colors.background.primary,
              boxShadow: designTokens.boxShadow.sm,
            }}
          >
            <h4 className="font-semibold mb-2">Small Shadow</h4>
            <p className="text-sm text-gray-600">Card with small shadow elevation</p>
          </div>
          <div
            className="p-6 rounded-lg"
            style={{
              backgroundColor: designTokens.colors.background.primary,
              boxShadow: designTokens.boxShadow.DEFAULT,
            }}
          >
            <h4 className="font-semibold mb-2">Default Shadow</h4>
            <p className="text-sm text-gray-600">Card with default shadow elevation</p>
          </div>
          <div
            className="p-6 rounded-lg"
            style={{
              backgroundColor: designTokens.colors.background.primary,
              boxShadow: designTokens.boxShadow.lg,
            }}
          >
            <h4 className="font-semibold mb-2">Large Shadow</h4>
            <p className="text-sm text-gray-600">Card with large shadow elevation</p>
          </div>
        </div>
      </div>

      {/* Transcript Colors */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Transcript Colors</h3>
        <div className="space-y-2">
          <div className="p-4 rounded-md" style={{ backgroundColor: designTokens.colors.transcript.highlight }}>
            Search Highlight
          </div>
          <div className="p-4 rounded-md" style={{ backgroundColor: designTokens.colors.transcript.selected }}>
            Selected Segment
          </div>
          <div className="p-4 rounded-md" style={{ backgroundColor: designTokens.colors.transcript.current }}>
            Current Playing Segment
          </div>
          <div className="p-4 rounded-md" style={{ backgroundColor: designTokens.colors.transcript.edited }}>
            Edited Segment
          </div>
        </div>
      </div>
    </div>
  ),
};