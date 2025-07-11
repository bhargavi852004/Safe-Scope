document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.sync.get(["child_email"], function (result) {
    if (result.child_email) {
      document.getElementById("email").value = result.child_email;
    }
  });

  document.getElementById("saveBtn").addEventListener("click", async () => {
    const email = document.getElementById("email").value.trim();
    const statusDiv = document.getElementById("status");

    if (email === "") {
      statusDiv.textContent = "❌ Please enter a valid email.";
      statusDiv.style.color = "red";
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8000/api/validate_child_email/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        chrome.storage.sync.set({ child_email: email }, function () {
          statusDiv.textContent = "✅ Email validated and saved!";
          statusDiv.style.color = "green";
        });
      } else {
        statusDiv.textContent = "❌ Email not recognized. Please ask your parent to add you.";
        statusDiv.style.color = "red";
      }
    } catch (err) {
      console.error("Validation error:", err);
      statusDiv.textContent = "❌ Couldn't validate. Try again later.";
      statusDiv.style.color = "red";
    }
  });
});
