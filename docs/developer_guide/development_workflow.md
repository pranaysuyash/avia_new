# Development Workflow

This document describes the development workflow for the Audio/Video Transcription & Analysis Platform.

## Branching Model

The project uses the following branching model:

-   `main`: The main branch, which represents the latest stable release.
-   `develop`: The development branch, which represents the latest development version.
-   `feature/*`: Feature branches, which are used to develop new features.
-   `bugfix/*`: Bugfix branches, which are used to fix bugs.

## Committing Changes

All changes should be committed to a feature or bugfix branch. Once the changes are complete, a pull request should be created to merge the changes into the `develop` branch.

## Pull Requests

All pull requests must be reviewed and approved by at least one other developer before they can be merged. Pull requests should include a detailed description of the changes, as well as any relevant screenshots or videos.

## Code Style

The project follows the PEP 8 style guide for Python code. All code should be formatted with Black before it is committed.

## Testing

All new code should be accompanied by unit tests. The tests should be run before a pull request is created to ensure that the changes do not break any existing functionality.
