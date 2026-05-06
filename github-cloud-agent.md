# GitHub Cloud Agent — API Endpoints

Reference for interacting with the GitHub Copilot cloud agent (formerly "Copilot coding agent") via API.
All curl examples include `Authorization`, `Accept`, and `X-GitHub-Api-Version: 2026-03-10` headers.

---

## Official Documented Endpoints

### Enterprise policy management

All require `manage_billing:copilot` or `admin:enterprise` scope on a classic PAT.
**These do not work with GitHub Apps or fine-grained PATs.**

**Set enterprise-wide CCA policy:**

```bash
curl -X PUT \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/enterprises/ENTERPRISE/copilot/policies/coding_agent \
  -d '{"policy_state": "enabled_for_all_orgs"}'
  # policy_state options: enabled_for_all_orgs | disabled_for_all_orgs
  #                       decided_by_org | enabled_for_selected_orgs
```

**Enable CCA for specific orgs (or by custom property):**

```bash
curl -X POST \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/enterprises/ENTERPRISE/copilot/policies/coding_agent/organizations \
  -d '{
    "organizations": ["my-org-1"],
    "custom_properties": [{"property_name": "department", "values": ["engineering"]}]
  }'
```

**Disable CCA for specific orgs:** same endpoint with `DELETE`.

**Org-level: get repository permissions:**

```bash
curl \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/orgs/ORG/copilot/coding-agent/permissions
```

**Org-level: list enabled repositories:**

```bash
curl \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/orgs/ORG/copilot/coding-agent/permissions/repositories
```

> ⚠️ These org-level repository endpoints are in **public preview** and subject to change.

---

### Custom agents management (Enterprise)

Requires `admin:enterprise` scope.

**List custom agents defined in `.github-private`:**

```bash
curl \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/enterprises/ENTERPRISE/copilot/custom-agents
```

**Set source org for custom agent definitions:**

```bash
curl -X PUT \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/enterprises/ENTERPRISE/copilot/custom-agents/source \
  -d '{"organization_id": 123, "create_ruleset": true}'
```

**Remove custom agents source:**

```bash
curl -X DELETE \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/enterprises/ENTERPRISE/copilot/custom-agents/source
```

---

## Undocumented / Community-Discovered Behavior

These are not in the official API reference but have been validated through community experimentation.

### Triggering the agent: assign an issue (REST)

The primary way to programmatically start the cloud agent is to create or update an issue with `copilot-swe-agent[bot]` as an assignee and include an `agent_assignment` block.

> ⚠️ The `agent_assignment` field is **not in the official issues API schema** — it is community-discovered. See the undocumented fields table below.

**Create an issue and trigger the agent in one call:**

```bash
curl -X POST \
  -H "Authorization: Bearer <PAT>" \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  https://api.github.com/repos/OWNER/REPO/issues \
  -d '{
    "title": "Fix the login bug",
    "body": "The login form fails on Safari. Please investigate and fix.",
    "assignees": ["copilot-swe-agent[bot]"],
    "agent_assignment": {
      "target_repo": "OWNER/REPO",
      "base_branch": "main",
      "custom_instructions": "",
      "custom_agent": "",
      "model": ""
    }
  }'
```

**Assign the agent to an existing issue:**

```bash
gh issue edit <NUMBER> --add-assignee copilot-swe-agent
```

### Triggering the agent: GraphQL mutations

Announced December 2025, GitHub added GraphQL support for agent assignment with more control than REST.

```graphql
mutation {
  assignCopilotToIssue(input: {
    issueId: "I_xxx"
    repositoryId: "R_xxx"
    baseBranch: "main"
    customInstructions: "Follow the existing code style."
    customAgent: ""
    model: ""
  }) {
    issue { number url }
  }
}
```

Ref: https://github.blog/changelog/2025-12-03-assign-issues-to-copilot-using-the-api/

### The `agent_assignment` fields

The `agent_assignment` JSON field in `POST /repos/{owner}/{repo}/issues` is not listed in the standard issues API schema. Known fields:

| Field | Description |
|---|---|
| `target_repo` | Repo where the branch/PR will be created (`OWNER/REPO`) |
| `base_branch` | Branch to base work on (e.g. `main`) |
| `custom_instructions` | Extra instructions injected into the agent's context |
| `custom_agent` | Name of a custom agent to use instead of the default |
| `model` | Model override (leave empty for default) |

### Assignee handle quirks

Using `copilot` or `Copilot` as the assignee returns HTTP 422. The correct handle depends on context:
- REST API: `copilot-swe-agent[bot]`
- `gh` CLI: `copilot-swe-agent` (without `[bot]`)

### Authentication requirements

The `GITHUB_TOKEN` from GitHub Actions **cannot** assign the cloud agent — it returns HTTP 422. A **classic PAT** with `repo` scope is required. Fine-grained PATs with issues+PR read/write are insufficient for triggering the agent; they may assign it but the agent then errors with a billing/token mismatch.

### GraphQL: discovering the suggested assignee

Before assigning via GraphQL, you can query who the suggested actor is (the bot):

```graphql
query {
  repository(owner: "OWNER", name: "REPO") {
    suggestedActors(capabilities: [CAN_BE_ASSIGNED]) {
      nodes { login }
    }
  }
}
```

---

## References

- [Official REST docs for CCA management](https://docs.github.com/en/rest/copilot/copilot-coding-agent-management)
- [Assign issues via API — changelog](https://github.blog/changelog/2025-12-03-assign-issues-to-copilot-using-the-api/)
- [Community discussion: triggering via REST](https://github.com/orgs/community/discussions/164267)
- [Community discussion: workflow triggering](https://github.com/orgs/community/discussions/186820)
- [About Copilot cloud agent](https://docs.github.com/copilot/concepts/agents/coding-agent/about-coding-agent)
