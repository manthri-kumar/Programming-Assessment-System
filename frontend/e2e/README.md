# Browser verification

Playwright projects cover desktop, tablet, and mobile viewports. Tests must use clearly labeled UI fixtures or a local FastAPI database. Mocked browser tests are presentation evidence only and must never be reported as real student-code execution evidence.

`E2E_API_URL` and `VITE_API_PROXY_TARGET` may point the suite and Vite proxy at the same disposable local backend port. `E2E_WEB_PORT` and `VITE_DEV_PORT` may likewise select the same disposable frontend port. This avoids reusing or interrupting developer processes. API values default to `http://127.0.0.1:8000`; web ports default to `5173`.

Set `E2E_TEACHER_REGISTRATION_CODE` to the same disposable value supplied to the backend as `ASSESSMENT_TEACHER_REGISTRATION_CODE`. The suite has no embedded invitation-code fallback and never prints the value.
