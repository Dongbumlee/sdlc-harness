# Security Policy

## Supported versions

Only the latest release of this project receives security fixes.
Older releases are not patched — upgrade to the latest release
first when a report concerns an older version.

## Reporting a vulnerability

Report vulnerabilities privately through GitHub's private
vulnerability reporting: open the repository's **Security** tab
and choose **Report a vulnerability**. Never open a public issue
for a security problem, and never post credentials or exploit
details in a public thread.

Expect an acknowledgement within 3 business days and a status
update at least every 7 days until the report is resolved.
Accepted fixes ship in the next release; reporters are credited
in the release notes unless they ask to stay anonymous.

## Handling secrets

Secrets never enter this repository. Configuration arrives
through environment variables or the organization's secret
manager, and `.env.example` carries names and dummy values only.
A committed secret is treated as compromised: rotate it first,
then remove it from history.
