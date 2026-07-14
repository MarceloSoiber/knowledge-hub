# SpecKit Constitution

## Core Principles

### Code Quality
- **Type Safety**: Enforce strict typing in TypeScript (frontend) and Python type hints (backend)
- **Clean Architecture**: Maintain separation of concerns with clear boundaries between business logic, API routes, and data access
- **Code Review**: All changes must pass code review before merging; enforce linting rules with ESLint and Pylint
- **Maintainability**: Write self-documenting code with meaningful names; complex logic must have clear comments
- **Consistency**: Follow project-specific patterns established in `backend/app/services` and keep routes thin in `backend/app/api/routes`

### Testing Standards
- **Test Coverage**: Maintain minimum 80% coverage for critical paths (services, core logic)
- **Unit Tests**: Test services and business logic independently in `tests/` directory
- **Integration Tests**: Test API endpoints with real database context using PostgreSQL + pgvector
- **Performance Tests**: Validate embedding generation and search performance within acceptable thresholds
- **Test Command**: Run tests via `.venv/bin/python -m pytest` with verbose output for debugging
- **Pre-commit Validation**: Run tests before pushing to catch failures early

### User Experience Consistency
- **Frontend Simplicity**: Keep frontend focused on status display, ingestion interface, and search functionality
- **Responsive Design**: Ensure UI works across desktop and mobile viewports
- **Clear Feedback**: Provide immediate feedback on user actions (ingestion progress, search results, errors)
- **Accessibility**: Use semantic HTML and ARIA labels for screen readers
- **Consistent Styling**: Maintain visual consistency across components using centralized style definitions in `src/styles.css`

### Performance Requirements
- **Embedding Speed**: Embeddings must be generated efficiently, utilizing batch processing where applicable
- **Search Performance**: Vector similarity search must complete within 500ms for typical queries
- **Database Optimization**: Use pgvector indexes (HNSW) for efficient similarity searches; monitor query performance
- **API Response Time**: All endpoints should respond within 1 second under normal load
- **Memory Management**: Profile memory usage during batch operations; avoid loading entire datasets into memory

## Technology Stack Guidelines

### Backend
- **Framework**: FastAPI for REST API endpoints
- **Database**: PostgreSQL with pgvector extension for vector embeddings
- **ORM/Session**: SQLAlchemy with session management in `backend/app/db/session.py`
- **Schema Validation**: Pydantic v2 with StringConstraints for data validation and sanitization
- **MCP Integration**: Follow FastMCP SDK approach from official documentation

### Frontend
- **Build Tool**: Vite for development and production builds
- **Language**: TypeScript for type safety
- **Styling**: CSS with utility-first approach

### MCP Server
- **SDK**: FastMCP from official Model Context Protocol SDK
- **Tool Naming**: Keep tool names short and domain-oriented
- **Authentication**: Use Bearer token authentication for client connections

## Development Workflow

1. **Branch Strategy**: Create feature branches from `main`; use clear naming: `feature/`, `fix/`, `refactor/`
2. **Commit Messages**: Write descriptive messages explaining the "why" behind changes
3. **Code Standards**: Run linters and formatters before committing
4. **Testing**: Write tests for new features; all tests must pass before PR creation
5. **Documentation**: Update API docs in `doc/API.md` for new endpoints; maintain inline comments for complex logic

## File Organization Standards

- **Business Logic**: Store in `backend/app/services/` (e.g., knowledge.py, embeddings.py, rag.py)
- **API Routes**: Keep thin and focused in `backend/app/api/routes/`
- **Database Models**: Define in `backend/app/db/models.py`
- **Schemas**: Pydantic models in `backend/app/schemas/`
- **Tests**: Organize tests mirroring source structure in `tests/`

## Quality Gates

- ✅ All tests passing
- ✅ Type checking passes (mypy or Pylance)
- ✅ Linting passes (ESLint, Pylint)
- ✅ Code review approval
- ✅ Performance benchmarks met
- ✅ Documentation updated
