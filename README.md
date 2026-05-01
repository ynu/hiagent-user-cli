# Inactive User CLI

CLI tool for detecting and cleaning inactive users in AI Agent platform.

## Installation

```bash
uv sync
```

## Usage

```bash
uv run inactive-user --help
```

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Click Commands                      │   │
│  │  - analyze    - scan    - delete    - list          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              InactiveUserAnalyzer                    │   │
│  │  - Analyzes inactive users                           │   │
│  │  - Computes creator sets from apps                   │   │
│  │  - Identifies users without active agents            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  ListAppAPI  │  │  ListUserAPI │  │ DeleteUserAPI│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                          │                                  │
│              ┌───────────┴───────────┐                     │
│              │      APIClient        │                     │
│              │  - Volcengine SignerV4│                     │
│              │  - Pagination Helper  │                     │
│              │  - Error Handling     │                     │
│              └───────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API                              │
│  - ListApp        - 获取智能体列表及创建人                   │
│  - ListUserForAdmin - 获取平台用户列表                       │
│  - DeleteUser     - 删除指定用户                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| CLI Framework | Click | Command-line interface |
| HTTP Client | requests | API communication |
| Authentication | volcengine SignerV4 | Volcengine signature v4 |
| Configuration | python-dotenv | Environment variable loading |
| Progress Display | rich | Progress bars and tables |
| Logging | Python logging | Operation logging |

### Inactive User Detection Logic

The tool identifies inactive users through a set difference operation:

```
Inactive Users = Platform Users - Agent Creators
```

**Algorithm Flow:**
1. Fetch all agent creators via `ListApp` API
2. Extract `CreateUser` field from each agent
3. Fetch all platform users via `ListUserForAdmin` API
4. Identify users whose ID is not in the creator set
5. Report these users as inactive

**Rationale:** A user who has created at least one agent is considered active, even if they haven't logged in recently. This approach ensures that creators with valuable content are not accidentally removed.

### API Call Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                         Inactive User Analysis                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: ListApp                                                   │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  Request: POST /?Action=ListApp                          │      │
│  │  Pagination: PageNumber=1, PageSize=100 (auto-loop)      │      │
│  │  Response: { Items: [{AppID, CreateUser, ...}, ...] }    │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                     │
│                              ▼                                     │
│  Step 2: ListUserForAdmin                                          │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  Request: POST /?Action=ListUserForAdmin                 │      │
│  │  Pagination: PageNumber=1, PageSize=100 (auto-loop)      │      │
│  │  Response: { Items: [{ID, UserName, ...}, ...] }         │      │
│  └──────────────────────────────────────────────────────────┘      │
│                              │                                     │
│                              ▼                                     │
│  Step 3: Compute Difference                                        │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │  creators = {CreateUser for all apps}                    │      │
│  │  inactive = {user for users if user.ID not in creators}  │      │
│  └──────────────────────────────────────────────────────────┘      │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

### Configuration

The tool reads configuration from environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| API_HOST | 10.10.160.222:30040/ | API endpoint host |
| API_VERSION | 2023-08-01 | API version |
| API_SERVICE | app | Service name for signing |
| API_REGION | cn-north-1 | Region for signing |
| ACCOUNT_ID | 1000000000 | Account ID |
| API_AK | (required) | Access Key |
| API_SK | (required) | Secret Key |
| LOG_DIR | logs | Log directory |
| DEFAULT_PAGE_SIZE | 100 | Default pagination size |

### Security

- All API requests use Volcengine Signature V4 authentication
- Credentials are never logged or exposed
- Delete operations require explicit user confirmation
- All operations are logged for audit purposes

### Logging

Logs are written to `logs/` directory with the following structure:
```
logs/
└── inactive_user_{timestamp}.log
```

Log entries include:
- Timestamp
- Log level (INFO/WARNING/ERROR)
- Operation details
- API responses (sanitized)