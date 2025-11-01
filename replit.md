# Overview

This is a Flask-based web application that analyzes ZIP file contents with configurable analysis profiles. The application allows users to upload ZIP archives and generates detailed reports about the file structure, programming languages used, and other statistics based on selected analysis profiles. The tool provides filtered views of project contents, making it easier to understand project composition while excluding irrelevant files (like dependencies, build artifacts, etc.).

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Application Framework
- **Technology**: Flask (Python web framework)
- **Rationale**: Lightweight framework suitable for single-purpose utility applications with minimal overhead
- **Template Engine**: Jinja2 (Flask's default templating)
- **Static Assets**: Inline CSS in templates for simplicity

## File Upload & Processing
- **Upload Handling**: Flask's built-in file upload with 50MB size limit
- **Allowed Formats**: ZIP files only
- **Storage**: Instance-relative downloads folder for generated reports
- **Processing**: In-memory ZIP file analysis without extracting to disk (security consideration)

## Analysis Profile System
- **Design Pattern**: Strategy pattern with abstract base class (`AnalysisProfile`)
- **Purpose**: Encapsulates filtering logic, categorization rules, and reporting for different project types
- **Extensibility**: New profiles can be added by implementing the abstract interface
- **Key Methods**:
  - `is_file_ignored()`: Determines which files to exclude from analysis
  - Profile identification and naming for UI integration

## Language Detection
- **Approach**: Extension-based mapping
- **Coverage**: Supports 20+ programming languages and config file formats
- **Implementation**: Simple dictionary lookup in `get_language_from_filename()`

## Report Generation
- **Format**: Text-based reports (likely plain text or markdown)
- **Storage**: Generated reports saved to downloads folder with unique identifiers
- **Statistics**: File counting, language distribution using `Counter` class
- **Delivery**: Direct download links provided after processing

## Configuration Management
- **Critical Files Detection**: Hardcoded set of essential config files (pyproject.toml, requirements.txt, Dockerfile, docker-compose.yml)
- **Purpose**: Prioritizes important configuration files in analysis
- **User-Centric**: Focuses on files the user needs to understand the project quickly

## Session Management
- **Flash Messages**: Category-based (success/error) user feedback
- **Secret Key**: Hardcoded (should be environment variable in production)
- **Session ID**: UUID generation for tracking downloads

# External Dependencies

## Python Packages
- **Flask**: Web framework (core dependency)
- **zipfile**: Standard library for ZIP archive handling
- **datetime**: Timestamp generation for reports
- **collections.Counter**: Statistical aggregation of file types/languages

## File System
- **Instance Path**: Flask instance folder for storing generated downloads
- **Directory Structure**: Auto-created downloads folder at application startup

## Frontend
- **No External JavaScript Libraries**: Vanilla JavaScript for copy-to-clipboard functionality
- **No CSS Framework**: Custom inline styles for lightweight deployment
- **Browser Requirements**: Modern browser with file upload support

## Potential Future Integrations
- **Database**: None currently (stateless application)
- **Authentication**: None (single-user utility tool)
- **Cloud Storage**: Not implemented (uses local file system)