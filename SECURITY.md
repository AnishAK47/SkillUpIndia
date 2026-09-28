# Security policy

SkillUpIndia is a prototype built for the Smart India Hackathon (problem statement SIH26134). We take reports about the security of the app and the people who use it seriously.

## Reporting a vulnerability

**Please report vulnerabilities privately, not in public issues or through the in-app Feedback page** (feedback can be posted publicly as GitHub issues).

Use GitHub's private reporting: open the repository's **Security** tab and click **Report a vulnerability**, or go directly to <https://github.com/AnishAK47/SkillUpIndia/security/advisories/new>.

Please include:

- what the issue is and where it is (page, URL, or file and line),
- steps to reproduce it, using test accounts you own,
- what an attacker could do with it, and
- any suggested fix.

We aim to acknowledge reports within **3 days** and to share a plan for a fix within **14 days**. This is a small student team, so complex issues may take longer; we'll keep you updated either way. With your permission, we'll credit you when the fix is published.

## Supported versions

Only the latest code on the `main` branch and the live deployment at <https://skillupindia.streamlit.app> are supported. Fixes are not backported.

## Scope

**In scope**

- Signing in as someone else, or bypassing sign-in on pages that require it.
- Reaching admin-only pages or data (Data ingestion, Curriculum upload, the feedback inbox, other members' profiles) without a verified admin account.
- Reading or changing another member's profiles, progress, or feedback.
- Exposure of secrets, such as the Auth0 client secret, cookie secret, Supabase secret key, or GitHub token.
- Injection or script execution through uploaded PDFs, CSV files, or text fields.

**Out of scope**

- Issues in Streamlit Community Cloud, Auth0, Supabase, Google, or GitHub themselves. Please report those to the provider.
- Security headers, cookies, or redirects controlled by the `streamlit.app` hosting platform.
- Denial-of-service or load testing, and spam that the feedback form's per-session limit already addresses.
- Social engineering, phishing, or physical attacks.
- Accuracy of the demonstration data or of skill and gap scores (please use the Feedback page for these).

## Safe harbor

We won't pursue action against good-faith research that follows this policy. Please:

- use only accounts and data you own, and stop as soon as you've confirmed an issue that exposes someone else's data;
- avoid automated scanning or high request volumes against the live app;
- give us a reasonable chance to fix the issue before sharing it publicly.

## How the app protects data

- **Sign-in** is handled by Auth0 through Streamlit's `st.login` (OpenID Connect). The app never sees or stores passwords, and the identity cookie is signed.
- **Admin access** requires an email on the allowlist in the app's secrets *and* a verified email address, so an unverified sign-up using someone else's address can't become an admin.
- **Ownership:** profiles are tied to the sign-in provider's account ID, not the email address. Members can only list their own profiles.
- **Admin-only pages** are registered only for admins, so other visitors can't open them by URL.
- **Database:** Supabase tables have row-level security enabled with no policies, so the public key can't read or write them. The app uses a server-side secret key that lives only in Streamlit secrets.
- **Uploads:** resumes, syllabi, and job files are processed in memory and not stored.
- **Feedback:** the reporter's email is stored in the database only, never in a public GitHub issue.
- **Secrets** are kept in Streamlit secrets. `.streamlit/secrets.toml` and `.env` are git-ignored.

## For contributors

- Never commit real secrets. Use [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) as the template.
- If a secret is ever committed or shared, **rotate it immediately**. Deleting the commit isn't enough, because it stays in git history and forks. The relevant places are Auth0 (client secret), Supabase (secret key), the `cookie_secret`, and GitHub (token).
- Run `python -m pytest tests` before pushing; the tests cover the visitor, member, and admin access rules.
