#!/usr/bin/env node
/**
 * AfterAgent Hook: Ralph Wiggum Loop Controller
 * Windows 11 Compatible
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Configuration
const RALPH_MODE = process.env.GEMINI_RALPH_MODE === 'true';
const MAX_ITERATIONS = parseInt(process.env.GEMINI_MAX_ITERATIONS || '25');
const COMPLETION_PROMISE = process.env.GEMINI_COMPLETION_PROMISE || 'complete';
const TASK_LIST_ID = process.env.GEMINI_TASK_LIST_ID || 'default';

// Windows-compatible paths
const homeDir = os.homedir();
const stateDir = path.join(homeDir, '.gemini', 'ralph-state');
const stateFile = path.join(stateDir, `${TASK_LIST_ID}.json`);
const tasksDir = path.join(homeDir, '.gemini', 'tasks');

function loadState() {
  if (!fs.existsSync(stateFile)) {
    return { iteration: 0, startTime: Date.now() };
  }
  return JSON.parse(fs.readFileSync(stateFile, 'utf-8'));
}

function saveState(state) {
  if (!fs.existsSync(stateDir)) {
    fs.mkdirSync(stateDir, { recursive: true });
  }
  fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
}

function clearState() {
  if (fs.existsSync(stateFile)) {
    fs.unlinkSync(stateFile);
  }
}

function loadTasks() {
  const tasksFile = path.join(tasksDir, `${TASK_LIST_ID}.json`);
  if (!fs.existsSync(tasksFile)) {
    return [];
  }
  return JSON.parse(fs.readFileSync(tasksFile, 'utf-8'));
}

function checkTasksComplete() {
  const tasks = loadTasks();
  if (tasks.length === 0) {
    return { complete: true, reason: 'No tasks exist' };
  }
  
  const incomplete = tasks.filter(t => t.status !== 'completed');
  
  if (incomplete.length === 0) {
    return { complete: true, reason: 'All tasks completed' };
  }
  
  return {
    complete: false,
    reason: `${incomplete.length} tasks still incomplete`,
    incompleteTasks: incomplete.map(t => ({
      id: t.id,
      subject: t.subject,
      status: t.status,
      blocked_by: t.blocked_by
    }))
  };
}

function runVerification() {
  const projectDir = process.env.GEMINI_PROJECT_DIR || process.cwd();
  
  // Check for PowerShell script first (Windows)
  const verifyPs1 = path.join(projectDir, '.gemini', 'verify.ps1');
  const verifyPs1Alt = path.join(projectDir, 'scripts', 'verify.ps1');
  // Then check for bash script (WSL/Git Bash)
  const verifySh = path.join(projectDir, '.gemini', 'verify.sh');
  const verifyShAlt = path.join(projectDir, 'scripts', 'verify.sh');
  // Then check for Node.js script
  const verifyJs = path.join(projectDir, '.gemini', 'verify.js');
  
  let verifyScript = null;
  let command = null;
  
  if (fs.existsSync(verifyPs1)) {
    verifyScript = verifyPs1;
    command = `powershell -ExecutionPolicy Bypass -File "${verifyPs1}"`;
  } else if (fs.existsSync(verifyPs1Alt)) {
    verifyScript = verifyPs1Alt;
    command = `powershell -ExecutionPolicy Bypass -File "${verifyPs1Alt}"`;
  } else if (fs.existsSync(verifySh)) {
    verifyScript = verifySh;
    // Try bash (Git Bash) or sh (WSL)
    command = process.platform === 'win32' 
      ? `bash "${verifySh}"` 
      : `sh "${verifySh}"`;
  } else if (fs.existsSync(verifyShAlt)) {
    verifyScript = verifyShAlt;
    command = process.platform === 'win32' 
      ? `bash "${verifyShAlt}"` 
      : `sh "${verifyShAlt}"`;
  } else if (fs.existsSync(verifyJs)) {
    verifyScript = verifyJs;
    command = `node "${verifyJs}"`;
  }
  
  if (!verifyScript) {
    // If no specific verification script, we can assume passed or implement default checks
    return { passed: true, reason: 'No verification script found (skipped)' };
  }
  
  try {
    // Windows needs shell: true for proper command execution
    execSync(command, { 
      stdio: 'pipe',
      shell: true,
      windowsHide: true
    });
    return { passed: true, reason: 'Verification passed' };
  } catch (error) {
    return {
      passed: false,
      reason: 'Verification failed',
      output: error.stderr?.toString() || error.stdout?.toString() || error.message
    };
  }
}

async function main() {
  try {
    const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
    
    // If Ralph mode not enabled, just pass through
    if (!RALPH_MODE) {
      console.log(JSON.stringify({}));
      return;
    }
    
    const { prompt_response, stop_hook_active } = input;
    
    // Load/update iteration state
    const state = loadState();
    state.iteration += 1;
    saveState(state);
    
    // Log to stderr for debugging
    console.error(`Ralph iteration ${state.iteration}/${MAX_ITERATIONS}`);
    
    // Check max iterations (safety brake)
    if (state.iteration >= MAX_ITERATIONS) {
      console.error('Max iterations reached, forcing stop');
      clearState();
      console.log(JSON.stringify({
        systemMessage: `⚠️  Max iterations (${MAX_ITERATIONS}) reached. Stopping Ralph loop.`,
        decision: 'allow' // Let it stop
      }));
      return;
    }
    
    // Check if agent output completion promise
    const hasCompletionPromise = prompt_response?.toLowerCase().includes(COMPLETION_PROMISE.toLowerCase());
    
    if (!hasCompletionPromise) {
      // Agent didn't say it's complete, so force retry
      console.error('No completion promise found, continuing loop');
      console.log(JSON.stringify({
        decision: 'deny',
        reason: `You must continue working until you output "${COMPLETION_PROMISE}". Check tasks and verification.`,
        systemMessage: '🔄 Ralph loop continuing...'
      }));
      return;
    }
    
    // Agent claims completion, verify it's true
    console.error('Completion promise found, verifying...');
    
    // Check 1: All tasks complete?
    const taskCheck = checkTasksComplete();
    if (!taskCheck.complete) {
      console.error('Tasks incomplete:', taskCheck.reason);
      console.log(JSON.stringify({
        decision: 'deny',
        reason: `Work incomplete: ${taskCheck.reason}\n\nIncomplete tasks:\n${
          taskCheck.incompleteTasks.map(t => `- ${t.id}: ${t.subject} (${t.status})`).join('\n')
        }\n\nComplete these tasks before outputting "${COMPLETION_PROMISE}".`,
        systemMessage: '❌ Tasks incomplete, continuing work...'
      }));
      return;
    }
    
    // Check 2: Verification passes?
    const verifyCheck = runVerification();
    if (!verifyCheck.passed) {
      console.error('Verification failed:', verifyCheck.reason);
      console.log(JSON.stringify({
        decision: 'deny',
        reason: `Verification failed: ${verifyCheck.reason}\n\nOutput:\n${verifyCheck.output}\n\nFix the issues and run verification again.`,
        systemMessage: '❌ Verification failed, fixing issues...'
      }));
      return;
    }
    
    // All checks passed! Work is complete
    console.error('All verification passed, allowing stop');
    clearState();
    
    const tasks = loadTasks();
    const completed = tasks.filter(t => t.status === 'completed').length;
    
    console.log(JSON.stringify({
      decision: 'allow',
      systemMessage: `✅ Ralph loop complete! ${completed} tasks completed in ${state.iteration} iterations. 🎉`
    }));
    
  } catch (error) {
    console.error('AfterAgent hook error:', error.message);
    // On error, allow stop (safe default)
    console.log(JSON.stringify({
      systemMessage: `⚠️  Hook error: ${error.message}`
    }));
  }
}

main();