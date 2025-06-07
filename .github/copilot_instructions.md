# 🧠 Lamda Monitor Project – Best Practices Guide

This guide outlines **best practices** for building the **Lamda Monitor** system. The goal is to ensure **readability**, **modularity**, and **maintainability** when integrating scraping, AI analysis, and real-time alerting.

Technologies used:

* Python
* Postgres (native driver only)
* NVIDIA Nemotron LLM API
* ScrapeCreators API or ChromeDriver
* X (Twitter) API
* Truth Social scraping
* Webhooks / Push Notifications
* Redis (for queueing, if used)

---

## 📁 Project Structure

Keep a **modular and predictable** folder structure:

```bash
/lamda-monitor
  /src
    /fetchers       # Modules to pull posts from X, Truth Social, etc.
    /analyzers      # AI models + scoring logic
    /notifiers      # Push notification logic (mobile, webhook)
    /database       # Postgres SQL queries (no ORM)
    /utils          # Utility scripts (time, logging, parsing)
    /drivers        # Fallback scraping logic using ChromeDriver
    main.py         # Entry point (Python) or index.js (Node.js)
    config.env      # API keys and config
  /logs
  /docs             # PRD, API specs, markdown docs
```

📌 **Rules:**

* **Flat > deeply nested.**
* **No magical abstractions.** Keep things clear.
* **Group by function, not type.**

---

## 🔍 Data Fetching Best Practices

### ✅ Use APIs when available

```ts
// src/fetchers/xApiFetcher.ts
fetchFromXAPI(userId) {
  return fetch(`https://api.x.com/2/users/${userId}/tweets?...`, headers)
}
```

### 🔄 Use fallback scraping (ChromeDriver) when needed

```ts
// src/drivers/truthSocialScraper.ts
const driver = new Builder().forBrowser('chrome').build();
await driver.get("https://truthsocial.com/@realDonaldTrump");
```

📌 **Rules:**

* **Always prefer official API.**
* **Respect rate limits.**
* **Isolate scraping logic.**

---

## 🧠 AI Analysis Best Practices

### ✅ Use external model APIs (e.g., Nemotron)

```ts
// src/analyzers/nemotronAnalyzer.ts
const response = await fetch("https://api.nvidia.com/...", {
  method: "POST",
  body: JSON.stringify({ prompt: postText })
});
```

📌 **Rules:**

* **Keep model prompts version-controlled.**
* **Log every inference with score & timestamp.**
* **Fallback to basic keyword heuristics if API fails.**

---

## 📣 Notification Best Practices

### ✅ Push notifications immediately when impact is high

```ts
// src/notifiers/pushMobileAlert.ts
if (score > 80) {
  sendPush(userDeviceId, "🚨 High-impact post detected!");
}
```

📌 **Rules:**

* **Don't spam. Throttle alerts.**
* **Log all alerts sent.**
* **Use scoring thresholds.**

---

## 🗃 Database Best Practices

### ✅ Use native Postgres driver

```ts
// src/database/postLogger.ts
await client.query("INSERT INTO posts (author, content, impact_score) VALUES ($1, $2, $3)", [author, text, score]);
```

📌 **Rules:**

* **Avoid ORMs. Use raw SQL.**
* **Use indexes on timestamp + author.**
* **Batch writes where possible.**

---

## ⚙ Utility and Config Best Practices

```env
# config.env
X_API_KEY=...
SCRAPE_CREATORS_KEY=...
PUSH_SERVICE_URL=https://...
```

📌 **Rules:**

* **Never hardcode secrets.**
* **Use dotenv or environment variables.**
* **Validate config at startup.**

---

## 🧪 Logging and Debugging Best Practices

* **Use consistent logging format.**
* **Log errors with trace ID.**
* **Log every major action: fetch, analyze, notify.**

---

## 🛠 Dev Environment Tips (PowerShell Compatible)

```ps1
# Install dependencies
npm install

# Start local dev mode (Node)
npm run dev

# For Python modules
pip install -r requirements.txt
python main.py
```

---

## 🔥 Final Thoughts

1. **Readability > Cleverness.**
2. **Always version control API prompts and thresholds.**
3. **Test every module independently.**
4. **Use markdown docs for all workflows.**
5. **Respect external platform policies.**
6. **Avoid building brittle scrapers—log failures.**

---
