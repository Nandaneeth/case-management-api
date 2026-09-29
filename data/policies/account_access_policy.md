# Account Access Policy

- Policy ID: POL-ACC-002
- Policy name: Customer Account Access and Authorization Standard
- Category: Identity and Access Management
- Version: 4.2
- Effective date: 2026-03-01
- Department: Identity Access Management and Customer Support
- Status: Approved
- Source: Internal Policy Library / Governance and Security

## Purpose
This policy establishes the rules for granting, verifying, and restricting access to customer accounts and support tools. It ensures that only authorized users can access personal data, account controls, and service settings while allowing support teams to resolve legitimate access issues without creating unnecessary risk.

## Scope
This policy applies to customer accounts, administrator roles, delegated user access, onboarding and offboarding, account recovery, and support scenarios involving account-level permissions. It covers access to customer dashboards, internal support tools, and any records associated with an account profile, including payment history, service settings, and case records.

## Procedure
1. Confirm the user’s identity and authority before discussing or changing access permissions.
2. Verify whether the request is for the account owner, a delegated family member, a business administrator, or a support agent handling a third-party case.
3. Check whether the account has any active access restrictions, fraud flags, security challenge states, or prior approval records.
4. If the request is reasonable and validated, grant the lowest level of access needed to complete the task. Avoid broad administrative access unless specifically required for service recovery or troubleshooting.
5. For delegated access requests, validate the relationship, document the scope of authority, and record the approval time and approving contact.
6. For any access change to billing, service configuration, or personal data, confirm the customer’s intent and log the action in the case record.
7. If access is granted temporarily, set a validity window and notify the customer of the expiration terms.
8. When an account is compromised or a suspicious access event is observed, disable or limit access immediately and start an account security review.

## Exceptions
Exceptions may be permitted when:
- a legal representative or authorized person has a verified power of attorney or documented authority to manage the account;
- a customer is unable to complete MFA because of a temporary device issue and the login challenge is safely validated through a secure recovery path;
- a support escalation requires a temporary service access override for a regulated account and is approved by an IAM supervisor.

All exceptions must be time-limited, logged, and reviewed within the next support cycle. Any unapproved exception is treated as a policy breach.

## Escalation guidance
Escalate to the IAM team when:
- a customer asks for access to another person’s account without documented authorization;
- there are signs of credential theft, password spraying, suspicious login automation, or account takeover;
- the account has multiple failed identity checks across different channels;
- a support agent cannot confirm the requestor’s authority with the available evidence.

Escalate to Security Operations for security incidents, suspected fraud, or any scenario where unauthorized access may have occurred. In all escalations, include the account ID, type of access requested, verification steps performed, and action already taken so the next team can continue without repeating the same process.
