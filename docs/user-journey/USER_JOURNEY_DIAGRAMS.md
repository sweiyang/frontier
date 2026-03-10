# Conduit User Journey Diagrams
## Visual Flowcharts for Presentations

This document contains Mermaid diagrams that can be rendered in presentations, documentation sites, or exported as images.

---

## Journey 1: End User - Daily Chat Experience

### Complete Flow Diagram

```mermaid
graph TB
    Start([User Opens Conduit]) --> Auth{Authenticated?}

    Auth -->|No| Login[Login Page]
    Login --> EnterCreds[Enter Credentials]
    EnterCreds --> LDAP{LDAP Enabled?}
    LDAP -->|Yes| LDAPAuth[Authenticate via LDAP]
    LDAP -->|No| LocalAuth[Local Authentication]
    LDAPAuth --> TokenGen[Generate JWT Token]
    LocalAuth --> TokenGen
    TokenGen --> Dashboard

    Auth -->|Yes| Dashboard[Project Dashboard]

    Dashboard --> ProjectList[View Project List]
    ProjectList --> SearchProj{Search/Filter?}
    SearchProj -->|Yes| FilterProj[Filter Projects]
    SearchProj -->|No| SelectProj[Select Project]
    FilterProj --> SelectProj

    SelectProj --> LoadConv[Load Conversations]
    LoadConv --> ConvChoice{New or Existing?}

    ConvChoice -->|Existing| ClickConv[Click Conversation]
    ClickConv --> LoadHistory[Load Message History]

    ConvChoice -->|New| NewConv[Create New Conversation]
    NewConv --> ChatArea[Empty Chat Area]

    LoadHistory --> ChatArea

    ChatArea --> TypeMsg[Type Message]
    TypeMsg --> AddFiles{Add Files?}
    AddFiles -->|Yes| UploadFiles[Upload Files]
    AddFiles -->|No| SendMsg[Send Message]
    UploadFiles --> SendMsg

    SendMsg --> AgentSelect{Agent Selected?}
    AgentSelect -->|No| DefaultAgent[Use Default Agent]
    AgentSelect -->|Yes| SelectedAgent[Use Selected Agent]
    DefaultAgent --> StreamStart
    SelectedAgent --> StreamStart

    StreamStart[Start Streaming] --> WaitToken[Wait for First Token]
    WaitToken --> FirstToken{Token Received?}
    FirstToken -->|Timeout| Error[Show Error]
    FirstToken -->|Success| StreamTokens[Stream Response Tokens]

    Error --> Retry{Retry?}
    Retry -->|Yes| SendMsg
    Retry -->|No| End([End Session])

    StreamTokens --> Complete[Response Complete]
    Complete --> UserAction{User Action?}

    UserAction -->|Follow-up| TypeMsg
    UserAction -->|Switch Conversation| LoadConv
    UserAction -->|Switch Project| ProjectList
    UserAction -->|Logout| End

    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#F44336,stroke:#C62828,color:#fff
    style Error fill:#FF9800,stroke:#F57C00,color:#fff
    style StreamTokens fill:#2196F3,stroke:#1565C0,color:#fff
    style Complete fill:#4CAF50,stroke:#2E7D32,color:#fff
```

### Emotional Journey Timeline

```mermaid
journey
    title End User Daily Chat Experience
    section Discovery
      Click invitation link: 3: User
      View login page: 3: User
      Read value proposition: 4: User
    section Authentication
      Enter credentials: 2: User
      Wait for LDAP: 2: User
      Login successful: 5: User
    section Project Selection
      View project list: 3: User
      Search for project: 2: User
      Select project: 4: User
    section Conversation
      View conversation list: 5: User
      Load message history: 5: User
      Review context: 5: User
    section Messaging
      Type question: 5: User
      Send message: 5: User
      Wait for response: 2: User
      Receive streaming: 5: User
      Read answer: 5: User
    section Follow-up
      Continue or switch: 4: User
```

### Pain Points Heatmap

```mermaid
graph LR
    subgraph "🔴 Critical Pain Points"
        P1[Slow Response<br/>3-5 seconds]
        P2[LDAP Failures<br/>Generic Errors]
        P3[No Search<br/>Hard to Find]
    end

    subgraph "🟡 Important Pain Points"
        P4[No Bulk Operations<br/>Manual Work]
        P5[No Cost Visibility<br/>Budget Concerns]
        P6[Complex Config<br/>Technical Barrier]
    end

    subgraph "🟢 Monitor"
        P7[Slow Loading<br/>Large Conversations]
        P8[No Export<br/>Limited Sharing]
    end

    style P1 fill:#F44336,stroke:#C62828,color:#fff
    style P2 fill:#F44336,stroke:#C62828,color:#fff
    style P3 fill:#F44336,stroke:#C62828,color:#fff
    style P4 fill:#FF9800,stroke:#F57C00,color:#fff
    style P5 fill:#FF9800,stroke:#F57C00,color:#fff
    style P6 fill:#FF9800,stroke:#F57C00,color:#fff
    style P7 fill:#4CAF50,stroke:#2E7D32,color:#fff
    style P8 fill:#4CAF50,stroke:#2E7D32,color:#fff
```

---

## Journey 2: Project Admin - Setup & Configuration

### Project Setup Flow

```mermaid
graph TB
    Start([Admin Dashboard]) --> CreateProj[Click Create Project]
    CreateProj --> ProjForm[Enter Project Details]
    ProjForm --> ValidateName{Name Valid?}
    ValidateName -->|No| ShowError[Show Validation Error]
    ShowError --> ProjForm
    ValidateName -->|Yes| SubmitProj[Submit Project]

    SubmitProj --> CreateTables[Create Database Tables]
    CreateTables --> ProjCreated[Project Created]

    ProjCreated --> ConfigAgent[Configure Agent]
    ConfigAgent --> SelectType{Agent Type?}

    SelectType -->|OpenAI| OpenAIForm[OpenAI Configuration]
    SelectType -->|LangGraph| LangGraphForm[LangGraph Configuration]
    SelectType -->|HTTP| HTTPForm[HTTP Configuration]

    OpenAIForm --> EnterCreds[Enter API Credentials]
    LangGraphForm --> EnterCreds
    HTTPForm --> EnterCreds

    EnterCreds --> TestConn[Test Connection]
    TestConn --> TestResult{Test Success?}

    TestResult -->|No| ShowTestError[Show Error Details]
    ShowTestError --> EnterCreds
    TestResult -->|Yes| SaveAgent[Save Agent Config]

    SaveAgent --> SetDefault[Set as Default Agent]
    SetDefault --> AddMembers[Add Team Members]

    AddMembers --> MemberMethod{Add Method?}
    MemberMethod -->|Individual| AddOne[Add One Member]
    MemberMethod -->|Bulk| BulkImport[Import CSV]
    MemberMethod -->|AD Group| ADGroup[Link AD Group]

    AddOne --> AssignRole[Assign Role]
    BulkImport --> AssignRole
    ADGroup --> AssignRole

    AssignRole --> MoreMembers{More Members?}
    MoreMembers -->|Yes| AddMembers
    MoreMembers -->|No| SendInvites[Send Invitations]

    SendInvites --> SetupComplete[Setup Complete]
    SetupComplete --> Monitor[Monitor Usage]

    Monitor --> End([Project Active])

    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style SetupComplete fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#2196F3,stroke:#1565C0,color:#fff
    style ShowError fill:#FF9800,stroke:#F57C00,color:#fff
    style ShowTestError fill:#FF9800,stroke:#F57C00,color:#fff
```

### Time Investment Breakdown

```mermaid
pie title Project Setup Time Distribution (Current)
    "Project Creation" : 10
    "Agent Configuration" : 30
    "Agent Testing" : 15
    "Team Member Addition" : 40
    "Documentation" : 5
```

```mermaid
pie title Project Setup Time Distribution (Target)
    "Project Creation" : 15
    "Agent Configuration" : 30
    "Agent Testing" : 15
    "Team Member Addition" : 30
    "Documentation" : 10
```

### Admin Journey Emotional Arc

```mermaid
journey
    title Project Admin Setup Experience
    section Project Creation
      Click create project: 5: Admin
      Enter project details: 5: Admin
      Submit form: 5: Admin
    section Agent Configuration
      Select agent type: 4: Admin
      Find API credentials: 2: Admin
      Enter configuration: 3: Admin
      Test connection: 2: Admin
      Connection successful: 5: Admin
    section Team Onboarding
      Add first member: 4: Admin
      Add second member: 3: Admin
      Add remaining members: 2: Admin
      Send invitations: 4: Admin
    section Monitoring
      View usage metrics: 5: Admin
      Check token usage: 3: Admin
      Calculate costs: 3: Admin
```

---

## Journey 3: Platform Admin - Deployment

### Deployment Flow

```mermaid
graph TB
    Start([Clone Repository]) --> InstallDeps[Install Dependencies]
    InstallDeps --> DepCheck{Dependencies OK?}
    DepCheck -->|No| FixDeps[Fix Dependency Issues]
    FixDeps --> InstallDeps
    DepCheck -->|Yes| CreateConfig[Create config.yaml]

    CreateConfig --> ConfigDB{Database Type?}
    ConfigDB -->|SQLite| DefaultDB[Use Default SQLite]
    ConfigDB -->|PostgreSQL| SetupPG[Setup PostgreSQL]

    SetupPG --> CreateDB[Create Database]
    CreateDB --> AddConnStr[Add Connection String]
    AddConnStr --> ConfigLDAP

    DefaultDB --> ConfigLDAP{Enable LDAP?}
    ConfigLDAP -->|Yes| LDAPSettings[Configure LDAP Settings]
    ConfigLDAP -->|No| ConfigCORS

    LDAPSettings --> ConfigCORS[Configure CORS Origins]
    ConfigCORS --> BuildFE[Build Frontend]

    BuildFE --> FEBuild{Build Success?}
    FEBuild -->|No| FixFE[Fix Build Errors]
    FixFE --> BuildFE
    FEBuild -->|Yes| StartServer[Start Server]

    StartServer --> ServerStart{Server Started?}
    ServerStart -->|No| CheckLogs[Check Error Logs]
    CheckLogs --> FixConfig[Fix Configuration]
    FixConfig --> StartServer

    ServerStart -->|Yes| HealthCheck[Check /health Endpoint]
    HealthCheck --> HealthOK{Health OK?}
    HealthOK -->|No| CheckLogs
    HealthOK -->|Yes| TestAuth[Test Authentication]

    TestAuth --> AuthType{Auth Type?}
    AuthType -->|LDAP| TestLDAP[Test LDAP Login]
    AuthType -->|Local| TestLocal[Test Local Login]

    TestLDAP --> LDAPResult{LDAP Works?}
    LDAPResult -->|No| DebugLDAP[Debug LDAP Config]
    DebugLDAP --> LDAPSettings
    LDAPResult -->|Yes| SetupMonitor

    TestLocal --> SetupMonitor[Setup Monitoring]

    SetupMonitor --> AddProm[Add Prometheus Scrape]
    AddProm --> CreateDash[Create Grafana Dashboard]
    CreateDash --> SetAlerts[Configure Alerts]

    SetAlerts --> CreateProjects[Create Initial Projects]
    CreateProjects --> InviteUsers[Invite Pilot Users]
    InviteUsers --> DeployComplete[Deployment Complete]

    DeployComplete --> Monitor[Monitor Adoption]
    Monitor --> End([Production Ready])

    style Start fill:#4CAF50,stroke:#2E7D32,color:#fff
    style DeployComplete fill:#4CAF50,stroke:#2E7D32,color:#fff
    style End fill:#2196F3,stroke:#1565C0,color:#fff
    style FixDeps fill:#FF9800,stroke:#F57C00,color:#fff
    style FixFE fill:#FF9800,stroke:#F57C00,color:#fff
    style CheckLogs fill:#FF9800,stroke:#F57C00,color:#fff
    style DebugLDAP fill:#F44336,stroke:#C62828,color:#fff
```

### Deployment Success Funnel

```mermaid
graph LR
    A[100 Attempts] -->|90%| B[90 Installed]
    B -->|67%| C[60 Configured]
    C -->|75%| D[45 LDAP Working]
    D -->|94%| E[42 Monitoring Setup]
    E -->|100%| F[42 Production Ready]

    style A fill:#2196F3,stroke:#1565C0,color:#fff
    style B fill:#4CAF50,stroke:#2E7D32,color:#fff
    style C fill:#FF9800,stroke:#F57C00,color:#fff
    style D fill:#F44336,stroke:#C62828,color:#fff
    style E fill:#4CAF50,stroke:#2E7D32,color:#fff
    style F fill:#4CAF50,stroke:#2E7D32,color:#fff
```

---

## Cross-Journey Insights

### Pain Point Impact Matrix

```mermaid
quadrantChart
    title Pain Point Prioritization Matrix
    x-axis Low Impact --> High Impact
    y-axis Low Frequency --> High Frequency
    quadrant-1 Important
    quadrant-2 Urgent
    quadrant-3 Monitor
    quadrant-4 Backlog
    Slow Response: [0.85, 0.95]
    LDAP Failures: [0.90, 0.60]
    Generic Errors: [0.70, 0.85]
    No Search: [0.75, 0.80]
    No Bulk Ops: [0.65, 0.75]
    No Costs: [0.60, 0.70]
    Complex Config: [0.70, 0.65]
    Port Conflicts: [0.40, 0.30]
    Lost Drafts: [0.45, 0.35]
    No Mobile: [0.50, 0.25]
```

### Opportunity Roadmap Timeline

```mermaid
gantt
    title Opportunity Implementation Roadmap
    dateFormat YYYY-MM-DD
    section Quick Wins
    Better Error Messages           :done, qw1, 2026-03-10, 1w
    Test Connection Button          :done, qw2, 2026-03-17, 3d
    Cost Calculator                 :active, qw3, 2026-03-20, 1w
    Config Validation               :qw4, 2026-03-27, 3d
    Loading Indicators              :qw5, 2026-03-30, 1w

    section Medium-Term
    Comprehensive Search            :mt1, 2026-04-06, 3w
    Bulk Member Import              :mt2, 2026-04-27, 2w
    Project Setup Wizard            :mt3, 2026-05-11, 3w
    LDAP Test Command               :mt4, 2026-06-01, 2w
    Usage Alerts                    :mt5, 2026-06-15, 2w

    section Long-Term
    Optimize First Token            :lt1, 2026-06-29, 6w
    Admin Analytics Dashboard       :lt2, 2026-08-10, 8w
    Conversation Export             :lt3, 2026-10-05, 4w
    Mobile Responsive Design        :lt4, 2026-11-02, 8w
```

### User Satisfaction Trend (Projected)

```mermaid
xychart-beta
    title "Projected User Satisfaction Over Time"
    x-axis [Q1, Q2, Q3, Q4]
    y-axis "Satisfaction Score" 0 --> 100
    line [60, 70, 82, 90]
    line [55, 65, 75, 85]
    line [50, 60, 70, 80]
```

---

## Metrics Dashboard Visualizations

### Current vs Target Performance

```mermaid
graph LR
    subgraph "Response Time"
        A1[Current: 3-5s] -->|Target| A2[<1s]
    end

    subgraph "Login Success"
        B1[Current: 85%] -->|Target| B2[95%]
    end

    subgraph "Setup Time"
        C1[Current: 18min] -->|Target| C2[6min]
    end

    subgraph "LDAP Success"
        D1[Current: 45%] -->|Target| D2[90%]
    end

    style A1 fill:#F44336,stroke:#C62828,color:#fff
    style A2 fill:#4CAF50,stroke:#2E7D32,color:#fff
    style B1 fill:#FF9800,stroke:#F57C00,color:#fff
    style B2 fill:#4CAF50,stroke:#2E7D32,color:#fff
    style C1 fill:#F44336,stroke:#C62828,color:#fff
    style C2 fill:#4CAF50,stroke:#2E7D32,color:#fff
    style D1 fill:#F44336,stroke:#C62828,color:#fff
    style D2 fill:#4CAF50,stroke:#2E7D32,color:#fff
```

### Feature Adoption Funnel

```mermaid
graph TB
    U1[1000 Users] --> U2[850 Active Daily]
    U2 --> U3[680 Using Projects]
    U3 --> U4[510 Multiple Conversations]
    U4 --> U5[340 Power Users]

    U1 -.->|85%| U2
    U2 -.->|80%| U3
    U3 -.->|75%| U4
    U4 -.->|67%| U5

    style U1 fill:#2196F3,stroke:#1565C0,color:#fff
    style U2 fill:#4CAF50,stroke:#2E7D32,color:#fff
    style U3 fill:#4CAF50,stroke:#2E7D32,color:#fff
    style U4 fill:#FF9800,stroke:#F57C00,color:#fff
    style U5 fill:#F44336,stroke:#C62828,color:#fff
```

---

## How to Use These Diagrams

### In Presentations

1. **Copy the Mermaid code** from this document
2. **Paste into presentation tools** that support Mermaid:
   - Marp (Markdown Presentations)
   - Slidev
   - reveal.js with Mermaid plugin
   - Google Slides (via Mermaid extension)

### Export as Images

1. **Use Mermaid Live Editor**: https://mermaid.live/
2. **Paste diagram code** and export as PNG/SVG
3. **Insert images** into PowerPoint, Keynote, or Google Slides

### In Documentation

1. **GitHub/GitLab**: Automatically renders Mermaid in Markdown
2. **Confluence**: Use Mermaid macro
3. **Notion**: Use Mermaid embed block

### Customization

- **Colors**: Modify `style` statements to match brand colors
- **Layout**: Adjust `graph TB` (top-bottom) to `LR` (left-right)
- **Details**: Add/remove nodes based on audience technical level

---

**Document Version**: 1.0
**Last Updated**: March 2026
**Mermaid Version**: 10.x compatible
