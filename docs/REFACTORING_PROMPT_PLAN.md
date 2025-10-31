Creating docs/REFACTORING_PLAN.md based on docs/ARCHITECTURE.md file

Based on the observations above, here are some suggestions for refactoring the project to enhance its structure, maintainability, and scalability:

- **Project Structure**: Restructure into a Python package with src/, tests/, and docs/ directories.
- **Architecture Patterns**: Apply SOLID, KISS, 12-factor app, design principles, ports & adapters even for tools/small scripts. Architectural style (layered, microservices, event-driven, etc.)
- **Packaging**: Make the project installable via pip with a proper setup.py or pyproject.toml.
- **Configuration Management**: Use python-dotenv for .env .envrc files and config.py for structured config.
- **Async Refactor**: Convert blocking calls to async using asyncio and aiohttp.
- **Error Handling**: Implement custom exceptions and centralized error handling. Rich with logging and exits.
- **Logging**: Global logger
- **Testing**: Add integration tests and increase unit test coverage.
- **CI/CD**: Set up GitHub Actions for linting, testing, and deployment.
- **Dependency Management**: Use pyproject.toml and poetry for managing dependencies and virtual environments.
- **Performance**: Profile and optimize any slow parts of the code, especially I/O operations.
- **Documentation**: Good README + architecture diagram plantuml/C4, add docstrings, type hints. Follow the folder structure below.