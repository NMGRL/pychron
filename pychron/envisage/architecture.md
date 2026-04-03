# Envisage Architecture

## Purpose

This package is the application shell for Pychron. It wires together plugins,
task windows, browser panes, preferences, startup helpers, and shared Qt/Traits
UI behavior.

## Main Responsibilities

- build and launch the Envisage task application
- register plugins and services
- host task panes, editors, actions, and browser flows
- provide shared application-level UI behavior
- coordinate startup-time initialization and theme setup

## Key Entry Points

- `pychron.envisage.pychron_run`
  - runtime launch path used after launcher/bootstrap setup
  - assembles plugins and starts the application
- `pychron/applications`
  - application classes and application-specific composition
- `launchers/`
  - user-facing launcher scripts that enter the runtime

## Important Subareas

- `browser/`
  - shared sample, project, and analysis browsing flows
  - heavily reused across processing and review workflows
- `tasks/`
  - task panes, preferences dialog, layout manager, and task shell helpers
- `initialization/`
  - startup-time plugin initialization support
- `stylesheets/`
  - app-specific stylesheet resources

## Plugin Model

Pychron composes features through Envisage plugins. A typical path is:

1. launcher chooses an application
2. application adds core and feature plugins
3. plugins register services, tasks, and panes
4. task windows resolve services through the application

When behavior appears in the UI but the implementation is unclear, start by
finding the task or plugin class rather than searching every consumer.

## Change Guidance

- Fix shared behavior here only if the issue is truly application-wide.
- If a bug only affects one workflow, prefer changing that workflow's task,
  pane, editor, or adapter instead of the global shell.
- Browser tables and shared dialogs are high-traffic surfaces; validate them
  carefully after changing common UI code.
