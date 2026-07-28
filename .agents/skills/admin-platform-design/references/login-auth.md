# Login And Auth

Use this reference for login, registration, password reset, SSO, MFA, and first-run admin access screens.

## Composition

Prefer a focused product login, not a landing page:

- Centered or two-column layout with the form as the primary object.
- Brand/product mark visible in the first viewport.
- Short product descriptor or trust copy, not a marketing hero.
- Optional right-side product preview panel, security illustration, or dashboard glimpse if it supports trust.
- Footer with version, privacy/help links, or tenant info only when useful.

## Form

- Keep form width around 360-420px.
- Include email/account, password, remember me, forgot password, primary submit, and SSO/enterprise login if relevant.
- Use visible labels or highly stable placeholders. Do not rely on placeholder-only inputs for complex enterprise auth.
- Submit button should be full width when the form is narrow.
- Preserve layout during loading; show spinner and disable duplicate submit.
- Error messages should appear near the failed field or as a compact alert above the form.

## Visual Style

- Use a light neutral background with a subtle product accent.
- Avoid dark gradient login screens unless the brand requires them.
- Product preview panels can use a tinted surface, mock dashboard, or real product screenshot.
- Use security/status iconography sparingly: shield, key, lock, organization, user.

## States To Cover

- Invalid credentials.
- Required fields.
- Password visibility toggle.
- Loading submit.
- SSO unavailable or tenant mismatch if the product supports SSO.
- MFA code entry and resend countdown if the product supports MFA.
- Password reset sent and expired link states.

## Copy

- Use direct action labels: "登录", "继续", "发送重置链接", "验证".
- Avoid long onboarding explanations inside the login card.
- For Chinese enterprise products, pair the product name with a short trust line such as "智能 · 高效 · 安全" only if it fits the brand.
