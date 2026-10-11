
const API_URL = window.location.origin;
document.addEventListener("DOMContentLoaded", () => {
    const loginSection = document.getElementById("loginSection");
    const registerSection = document.getElementById("registerSection");

    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    // Show Login page
    window.showLogin = function () {
    document.getElementById("registerSection").style.display = "none";
    document.getElementById("loginSection").style.display = "block";
};

window.showRegister = function () {
    document.getElementById("loginSection").style.display = "none";
    document.getElementById("registerSection").style.display = "block";
};

    showLogin();

    // Handle Register/Login navigation links or buttons
    document.addEventListener("click", (event) => {
        const element = event.target.closest("a, button");

        if (!element) return;

        const text = element.textContent.trim().toLowerCase();
        const id = element.id.toLowerCase();

        if (
            (id.includes("register") || id.includes("signup") ||
             text === "register" || text === "sign up" ||
             text.includes("create an account") ||
             text.includes("don't have an account"))
            && !element.closest("#registerForm")
        ) {
            event.preventDefault();
            showRegister();
        }

        if (
            (id.includes("showlogin") || id.includes("backtologin") ||
             text === "back to login" || text === "already have an account?" ||
             text === "login here")
            && !element.closest("#loginForm")
        ) {
            event.preventDefault();
            showLogin();
        }
    });

    // Registration
    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const name = document.getElementById("registerName").value.trim();
        const email = document.getElementById("registerEmail").value.trim();
        const password = document.getElementById("registerPassword").value;
        const department = document.getElementById("registerDepartment")?.value || "";
        const year = document.getElementById("registerYear")?.value || "";

        const message = document.getElementById("registerMessage");
        message.textContent = "Registering...";

        try {
            const response = await fetch(`${API_URL}/api/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
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
                throw new Error(result.message || "Registration failed.");
            }

            message.style.color = "green";
            message.textContent = "Registration successful! Please login.";

            registerForm.reset();

            setTimeout(showLogin, 1200);
        } catch (error) {
            message.style.color = "red";
            message.textContent = error.message || "Server connection failed.";
        }
    });

    // Login
    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const email = document.getElementById("loginEmail").value.trim();
        const password = document.getElementById("loginPassword").value;

        const message = document.getElementById("loginMessage");
        message.textContent = "Logging in...";

        try {
            const response = await fetch(`${API_URL}/api/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (!response.ok || result.success === false || !result.user) {
                throw new Error(result.message || "Invalid email or password.");
            }

            const user = result.user;

            localStorage.setItem("student", JSON.stringify({
                student_id: user.id,
                id: user.id,
                name: user.name,
                email: user.email,
                credit_balance: user.skill_credits ?? 10
            }));

            message.style.color = "green";
            message.textContent = "Login successful!";

            window.location.href = "dashboard.html";
        } catch (error) {
            message.style.color = "red";
            message.textContent = error.message || "Server connection failed.";
        }
    });
});
