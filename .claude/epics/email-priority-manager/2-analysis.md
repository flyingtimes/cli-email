---
title: Database Schema Design Analysis
epic: email-priority-manager
task_number: 2
analysis_type: technical
date: 2025-09-16
---

# Database Schema Design Analysis for email-priority-manager

## Executive Summary

This analysis provides a comprehensive technical breakdown of the SQLite database schema design task. The database will serve as the foundation for storing email metadata, attachments, classifications, and priority information for the email priority management system.

## 1. Technical Requirements

### Core Database Components

**Mandatory Tables:**
- `emails`: Primary table for email storage
- `attachments`: File attachment metadata and storage paths
- `classifications`: AI-generated priority scores and classifications
- `rules`: User-defined filtering and prioritization rules
- `history`: Audit trail for processing and user actions
- `tags`: Email tagging system for categorization
- `email_tags`: Many-to-many relationship table

**Schema Design Requirements:**
- SQLite3 database engine
- Normalized data structure (3NF)
- Proper data types and constraints
- Full-text search capabilities
- Foreign key relationships with integrity constraints
- Comprehensive indexing strategy
- Migration system for schema evolution

### Performance Requirements
- Query response time < 2 seconds for common operations
- Support for 10,000+ email records
- Efficient full-text search across email content
- Proper indexing for priority-based queries

## 2. File Structure

### Required Files to Create

**Database Schema Files:**
```
src/database/
├── __init__.py
├── schema.py              # Database schema definition
├── migrations.py          # Migration system
├── models.py              # ORM models/data classes
├── connections.py         # Connection management
├── operations.py          # CRUD operations
└── utils.py               # Database utilities
```

**Migration Files:**
```
migrations/
├── 001_initial_schema.py  # Initial database creation
└── migration_manager.py   # Migration orchestration
```

**Configuration Files:**
```
config/
└── database.yaml          # Database configuration
```

### Files to Modify
- `requirements.txt` (add SQLite dependencies)
- `config/settings.py` (add database configuration)
- `tests/` (add database tests)

## 3. Implementation Strategy

### Phase 1: Core Schema Design
1. **Table Definitions**
   - Design normalized table structures
   - Define appropriate data types and constraints
   - Implement foreign key relationships
   - Add proper indexing strategy

2. **Database Initialization**
   - Create SQLite database file
   - Execute schema creation scripts
   - Set up connection management
   - Implement error handling

### Phase 2: Advanced Features
1. **Full-Text Search**
   - Create FTS5 virtual tables for email content
   - Implement search indexing
   - Add search utility functions

2. **Migration System**
   - Version tracking table
   - Migration script framework
   - Rollback capabilities
   - Migration execution engine

### Phase 3: Data Access Layer
1. **ORM/Models**
   - Data classes for each entity
   - Validation methods
   - Serialization/deserialization

2. **Operations Layer**
   - CRUD operations for each table
   - Complex query methods
   - Transaction management
   - Performance optimization

## 4. Dependencies

### Prerequisites
- **Database Engine**: SQLite3 (built-in with Python)
- **ORM**: SQLAlchemy or raw SQLite3 (decision needed)
- **Migration Tool**: Alembic or custom migration system
- **Testing**: pytest with database fixtures

### Dependencies on This Task
- **Task 3**: Email Retrieval & Processing (depends on email storage schema)
- **Task 4**: Classification Engine (depends on classification storage)
- **Task 5**: AI Integration (depends on classification and rules tables)
- **Task 6**: CLI Interface (depends on all database operations)

### External Dependencies
- Python 3.8+
- SQLite3
- Optional: SQLAlchemy, Alembic

## 5. Work Streams (Parallel Opportunities)

### Stream A: Core Schema Development
- Table design and SQL scripts
- Database initialization
- Basic CRUD operations

### Stream B: Search & Indexing
- Full-text search implementation
- Index optimization
- Search query optimization

### Stream C: Migration System
- Version tracking
- Migration framework
- Rollback mechanisms

### Stream D: Testing & Validation
- Unit tests for schema
- Integration tests
- Performance testing
- Data integrity validation

## 6. Success Criteria

### Technical Validation
- [ ] All 7 core tables created with proper schema
- [ ] Foreign key constraints implemented and enforced
- [ ] Indexing strategy applied with performance benchmarks
- [ ] Full-text search functional on email content
- [ ] Migration system operational with version tracking
- [ ] Connection pooling and error handling implemented
- [ ] Data integrity constraints enforced (UNIQUE, NOT NULL, CHECK)
- [ ] Backup and recovery procedures documented

### Performance Criteria
- [ ] Database initialization < 5 seconds
- [ ] Email insertion < 100ms per record
- [ ] Search queries < 2 seconds response time
- [ ] Migration execution < 30 seconds
- [ ] Memory usage < 50MB for 10,000 emails

### Quality Assurance
- [ ] Complete schema documentation with ERD
- [ ] Migration procedures documented
- [ ] Performance benchmarks documented
- [ ] Test coverage > 80% for database operations
- [ ] Data validation and error handling tested

## Schema Design Specifications

### Table: emails
```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    subject TEXT NOT NULL,
    sender TEXT NOT NULL,
    recipients TEXT NOT NULL,
    cc TEXT,
    bcc TEXT,
    body_text TEXT,
    body_html TEXT,
    received_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    size_bytes INTEGER,
    has_attachments BOOLEAN DEFAULT FALSE,
    is_read BOOLEAN DEFAULT FALSE,
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: attachments
```sql
CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    size_bytes INTEGER,
    mime_type TEXT,
    content_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
);
```

### Table: classifications
```sql
CREATE TABLE classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER UNIQUE NOT NULL,
    priority_score INTEGER NOT NULL CHECK (priority_score BETWEEN 1 AND 5),
    urgency_level TEXT NOT NULL CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
    importance_level TEXT NOT NULL CHECK (importance_level IN ('low', 'medium', 'high', 'critical')),
    classification_type TEXT NOT NULL,
    confidence_score REAL CHECK (confidence_score BETWEEN 0 AND 1),
    ai_analysis TEXT,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
);
```

### Table: rules
```sql
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('sender', 'keyword', 'time', 'custom')),
    condition TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('classify', 'tag', 'flag', 'move')),
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: history
```sql
CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    action_type TEXT NOT NULL,
    action_details TEXT,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE SET NULL
);
```

### Table: tags
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: email_tags
```sql
CREATE TABLE email_tags (
    email_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (email_id, tag_id),
    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

## Implementation Timeline

**Week 1: Core Schema**
- Days 1-2: Table design and SQL scripts
- Days 3-4: Database initialization and connection management
- Days 5-7: Basic CRUD operations

**Week 2: Advanced Features**
- Days 1-3: Full-text search implementation
- Days 4-5: Migration system development
- Days 6-7: Performance optimization

**Week 3: Testing & Documentation**
- Days 1-3: Comprehensive testing
- Days 4-5: Performance benchmarking
- Days 6-7: Documentation completion

## Risk Assessment

### Technical Risks
- **Schema Design Flaws**: Inadequate normalization or indexing
- **Performance Issues**: Poor query optimization for large datasets
- **Migration Complexity**: Difficult schema evolution requirements

### Mitigation Strategies
- Iterative schema validation with test data
- Performance testing with realistic email volumes
- Comprehensive migration testing and rollback procedures

## Next Steps

1. **Immediate**: Create database schema files and initial scripts
2. **Short-term**: Implement core CRUD operations and testing
3. **Medium-term**: Add full-text search and migration system
4. **Long-term**: Performance optimization and documentation

This analysis provides a comprehensive roadmap for implementing the database schema design task, with clear technical specifications, file structure, and implementation strategy.