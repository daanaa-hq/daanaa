#!/usr/bin/env node

/**
 * Ralph Task Orchestrator for Daanaa
 *
 * Executes autonomous agent workflows for:
 * - Phase 1-4 deployments
 * - Feature development iterations
 * - Data pipeline runs
 *
 * Ralph respects Stewardship governance gates and maintains task state.
 *
 * Usage:
 *   node scripts/ralph-setup.js                          # Show available tasks
 *   node scripts/ralph-setup.js <task_name>              # Start new task
 *   node scripts/ralph-setup.js --resume                 # Resume last task
 *   node scripts/ralph-setup.js --status                 # Show current task status
 */

const fs = require('fs');
const path = require('path');

const RALPH_BASE_CONFIG = {
  projectName: 'daanaa',
  autonomyLevel: 'supervised',
  governanceGates: [
    'principles_check',
    'privacy_gate',
    'data_source_verification',
    'founder_approval',
  ],
  taskTemplates: {
    feature_development: {
      steps: [
        'develop_locally',
        'run_qc_tests',
        'commit_if_passing',
        'await_approval',
        'deploy_if_approved',
      ],
      governance: ['principles_check', 'privacy_gate'],
    },
    data_pipeline: {
      steps: [
        'validate_sources',
        'run_scorer',
        'build_fts_index',
        'verify_coverage',
        'smoke_test',
      ],
      governance: ['data_source_verification', 'privacy_gate'],
    },
    phase_deployment: {
      steps: [
        'verify_all_blockers_fixed',
        'run_full_test_suite',
        'check_principles',
        'prepare_deployment',
        'await_founder_approval',
        'deploy_to_production',
        'verify_smoke_tests',
        'document_in_decisions',
      ],
      governance: ['principles_check', 'privacy_gate', 'founder_approval'],
    },
  },
  integrations: {
    codex: {
      enabled: true,
      role: 'architectural_review',
      gates: ['phase_deployment'],
    },
    playwright: {
      enabled: true,
      role: 'quality_assurance',
      command: 'bash scripts/qc-test-suite.sh',
    },
    context7: {
      enabled: true,
      role: 'documentation_context',
      command: 'node scripts/context7-index.js',
    },
  },
};

const CONFIG_PATH = path.join('/home/akbar/meritgiving', '.ralph-config.json');

function loadConfig() {
  if (fs.existsSync(CONFIG_PATH)) {
    try {
      const data = fs.readFileSync(CONFIG_PATH, 'utf8');
      return JSON.parse(data);
    } catch (e) {
      return { ...RALPH_BASE_CONFIG };
    }
  }
  return { ...RALPH_BASE_CONFIG };
}

function saveConfig(config) {
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2));
}

function showAvailableTasks(config) {
  console.log('🎭 Ralph: Available Task Templates\n');
  Object.entries(config.taskTemplates).forEach(([name, tmpl]) => {
    console.log(`${name}:`);
    tmpl.steps.forEach(step => {
      console.log(`  → ${step}`);
    });
    console.log(`  Governance: ${tmpl.governance.join(', ')}\n`);
  });
}

function startTask(taskName, config) {
  if (!config.taskTemplates[taskName]) {
    console.error(`❌ Unknown task: ${taskName}`);
    console.error(`Available tasks: ${Object.keys(config.taskTemplates).join(', ')}`);
    process.exit(1);
  }

  const template = config.taskTemplates[taskName];
  const now = new Date().toISOString();

  const currentTask = {
    name: taskName,
    started: now,
    currentStep: 0,
    steps: template.steps,
    governance: template.governance,
    status: 'in_progress',
    results: {},
  };

  config.currentTask = currentTask;
  saveConfig(config);

  console.log(`🎭 Ralph: Starting ${taskName}`);
  console.log(`⏱️  Started: ${now}`);
  console.log('');
  console.log('📋 Steps:');
  template.steps.forEach((step, i) => {
    const indicator = i === 0 ? '→' : ' ';
    console.log(`  ${indicator} [${i}/${template.steps.length}] ${step}`);
  });
  console.log('');
  console.log('🚪 Governance Gates:');
  template.governance.forEach(gate => {
    console.log(`  ✓ ${gate}`);
  });
  console.log('');
  console.log('💾 Task state saved to .ralph-config.json');
  console.log('');
  console.log('Usage:');
  console.log('  node scripts/ralph-setup.js --status   # Check progress');
  console.log('  node scripts/ralph-setup.js --resume   # Continue from here');
}

function resumeTask(config) {
  if (!config.currentTask) {
    console.error('❌ No active task to resume');
    process.exit(1);
  }

  const task = config.currentTask;
  console.log(`🎭 Ralph: Resuming ${task.name}`);
  console.log(`⏱️  Originally started: ${task.started}`);
  console.log(`📊 Progress: ${task.currentStep}/${task.steps.length}`);
  console.log('');
  console.log('Next step:');
  console.log(`  [${task.currentStep}/${task.steps.length}] ${task.steps[task.currentStep]}`);
  console.log('');
  console.log('After completing this step, call:');
  console.log('  node scripts/ralph-setup.js --step-done');
}

function showStatus(config) {
  if (!config.currentTask) {
    console.log('🎭 Ralph: No active task');
    console.log('');
    console.log('Start a task with:');
    console.log('  node scripts/ralph-setup.js <task_name>');
    return;
  }

  const task = config.currentTask;
  console.log(`🎭 Ralph: Task Status\n`);
  console.log(`Task: ${task.name}`);
  console.log(`Status: ${task.status}`);
  console.log(`Progress: ${task.currentStep}/${task.steps.length}`);
  console.log(`Started: ${task.started}\n`);

  console.log('Steps:');
  task.steps.forEach((step, i) => {
    const indicator = i < task.currentStep ? '✅' : i === task.currentStep ? '→' : ' ';
    console.log(`  ${indicator} [${i}/${task.steps.length}] ${step}`);
  });
}

async function main() {
  const args = process.argv.slice(2);
  const config = loadConfig();

  if (args.length === 0) {
    showAvailableTasks(config);
    return;
  }

  const cmd = args[0];

  if (cmd === '--status') {
    showStatus(config);
  } else if (cmd === '--resume') {
    resumeTask(config);
  } else if (cmd === '--task-list') {
    showAvailableTasks(config);
  } else if (config.taskTemplates[cmd]) {
    startTask(cmd, config);
  } else {
    console.error(`❌ Unknown command: ${cmd}`);
    console.log('');
    console.log('Usage:');
    console.log('  node scripts/ralph-setup.js                 # List tasks');
    console.log('  node scripts/ralph-setup.js <task_name>     # Start task');
    console.log('  node scripts/ralph-setup.js --status        # Show current status');
    console.log('  node scripts/ralph-setup.js --resume        # Resume last task');
    process.exit(1);
  }
}

main().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
