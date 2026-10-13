// ==========================================================================
// COMPETITOR ANALYSIS AI AGENT - AUTHENTICATION CLIENT JS
// Handles Login, Registration, 1-Click Demo Access, & Session Redirects
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    const tabLoginBtn = document.getElementById("tabLoginBtn");
    const tabSignupBtn = document.getElementById("tabSignupBtn");
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");
    
    const authAlert = document.getElementById("authAlert");
    const authAlertText = document.getElementById("authAlertText");
    const authAlertIcon = document.getElementById("authAlertIcon");

    const quickDemoBtn = document.getElementById("quickDemoBtn");
    const loginSubmitBtn = document.getElementById("loginSubmitBtn");
    const loginSpinner = document.getElementById("loginSpinner");
    const signupSubmitBtn = document.getElementById("signupSubmitBtn");
    const signupSpinner = document.getElementById("signupSpinner");

    // Check if user is ALREADY authenticated; if so, send to dashboard immediately
    fetch("/api/auth/me", { credentials: "include" })
        .then(res => res.json())
        .then(data => {
            if (data.authenticated) {
                window.location.replace("/dashboard");
            }
        })
        .catch(() => {
            // Unauthenticated - stay on login page
        });

    // ----------------------------------------------------------------------
    // Tab Switching
    // ----------------------------------------------------------------------
    tabLoginBtn.addEventListener("click", () => {
        tabLoginBtn.classList.add("active");
        tabSignupBtn.classList.remove("active");
        loginForm.style.display = "block";
        signupForm.style.display = "none";
        hideAlert();
    });

    tabSignupBtn.addEventListener("click", () => {
        tabSignupBtn.classList.add("active");
        tabLoginBtn.classList.remove("active");
        loginForm.style.display = "none";
        signupForm.style.display = "block";
        hideAlert();
    });

    // ----------------------------------------------------------------------
    // Password Visibility Toggles
    // ----------------------------------------------------------------------
    document.querySelectorAll(".toggle-pwd-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const targetId = btn.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (!input) return;

            if (input.type === "password") {
                input.type = "text";
                btn.style.opacity = "1";
            } else {
                input.type = "password";
                btn.style.opacity = "0.6";
            }
        });
    });

    // ----------------------------------------------------------------------
    // Alert Notification Helpers
    // ----------------------------------------------------------------------
    function showAlert(type, message) {
        authAlert.className = `auth-alert ${type}`;
        authAlertText.textContent = message;
        authAlert.style.display = "flex";
    }

    function hideAlert() {
        authAlert.style.display = "none";
    }

    // ----------------------------------------------------------------------
    // 1-Click Fast Track Demo Login
    // ----------------------------------------------------------------------
    quickDemoBtn.addEventListener("click", async () => {
        document.getElementById("loginEmail").value = "demo@competitor.ai";
        document.getElementById("loginPassword").value = "password123";
        await submitLogin("demo@competitor.ai", "password123");
    });

    // ----------------------------------------------------------------------
    // Login Submission
    // ----------------------------------------------------------------------
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;
        await submitLogin(email, password);
    });

    async function submitLogin(email, password) {
        hideAlert();
        loginSubmitBtn.disabled = true;
        loginSpinner.style.display = "inline-block";

        try {
            const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Authentication failed. Check your credentials.");
            }

            // Save user in localStorage as fast fallback
            localStorage.setItem("ca_user", JSON.stringify(data.user));
            localStorage.setItem("ca_token", data.token);

            showAlert("success", `Authenticated as ${data.user.full_name}. Entering dashboard...`);
            
            setTimeout(() => {
                window.location.replace("/dashboard");
            }, 600);

        } catch (err) {
            showAlert("error", err.message || "Failed to log in. Please try again.");
            loginSubmitBtn.disabled = false;
            loginSpinner.style.display = "none";
        }
    }

    // ----------------------------------------------------------------------
    // Signup Submission
    // ----------------------------------------------------------------------
    signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideAlert();

        const fullName = document.getElementById("signupFullName").value.trim();
        const company = document.getElementById("signupCompany").value.trim();
        const email = document.getElementById("signupEmail").value.trim();
        const password = document.getElementById("signupPassword").value;
        const confirmPassword = document.getElementById("signupConfirmPassword").value;

        if (password !== confirmPassword) {
            showAlert("error", "Passwords do not match. Please re-enter.");
            return;
        }

        if (password.length < 6) {
            showAlert("error", "Password must be at least 6 characters in length.");
            return;
        }

        signupSubmitBtn.disabled = true;
        signupSpinner.style.display = "inline-block";

        try {
            const res = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({
                    email,
                    password,
                    full_name: fullName,
                    company
                })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Account creation failed.");
            }

            localStorage.setItem("ca_user", JSON.stringify(data.user));
            localStorage.setItem("ca_token", data.token);

            showAlert("success", `Account created successfully! Welcome, ${data.user.full_name}. Entering dashboard...`);

            setTimeout(() => {
                window.location.replace("/dashboard");
            }, 700);

        } catch (err) {
            showAlert("error", err.message || "Could not register account. Please check your details.");
            signupSubmitBtn.disabled = false;
            signupSpinner.style.display = "none";
        }
    });
});
