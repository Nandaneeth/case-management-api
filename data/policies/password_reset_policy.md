# Password Reset Policy

- Policy ID: POL-ACC-001
- Policy name: Customer Password Reset Standard
- Category: Authentication and Access
- Version: 2.4
- Effective date: 2026-01-15
- Department: Customer Support Operations
- Status: Approved
- Source: Internal Policy Library / Identity & Access Management

## Purpose
This policy defines how customer-support teams verify and process password reset requests for customer accounts. The goal is to prevent unauthorized account access while preserving a fast and consistent customer experience for legitimate users. All support interactions involving password recovery must follow the identity checks and logging requirements in this policy.

## Scope
This policy applies to all customer support agents, team leads, escalation specialists, and any staff member handling password reset requests through phone, email, chat, or self-service workflows. It covers user accounts for digital services, customer portals, mobile apps, and partner-facing login tools where the support team is responsible for account assistance.

## Procedure
1. Receive the request and confirm the channel of contact and the account identifier provided by the customer.
2. Verify the customer’s identity using at least two independent factors, such as:
   - registered email address or username;
   - phone number associated with the account;
   - customer account number or subscription ID;
   - one-time verification code sent to the customer’s secure contact method;
   - a knowledge-based challenge only when permitted by the risk policy and recorded in the case notes.
3. If the customer is unable to complete the verification steps, do not disclose account details or reset the password. Offer a secure alternative such as a one-time code to the registered contact method or a callback to the verified phone number.
4. Before performing a reset, review the account for signs of fraud or recent suspicious events such as multiple failed login attempts, login from a new device, or multiple password reset requests within a short period.
5. Complete the reset via the approved identity workflow. Use a temporary password or secure link that is valid for a single user session and requires password change on next login.
6. Confirm with the customer that the reset is complete, provide the required next steps, and remind them to enable MFA or device recovery options if available.
7. Record the case ID, verification factors used, date and time of the reset, agent name, and any follow-up recommendation in the case management system.
8. Where the account is a high-risk customer record or tied to a regulated service, notify the security or compliance contact per the escalation guidance below.

## Exceptions
Exceptions to standard verification are allowed only when approved by the Identity & Access Management team or the Security Operations lead. Examples include:
- customers with a verified government-issued ID on file and a documented account takeover investigation;
- accounts impacted by a service outage that blocks the customer from accessing a recovery channel;
- legacy accounts that cannot complete MFA but have a prior validated support case and documented manual review.

Any exception must be documented in writing, time-stamped, and approved before the reset is completed. Unsupported deviations are considered policy violations.

## Escalation guidance
Escalate to the IAM or Security Operations team when:
- the customer cannot satisfy identity verification requirements;
- the account shows signs of compromise, phishing, or unauthorized access;
- multiple reset attempts are made from different devices or geographies;
- the customer requests access to an account they do not control or claims to be acting on behalf of another person without proper authorization.

Escalate to the Support Team Lead when a reset cannot be completed because of system issues, incomplete account data, or a support workflow conflict. All escalations must include the account identifiers, verification steps attempted, and the exact reason the policy could not be applied without deviation.
