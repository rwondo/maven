# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    ConsensusOrchestrator                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │RoleAssigner │  │IterationMgr│  │   TraceRecorder     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │  Model A  │   │  Model B  │   │  Model C  │
     │(Interface)│   │(Interface)│   │(Interface)│
     └───────────┘   └───────────┘   └───────────┘
            │               │               │
            ▼               ▼               ▼
     ┌───────────┐   ┌───────────┐   ┌───────────┐
     │Claude API │   │OpenAI API │   │Gemini API │
     └───────────┘   └───────────┘   └───────────┘
```

## Components

### ConsensusOrchestrator
Main coordinator. Manages the verification lifecycle:
- Initializes models and configuration
- Runs iteration loop
- Checks for consensus after each round
- Generates final result

### RoleAssigner
Handles random role assignment:
- Shuffles model list
- Maps models to roles
- Supports role rotation between iterations

### ModelInterface
Abstract base class for model integrations:
- Defines `generate(prompt, role)` method
- Handles API authentication
- Manages rate limiting and retries

### ConsensusDetector
Determines when agreement is reached:
- Extracts key claims from responses
- Computes semantic similarity
- Returns agreement score

### TraceRecorder
Captures audit trail:
- Logs each step with timestamp
- Stores full response content
- Generates exportable trace

## Data Flow

```
Query
  │
  ▼
┌─────────────────┐
│ Role Assignment │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│    Architect    │────▶│     Skeptic     │
│   (proposes)    │     │   (challenges)  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │    Mediator     │
            │  (synthesizes)  │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────┐
            │Consensus Check  │
            └────────┬────────┘
                     │
          ┌─────────┴─────────┐
          ▼                   ▼
    [Consensus]          [No Consensus]
          │                   │
          ▼                   ▼
      Result            Rotate & Retry
```

## Extension Points

### Adding New Models
1. Implement `ModelInterface` abstract class
2. Register in model factory
3. Handle model-specific prompt formatting

### Custom Consensus Logic
1. Subclass `ConsensusDetector`
2. Override `check_consensus()` method
3. Inject via configuration

### Custom Roles
1. Add role prompt in `RolePrompts`
2. Update role assignment logic
3. Modify iteration flow if needed
