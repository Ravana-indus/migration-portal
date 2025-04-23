# Migration Portal

Migration Portal is a custom Frappe/ERPNext application designed to manage migration services, applications, and client data. It provides a comprehensive interface for tracking and processing migration applications.

## Features

- Client management
- Application processing and tracking
- Document management
- Integration with external systems
- Workflow automation
- Reporting and analytics

## Installation

### Prerequisites

- Frappe/ERPNext environment
- Python 3.10+
- MariaDB/MySQL

### Installation Steps

1. Change to your bench directory:
   ```
   cd frappe-bench
   ```

2. Get the app from GitHub:
   ```
   bench get-app migration_portal https://github.com/Ravana-indus/migration-portal
   ```

3. Install the app on your site:
   ```
   bench --site your-site.local install-app migration_portal
   ```

4. Migrate the database:
   ```
   bench --site your-site.local migrate
   ```

## Configuration

1. Set up the required settings in the Migration Portal Settings doctype
2. Configure user permissions
3. Set up workflows as needed

## Usage

Please refer to the user documentation for detailed usage instructions.

## License

MIT
