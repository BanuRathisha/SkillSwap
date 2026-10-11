const API_URL = "https://skillswap-0hx0.onrender.com";

// Make navigation functions available to index.html onclick
window.showLogin = function () {
    const loginSection = document.getElementById("loginSection");
    const registerSection = document.getElementById("registerSection");

    if (loginSection) loginSection.style.display = "block";
    if (registerSection) registerSection.style.display = "none";
};

window.showRegister = function () {
    const loginSection = document.getElementById("loginSection");
    const registerSection = document.getElementById("registerSection");

    if (loginSection) loginSection.style.display = "none";
    if (registerSection) registerSection.style.display = "block";
};

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    const loginMessage = document.getElementById("loginMessage");
    const registerMessage = document.getElementById("registerMessage");

    // Show login section initially
    window.showLogin();

    // Registration
    if (registerForm) {
        registerForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const name = document.getElementById("registerName").value.trim();
            const email = document.getElementById("registerEmail").value.trim();
            const password = document.getElementById("registerPassword").value;
            const department =
                document.getElementById("registerDepartment")?.value || "";
            const year =
                document.getElementById("registerYear")?.value || "";

            registerMessage.textContent = "Registering...";
            registerMessage.style.color = "black";

            try {
                const response = await fetch(`${API_URL}/api/register`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        name,
                        email,
                        password,
                        department,
                        year
                    })
                });

                const result = await response.json();

                if (!response.ok || result.success === false) {
                    throw new Error(
                        result.message || "Registration failed."
                    );
                }

                registerMessage.style.color = "green";
                registerMessage.textContent =
                    result.message || "Registration successful! Please login.";

                registerForm.reset();

                setTimeout(() => {
                    window.showLogin();
                }, 1200);

            } catch (error) {
                registerMessage.style.color = "red";
                registerMessage.textContent =
                    error.message || "Server connection failed.";
            }
        });
    }

    // Login
    if (loginForm) {
        loginForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const email = document.getElementById("loginEmail").value.trim();
            const password =
                document.getElementById("loginPassword").value;

            loginMessage.textContent = "Logging in...";
            loginMessage.style.color = "black";

            try {
                const response = await fetch(`${API_URL}/api/login`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ email, password })
                });

                const result = await response.json();

                if (!response.ok || result.success === false || !result.user) {
                    throw new Error(
                        result.message || "Invalid email or password."
                    );
                }

                const user = result.user;

                localStorage.setItem("student", JSON.stringify({
                    student_id: user.id,
                    id: user.id,
                    name: user.name,
                    email: user.email,
                    credit_balance: user.skill_credits ?? 100
                }));

                loginMessage.style.color = "green";
                loginMessage.textContent = "Login successful!";

                window.location.href = "dashboard.html";

            } catch (error) {
                loginMessage.style.color = "red";
                loginMessage.textContent =
                    error.message || "Server connection failed.";
            }
        });
    }
});