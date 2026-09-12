let currentTransactions = [];
let isLoginMode = true;
let expenseChart = null;

document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  checkAuth();
});

function setupEventListeners() {
  document.getElementById("auth-form").addEventListener("submit", handleAuthSubmit);
  document.getElementById("auth-toggle-link").addEventListener("click", toggleAuthMode);
  document.getElementById("logout-btn").addEventListener("click", handleLogout);
  document.getElementById("transaction-form").addEventListener("submit", handleFormSubmit);
  document.getElementById("cancel-btn").addEventListener("click", resetForm);
}

function checkAuth() {
  const token = localStorage.getItem("access_token");
  const username = localStorage.getItem("username");

  if (token) {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("app-section").style.display = "block";
    document.getElementById("logout-btn").style.display = "inline-block";
    document.getElementById("welcome-msg").textContent = `Logged in as ${username}`;
    document.getElementById("user_name").value = username;

    loadTransactions();
  } else {
    document.getElementById("auth-section").style.display = "block";
    document.getElementById("app-section").style.display = "none";
    document.getElementById("logout-btn").style.display = "none";
    document.getElementById("welcome-msg").textContent = "Log and track shared income and expenses";
  }
}

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

async function handleAuthSubmit(event) {
  event.preventDefault();

  const username = document.getElementById("auth-username").value.trim();
  const password = document.getElementById("auth-password").value;

  if (isLoginMode) {
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
      toggleAuthMode(event);
    } catch (error) {
      console.error("Registration failed:", error);
      alert("Unable to reach the server.");
    }
  }
}

function handleLogout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("username");
  checkAuth();
}

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
    renderExpenseChart(currentTransactions);
  } catch (error) {
    console.error("Error loading transactions:", error);
  }
}

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

function renderExpenseChart(transactions) {
  const categoryTotals = {};

  transactions.forEach((tx) => {
    if (tx.transaction_type === "expense") {
      const cat = tx.category.trim() || "Uncategorized";
      categoryTotals[cat] = (categoryTotals[cat] || 0) + tx.amount;
    }
  });

  const categories = Object.keys(categoryTotals);
  const amounts = Object.values(categoryTotals);

  const canvas = document.getElementById("expense-chart");
  const noDataMsg = document.getElementById("no-chart-data");

  if (categories.length === 0) {
    canvas.style.display = "none";
    noDataMsg.style.display = "block";
    if (expenseChart) {
      expenseChart.destroy();
      expenseChart = null;
    }
    return;
  }

  canvas.style.display = "block";
  noDataMsg.style.display = "none";

  const palette = [
    "#e57373", "#81c784", "#64b5f6", "#ffb74d",
    "#ba68c8", "#4db6ac", "#fff176", "#a1887f"
  ];

  if (expenseChart) {
    expenseChart.destroy();
  }

  const ctx = canvas.getContext("2d");
  expenseChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: categories,
      datasets: [{
        data: amounts,
        backgroundColor: palette.slice(0, categories.length),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom"
        }
      }
    }
  });
}

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

function resetForm() {
  const username = localStorage.getItem("username") || "";
  document.getElementById("editing-id").value = "";
  document.getElementById("transaction-form").reset();
  document.getElementById("user_name").value = username;
  document.getElementById("form-heading").textContent = "Add New Entry";
  document.getElementById("submit-btn").textContent = "Save Entry";
  document.getElementById("cancel-btn").style.display = "none";
}

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