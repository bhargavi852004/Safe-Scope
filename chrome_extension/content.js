(async () => {
  const navEntry = performance.getEntriesByType("navigation")[0];
  if (navEntry && navEntry.type !== "navigate") return;

  chrome.storage.sync.get(["child_email"], async function (result) {
    const childEmail = result.child_email;
    if (!childEmail) return;

    const url = window.location.href;
    const title = document.title;
    const startTime = Date.now();

    function extractSearchQuery(url) {
      try {
        const urlObj = new URL(url);
        const queryParam = urlObj.searchParams.get("q");
        return queryParam || title;
      } catch {
        return title;
      }
    }

    const queryText = extractSearchQuery(url);

    setTimeout(async () => {
      const durationSec = Math.floor((Date.now() - startTime) / 1000);
      const hour = new Date().getHours();
      const isNightTime = hour >= 22 || hour <= 6;

      const payload = {
        child_email: childEmail,
        title,
        url,
        query: queryText,
        hour_of_day: hour,
        image_score: 0.5,
        duration_sec: durationSec,
        is_night_time: isNightTime,
      };

      try {
        const response = await fetch("http://127.0.0.1:8000/api/log_browsing/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const result = await response.json();
        console.log("✅ Sent to backend:", result);
      } catch (err) {
        console.error("❌ Failed to send to backend:", err);
      }
    }, 3000);
  });
})();
