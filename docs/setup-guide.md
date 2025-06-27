# Development Setup Guide

## Prerequisites
- Docker Desktop installed
- Git access to repository
- VSCode (recommended)

## Setup Steps
1. `git clone https://github.com/MrSKXX/nuyu-odoo-customizations.git`
2. `cd nuyu-odoo-customizations/docker`
3. `docker-compose up -d`
4. Open browser: http://localhost:8069
5. Create database: "nuyu_dev"
6. Install custom modules from Apps menu

## Daily Workflow
1. `docker-compose up -d` (start environment)
2. Develop in `modules/` folder
3. `docker-compose restart odoo` (after changes)
4. Test in browser
5. Commit: `git add . && git commit -m "your message"`
6. Push: `git push origin [branch-name]`