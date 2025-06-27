# NuYu Medical Spa - Odoo Customizations

## Quick Start for Team
1. Clone: `git clone https://github.com/MrSKXX/nuyu-odoo-customizations.git`
2. Start: `cd docker && docker-compose up -d`
3. Access: http://localhost:8069
4. Create database: "nuyu_dev"

## Modules
- `medical_inventory/` - Georges: Medical spa inventory features
- `pos_lebanon/` - Lebanese currency and POS customizations  
- `appointment_enhancements/` - Appointment booking improvements
- `social_media/` - Social media integration

## Development Team
- Georges: Inventory + Infrastructure Setup
- Muneeb: Custom Features + POS Development

## Module Development
Each module goes in `modules/[module_name]/`
Use `docker-compose restart odoo` after changes.