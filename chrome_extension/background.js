chrome.runtime.onInstalled.addListener(() => {
  console.log("✅ SafeWebGuard Extension installed.");
  chrome.storage.sync.set({ child_email: "child@example.com" });
});

function sendBrowsingData(data) {
  fetch("http://127.0.0.1:8000/api/log_browsing/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data)
  })
  .then(res => res.json())
  .then(response => console.log("✅ Log sent:", response))
  .catch(err => console.error("❌ Error sending log:", err));
}

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url && tab.url.startsWith("http")) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: () => ({ title: document.title, url: window.location.href })
    }, (results) => {
      if (!results || !results[0] || !results[0].result) return;
      chrome.storage.sync.get("child_email", (result) => {
        const data = {
          child_email: result.child_email || "child@example.com",
          title: results[0].result.title,
          url: results[0].result.url,
          query: "",
          image_score: 0.2,
          duration_sec: 10,
          hour_of_day: new Date().getHours()
        };
        sendBrowsingData(data);
      });
    });
  }
});
