#!/usr/bin/env node
/**
 * BeforeAgent Hook: Display pending tasks
 * Windows 11 Compatible
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

async function main() {
  try {
    const input = JSON.parse(fs.readFileSync(0, 'utf-8'));
    
    // Get task list ID
    const taskListId = process.env.GEMINI_TASK_LIST_ID || 'default';
    
    // Windows-compatible path
    const tasksDir = path.join(os.homedir(), '.gemini', 'tasks');
    const tasksFile = path.join(tasksDir, `${taskListId}.json`);
    
    if (!fs.existsSync(tasksFile)) {
      console.log(JSON.stringify({}));
      return;
    }
    
    const tasks = JSON.parse(fs.readFileSync(tasksFile, 'utf-8'));
    const pending = tasks.filter(t => t.status === 'pending' || t.status === 'in_progress');
    
    if (pending.length === 0) {
      console.log(JSON.stringify({}));
      return;
    }
    
    // Build task display
    let taskDisplay = '\n📋 Active Tasks:\n';
    pending.slice(0, 10).forEach(task => {
      const icon = task.status === 'in_progress' ? '⟳' : '○';
      const blockers = task.blocked_by?.length > 0 
        ? ` [blocked by: ${task.blocked_by.join(', ')}]` 
        : '';
      taskDisplay += `  ${icon} ${task.id}: ${task.subject}${blockers}\n`;
    });
    
    if (pending.length > 10) {
      taskDisplay += `  ... and ${pending.length - 10} more\n`;
    }
    
    // Inject as additional context
    console.log(JSON.stringify({
      systemMessage: taskDisplay,
      hookSpecificOutput: {
        hookEventName: "BeforeAgent",
        additionalContext: taskDisplay
      }
    }));
    
  } catch (error) {
    console.error('BeforeAgent hook error:', error.message);
    console.log(JSON.stringify({}));
  }
}

main();