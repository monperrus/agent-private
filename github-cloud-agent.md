# Interacting with the GitHub Cloud Agent (Copilot)

GitHub's cloud agent — **GitHub Copilot coding agent** — can autonomously work on issues and pull requests. Here is how to interact with it effectively.

## Assigning Tasks via Issues

The primary way to trigger the cloud agent is to assign it to an issue.

1. Open or create an issue describing the task clearly.
2. Assign **Copilot** as the assignee (same as a human collaborator).
3. The agent will pick up the issue, create a branch, and open a pull request with its implementation.

For best results, write the issue body with:
- A clear problem statement or goal
- Acceptance criteria or expected behavior
- Relevant file paths or context if known

## Reviewing the Agent's Pull Request

Once the agent opens a PR:
- Review the diff as you would any human PR.
- Leave inline comments to request changes — the agent will read them and push follow-up commits.
- Approve and merge when satisfied.

## Giving Feedback Mid-Work

You can comment on the PR while the agent is still working. It monitors the PR thread and will incorporate feedback into subsequent commits. Be specific: reference file names and line numbers when possible.

## Tips for Better Results

- **Break tasks down**: One issue per atomic task works better than large multi-feature requests.
- **Provide context**: Link related PRs, issues, or documentation in the issue body.
- **Use labels**: Labels like `bug`, `enhancement`, or `good first issue` help the agent understand scope.
- **Check the agent's reasoning**: The agent often leaves comments explaining its approach — read them before reviewing code.

## Limitations

- The agent works best on well-scoped, self-contained tasks.
- It may struggle with tasks requiring access to external systems, secrets, or live data.
- Always review generated code before merging — the agent can make mistakes like any contributor.

## References

- [GitHub Copilot coding agent docs](https://docs.github.com/en/copilot/using-github-copilot/using-copilot-coding-agent-to-work-on-tasks/about-assigning-tasks-to-copilot)
