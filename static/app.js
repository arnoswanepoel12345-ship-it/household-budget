let currentTransactions = [];
let isLoginMode = true;

document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  checkAuth();
});

function setupEventListeners() {
  // Authentication form submit
  document.getElementById("auth-form").addEventListener("submit", handleAuthSubmit);

  // Switch between Log In and Register modes
  document.getElementById("auth-toggle-link").addEventListener("click", toggleAuthMode);

  // Log Out button
  document.getElementById("logout-btn").addEventListener("click", handleLogout);

  // Budget entry form
  document.getElementById("transaction-form").addEventListener("submit", handleFormSubmit);

  // Cancel edit button
  document.getElementById("cancel-btn").addEventListener("click", resetForm);
}

// Check if user is already logged in
function checkAuth() {
  const token = localStorage.getItem("access_token");
  const username = localStorage.getItem("username");

  if (token) {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("app-section").style.display = "block";
    document.getElementById("logout-btn").style.display = "inline-block";
    document.getElementById("welcome-msg").textContent = `Logged in as ${username}`;
    
    // Auto-fill the "Logged By" field with the user's logged-in name
    document.getElementById("user_name").value = username;

    loadTransactions();
  } else {
    document.getElementById("auth-section").style.display = "block";
    document.getElementById("app-section").style.display = "none";
    document.getElementById("logout-btn").style.display = "none";
    document.getElementById("welcome-msg").textContent = "Log and track shared income and expenses";
  }
}

// Toggle between Login and Register form
function toggleAuthMode(event) {
  event.preventDefault();
  isLoginMode = !isLoginMode;

  const title = document.getElementById("auth-title");
  const submitBtn = document.getElementById("auth-submit-btn");
  const toggleText = document.getElementById("auth-toggle-text");
  const toggleLink = document.getElementById("auth-toggle-link");

  if (isLoginMode) {
    title.textContent = "Log In";
    submitBtn.textContent = "Log In";
    toggleText.textContent = "Need an account?";
    toggleLink.textContent = "Register here";
  } else {
    title.textContent = "Create Account";
    submitBtn.textContent = "Register";
    toggleText.textContent = "Already have an account?";
    toggleLink.textContent = "Log in here";
  }
}

// Handle Login or Register API calls
async function handleAuthSubmit(event) {
  event.preventDefault();

  const username = document.getElementById("auth-username").value.trim();
  const password = document.getElementById("auth-password").value;

  if (isLoginMode) {
    // Log In (FastAPI expects form data for token endpoint)
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      const response = await fetch("/token", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString()
      });

      if (!response.ok) {
        alert("Invalid username or password.");
        return;
      }

      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("username", username);

      document.getElementById("auth-form").reset();
      checkAuth();
    } catch (error) {
      console.error("Login failed:", error);
      alert("Unable to reach the server.");
    }
  } else {
    // Register New User
    try {
      const response = await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        alert(errorData.detail || "Registration failed.");
        return;
      }

      alert("Account created successfully. You can now log in.");
      // Switch to Login mode
      toggleAuthMode(event);
    } catch (error) {
      console.error("Registration failed:", error);
      alert("Unable to reach the server.");
    }
  }
}

// Log out user
function handleLogout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("username");
  checkAuth();
}

// Fetch transactions with Authorization Header
async function loadTransactions() {
  const token = localStorage.getItem("access_token");

  try {
    const response = await fetch("/transactions/", {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (response.status === 401) {
      handleLogout();
      return;
    }

    if (!response.ok) {
      throw new Error("Failed to fetch transactions");
    }

    currentTransactions = await response.json();
    renderTransactions(currentTransactions);
  } catch (error) {
    console.error("Error loading transactions:", error);
  }
}

// Render transactions to the table
function renderTransactions(transactions) {
  const tbody = document.getElementById("transaction-rows");
  tbody.innerHTML = "";

  let totalIncome = 0;
  let totalExpense = 0;

  transactions.forEach((tx) => {
    if (tx.transaction_type === "income") {
      totalIncome += tx.amount;
    } else {
      totalExpense += tx.amount;
    }

    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${tx.title}</td>
      <td><span class="type-badge type-${tx.transaction_type}">${tx.transaction_type}</span></td>
      <td>${tx.category}</td>
      <td>${tx.user_name}</td>
      <td>${tx.amount.toFixed(2)}</td>
      <td>
        <div class="action-buttons">
          <button class="edit-btn" onclick="startEdit(${tx.id})">Edit</button>
          <button class="delete-btn" onclick="deleteTransaction(${tx.id})">Delete</button>
        </div>
      </td>
    `;
    tbody.appendChild(row);
  });

  document.getElementById("total-income").textContent = totalIncome.toFixed(2);
  document.getElementById("total-expense").textContent = totalExpense.toFixed(2);
  document.getElementById("net-balance").textContent = (totalIncome - totalExpense).toFixed(2);
}

// Submit a new transaction or an update
async function handleFormSubmit(event) {
  event.preventDefault();

  const token = localStorage.getItem("access_token");
  const editingId = document.getElementById("editing-id").value;
  const isEditing = editingId !== "";

  const payload = {
    title: document.getElementById("title").value.trim(),
    amount: parseFloat(document.getElementById("amount").value),
    transaction_type: document.getElementById("transaction_type").value,
    category: document.getElementById("category").value.trim(),
    user_name: document.getElementById("user_name").value.trim()
  };

  const url = isEditing ? `/transactions/${editingId}` : "/transactions/";
  const method = isEditing ? "PUT" : "POST";

  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      alert("Failed to save transaction. Please check your inputs.");
      return;
    }

    resetForm();
    loadTransactions();
  } catch (error) {
    console.error("Error submitting transaction:", error);
  }
}

// Populate form for editing
function startEdit(id) {
  const tx = currentTransactions.find((item) => item.id === id);
  if (!tx) return;

  document.getElementById("editing-id").value = tx.id;
  document.getElementById("title").value = tx.title;
  document.getElementById("amount").value = tx.amount;
  document.getElementById("transaction_type").value = tx.transaction_type;
  document.getElementById("category").value = tx.category;
  document.getElementById("user_name").value = tx.user_name;

  document.getElementById("form-heading").textContent = "Edit Entry";
  document.getElementById("submit-btn").textContent = "Update Entry";
  document.getElementById("cancel-btn").style.display = "inline-block";

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Reset form
function resetForm() {
  const username = localStorage.getItem("username") || "";
  document.getElementById("editing-id").value = "";
  document.getElementById("transaction-form").reset();
  document.getElementById("user_name").value = username;
  document.getElementById("form-heading").textContent = "Add New Entry";
  document.getElementById("submit-btn").textContent = "Save Entry";
  document.getElementById("cancel-btn").style.display = "none";
}

// Delete transaction
async function deleteTransaction(id) {
  const confirmed = confirm("Are you sure you want to delete this entry?");
  if (!confirmed) return;

  const token = localStorage.getItem("access_token");

  try {
    const response = await fetch(`/transactions/${id}`, {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!response.ok) {
      alert("Failed to delete the transaction.");
      return;
    }

    loadTransactions();
  } catch (error) {
    console.error("Error deleting transaction:", error);
  }
}