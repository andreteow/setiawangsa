// Client-side password gate using SHA-256
// Not secure against source inspection — sufficient for casual access control

// SHA-256 hash of the password "muda2026"
const PASSWORD_HASH = "88dcf054f3dfbd80b9b60e541462a7cbf6b855ba04edefe9145a5ab09279a6bc";

const AUTH_KEY = "setiawangsa_auth";

export async function hashPassword(password) {
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
}

export function isAuthenticated() {
    return sessionStorage.getItem(AUTH_KEY) === "true";
}

export async function authenticate(password) {
    const hash = await hashPassword(password);
    if (hash === PASSWORD_HASH) {
        sessionStorage.setItem(AUTH_KEY, "true");
        return true;
    }
    return false;
}

export function renderLoginScreen(onSuccess) {
    const app = document.getElementById("app");
    app.innerHTML = `
        <div class="login-screen">
            <div class="login-card">
                <div class="login-logo">
                    <h1>P.118 Setiawangsa</h1>
                    <p>Electoral Analytics Dashboard</p>
                </div>
                <form id="login-form">
                    <div class="form-group">
                        <input type="password" id="password-input" placeholder="Enter password" autocomplete="off" autofocus />
                    </div>
                    <button type="submit" class="btn-primary">Access Dashboard</button>
                    <p id="login-error" class="error-text" style="display:none">Incorrect password</p>
                </form>
                <p class="login-footer">MUDA — Internal Use Only</p>
            </div>
        </div>
    `;

    document.getElementById("login-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const pw = document.getElementById("password-input").value;
        const ok = await authenticate(pw);
        if (ok) {
            onSuccess();
        } else {
            const err = document.getElementById("login-error");
            err.style.display = "block";
            document.getElementById("password-input").value = "";
            document.getElementById("password-input").focus();
        }
    });
}
