#!/usr/bin/env node

/**
 * Context7 Integration for Daanaa
 *
 * Indexes the Daanaa codebase for AI-efficient documentation lookup
 * Reduces token overhead by keeping documentation fresh and discoverable
 *
 * Usage: node scripts/context7-index.js
 */

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

const CONTEXT7_CONFIG = {
  projectName: 'daanaa',
  projectPath: '/home/akbar/meritgiving',
  documentationPaths: [
    'docs/',
    'CLAUDE.md',
    'STEWARDSHIP.md',
    'DECISIONS.md',
    'LESSONS.md',
    'institution/',
  ],
  indexedAt: new Date().toISOString(),
};

async function indexCodebase() {
  console.log('🔍 Context7: Indexing Daanaa codebase...');
  console.log(`📍 Project: ${CONTEXT7_CONFIG.projectName}`);
  console.log(`📂 Path: ${CONTEXT7_CONFIG.projectPath}`);
  console.log('');

  // Create a context manifest for quick lookup
  const manifest = {
    project: CONTEXT7_CONFIG.projectName,
    indexed: CONTEXT7_CONFIG.indexedAt,
    sections: [],
  };

  // Index each documentation section
  for (const docPath of CONTEXT7_CONFIG.documentationPaths) {
    const fullPath = path.join(CONTEXT7_CONFIG.projectPath, docPath);

    if (fs.existsSync(fullPath)) {
      const stats = fs.statSync(fullPath);
      const isDir = stats.isDirectory();

      if (isDir) {
        const files = fs.readdirSync(fullPath).filter(f => f.endsWith('.md'));
        manifest.sections.push({
          type: 'directory',
          name: docPath,
          fileCount: files.length,
          files: files.slice(0, 5), // First 5 files
        });
        console.log(`✅ ${docPath} — ${files.length} files`);
      } else {
        manifest.sections.push({
          type: 'file',
          name: docPath,
          size: stats.size,
        });
        console.log(`✅ ${docPath} — ${(stats.size / 1024).toFixed(1)}KB`);
      }
    } else {
      console.log(`⚠️  ${docPath} — not found`);
    }
  }

  // Save manifest
  const manifestPath = path.join(CONTEXT7_CONFIG.projectPath, '.context7-manifest.json');
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  console.log('');
  console.log(`📋 Manifest saved: .context7-manifest.json`);
  console.log('');
  console.log('💡 Integration tips:');
  console.log('  • Query docs: npx context7 daanaa "how does scoring work?"');
  console.log('  • List projects: npx context7 search daanaa');
  console.log('  • Save output: npx context7 daanaa "explain V6 scoring" --save');
  console.log('');
  console.log('✅ Context7 integration ready');
}

indexCodebase().catch(err => {
  console.error('❌ Error indexing codebase:', err.message);
  process.exit(1);
});
