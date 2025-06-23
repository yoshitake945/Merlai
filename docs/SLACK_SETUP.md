# Slack Webhook Setup for CI/CD

This document explains how to set up Slack notifications for the Merlai CI/CD pipeline.

## Prerequisites

- Admin access to your Slack workspace
- Admin access to the GitHub repository

## Setup Steps

### 1. Create Slack App and Webhook

1. Go to [Slack API Apps page](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Enter app name (e.g., "Merlai CI Notifications") and select your workspace
4. In the left sidebar, go to "Incoming Webhooks"
5. Toggle "Activate Incoming Webhooks" to On
6. Click "Add New Webhook to Workspace"
7. Select the channel where you want to receive notifications (e.g., `#merlai-ci`)
8. Click "Allow"
9. Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

### 2. Add Webhook URL to GitHub Secrets

1. Go to your GitHub repository
2. Click "Settings" tab
3. In the left sidebar, click "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Name: `SLACK_WEBHOOK_URL`
6. Value: Paste the webhook URL from step 1
7. Click "Add secret"

### 3. Configure Channel (Optional)

The default channel is set to `#merlai-ci`. To change this:

1. Edit `.github/workflows/ci.yml`
2. Find the `channel: '#merlai-ci'` line in both notification steps
3. Replace with your desired channel name

## Notification Details

The pipeline will send notifications for:

- **Success**: When all CI checks pass
- **Failure**: When any CI check fails, including a link to the workflow run

## Message Format

### Success Message
```
✅ **Merlai CI Pipeline Succeeded**
• Repository: yoshitake945/Merlai
• Branch: feature/ci-setup
• Commit: abc123...
• Triggered by: username
• Workflow: CI
```

### Failure Message
```
❌ **Merlai CI Pipeline Failed**
• Repository: yoshitake945/Merlai
• Branch: feature/ci-setup
• Commit: abc123...
• Triggered by: username
• Workflow: CI
• [View Details](https://github.com/yoshitake945/Merlai/actions/runs/123456)
```

## Troubleshooting

### Notifications not appearing
1. Check that the webhook URL is correctly set in GitHub secrets
2. Verify the channel name exists in your Slack workspace
3. Ensure the Slack app has permission to post to the channel

### Webhook URL security
- Never commit the webhook URL directly to the repository
- Always use GitHub secrets for sensitive URLs
- Rotate webhook URLs periodically for security

## Testing

To test the Slack notifications:

1. Make a small change to trigger the CI pipeline
2. Push the changes to trigger the workflow
3. Check your Slack channel for notifications

The notifications will be sent after the build job completes, regardless of success or failure. 