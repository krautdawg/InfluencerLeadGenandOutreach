

---

### **Instagram LeadGen – Full‑Stack Build Spec (REV 3\)**

This document is the single source of truth, outlining a self-contained Flask application. It supersedes all previous drafts.

---

### **1\. End-to-End Workflow (Keyword → UI → Email)**

The application will manage the entire process, from data collection to displaying results and sending emails, within a single web interface. Data will be held in a server-side session and displayed dynamically.

#### **1.1. App Launch & Session Setup**

* On app start, the Flask backend checks for IG\_SESSIONID in the environment variables / Replit Secrets.  
* If the IG\_SESSIONID is **missing**, the UI will render a modal asking the user to provide it.  
* On submit, the ID is sent via POST /session to the server, where it's stored in the Flask session for all subsequent API calls.

#### **1.2. Keyword Processing & Data Fetching**

* The main UI presents a textbox labeled “Keyword eingeben…” and a "Run" button.  
* On "Run," the backend executes the following sequence:  
  1. **Hashtag Crawl**: Calls Apify actor DrF9mzPPEuVizVF4l (run-sync) using the user's keyword and the stored IG\_SESSIONID.  
  2. **Flatten & Deduplicate**: Iterates over latestPosts and topPosts, creating a clean list of unique {hashtag, username} objects. Duplicates are removed using the key f"{hashtag}|{username}".  
  3. **Profile Enrichment (Concurrent ≤ 10\)**: For each unique username, the backend concurrently calls the Apify actors:  
     * Profile data (8WEn9FvZnhE7lM3oA)  
  4. **Perplexity Fallback (Concurrent ≤ 5\)**: For any profile still missing an email, phone, or website, the backend calls the Perplexity Chat Completions API (pplx-7b-chat) with the following prompt to find publicly available contact info. The code must safely parse the expected JSON response.  
     * **System**: Du bist ein hilfreicher Recherche‑Assistent, finde öffentlich verfügbare Kontaktinfos.  
     * **User**:  
     * Plaintext

Suche nach E-Mail-Adresse, Telefonnummer oder Website des Instagram-Profils  
https://www.instagram.com/{username}/  
Antworte nur als JSON:  
{ "email": "…", "phone": "…", "website": "…" }

*   
  *   
  5. **Store Results**: The final, enriched list of profiles is stored in the server-side database.  
  6. Future results are added to the html table, which has a sort feature and highlights duplicate usernames with an orange background  
  7. There is an option to export to GoogleSheets, Excel or CSV

#### **1.3. UI: Data Display & Actions**

* After processing, the page re-renders, displaying the results in a dynamic HTML table. Each row represents a single lead and contains all collected data (username, fullName, bio, email, etc.).  
* Each row in the table will have:  
  * Display columns for all collected data.  
  * Text areas for Subject and EmailBody (can be populated on draft).  
  * A "**Draft Email**" button.  
  * A "**Send Email**" button.

#### **1.4. UI: Email Drafting & Sending**

This logic is handled entirely by the Flask backend, triggered by user actions in the UI.

* **When a user clicks "Draft Email" for a row:**  
  1. A fetch request is sent to a new Flask endpoint (e.g., POST /draft/\<username\>).  
  2. The backend retrieves the profile data for that username.  
  3. It calls the selected LLM (OpenAI GTP Model 4.5) using the customizable prompts from the UI's settings panel to generate a subject and body.  
  4. The generated { "subject": "...", "body": "..." } is returned to the UI, which then populates the Subject and EmailBody text areas for that specific row.  
* **When a user clicks "Send Email" for a row:**  
  1. A fetch request is sent to POST /send/\<username\>.  
  2. The backend retrieves the recipient's email address, subject, and body from the submitted form data.  
  3. It connects to the **Gmail API** using the OAuth2 credentials from the environment variables.  
  4. On a successful send, the backend returns a success message. The UI then updates that row to show a "Sent" status with a timestamp (e.g., replacing the "Send" button).  
  5. Errors (e.g., Gmail API quota) are logged and displayed to the user as a toast message.

---

### **2\. Tech Stack & Environment**

| Layer | Library / API |
| :---- | :---- |
| **Backend** | Flask (flask), httpx\[async\], asyncio |
| **LLMs** | OpenAI API, Perplexity API |
| **Frontend** | Vanilla JS \+ Bootstrap 5 |
| **Secrets** | Replit Secrets or .env \+ python-dotenv |

**Required Environment Variables (.env):**

* SECRET\_KEY (for Flask sessions)  
* APIFY\_TOKEN  
* IG\_SESSIONID (optional, can be input via UI)  
* OPENAI\_API\_KEY (optional)  
* PERPLEXITY\_API\_KEY  
* GMAIL\_CLIENT\_ID  
* GMAIL\_CLIENT\_SECRET  
* GMAIL\_REFRESH\_TOKEN

---

### **3\. File / Folder Layout**

The leadgen.gs file is no longer needed.

/                     \# repo root  
├─ main.py            \# Single-file Flask app with all logic  
├─ /templates  
│   └─ index.html     \# Main UI with form, results table, and modals  
├─ /static  
│   └─ ui.js          \# Client-side fetch/AJAX helpers for buttons  
├─ requirements.txt  
├─ .env.example  
└─ README.md

---

### **4\. Additional Requirements & Delivery**

* **Concurrency:** Use asyncio.Semaphore(10) for Apify calls and a limit of 5 for Perplexity.  
* **Error Logging:** Use logging.error() for backend errors and display user-friendly toast messages in the UI.  
* **Health Check:** Implement a GET /ping endpoint that returns 200 OK.  
* **Tests:** pytest for the de-duplication utility.  
* **Code Style:** black, isort, flake8.  
* **README:** Detailed setup for Replit and local environments.  
* **Delivery:** Provide a zip or GitHub repo ready to run.  
* Stylesheet: Use the following as a guide:

  /\* \--- Kasimir Lieselotte Inspired Stylesheet \--- \*/  
*   
* /\* 1\. Global Variables & Resets  
* \------------------------------------------- \*/  
* :root {  
*     \--font-main: 'Cormorant Garamond', 'EB Garamond', 'Times New Roman', serif; /\* Elegant serif font \*/  
*       
*     \--color-text: \#000000;  
*     \--color-background: \#FFFFFF;  
*     \--color-background-alt: \#F2F2F2; /\* Subtle grey for containers \*/  
*     \--color-border: \#E0E0E0;  
*     \--color-accent: \#A5A5A5; /\* A slightly darker grey for hover states \*/  
* }  
*   
* /\* Import the recommended Google Font \*/  
* @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700\&display=swap');  
*   
* \* {  
*     box-sizing: border-box;  
*     margin: 0;  
*     padding: 0;  
* }  
*   
* /\* 2\. Body & Typography  
* \------------------------------------------- \*/  
* body {  
*     font-family: var(--font-main);  
*     background-color: var(--color-background);  
*     color: var(--color-text);  
*     line-height: 1.7; /\* Generous line spacing for readability \*/  
*     padding: 2rem;  
*     font-size: 18px;  
*     \-webkit-font-smoothing: antialiased;  
* }  
*   
* h1, h2, h3 {  
*     font-weight: 700; /\* Bolder weight for headings \*/  
*     line-height: 1.2;  
*     margin-bottom: 1.5rem;  
* }  
*   
* h1 { font-size: 2.5rem; }  
* h2 { font-size: 2rem; }  
* p { margin-bottom: 1rem; }  
* a {  
*     color: var(--color-text);  
*     text-decoration: none;  
*     transition: color 0.2s ease;  
* }  
* a:hover {  
*     color: var(--color-accent);  
* }  
*   
* /\* 3\. Forms & Inputs  
* \------------------------------------------- \*/  
* .form-group {  
*     margin-bottom: 1.5rem;  
* }  
*   
* .form-control,  
* textarea {  
*     display: block;  
*     width: 100%;  
*     padding: 0.75rem 1rem;  
*     font-family: var(--font-main);  
*     font-size: 1rem;  
*     border: 1px solid var(--color-border);  
*     background-color: var(--color-background);  
*     color: var(--color-text);  
*     border-radius: 0; /\* Sharp corners \*/  
*     transition: border-color 0.2s ease;  
* }  
*   
* .form-control:focus {  
*     outline: none;  
*     border-color: var(--color-text);  
* }  
*   
* label {  
*     display: block;  
*     font-weight: 600;  
*     margin-bottom: 0.5rem;  
* }  
*   
* /\* 4\. Buttons  
* \------------------------------------------- \*/  
* .btn {  
*     padding: 0.75rem 1.5rem;  
*     font-family: var(--font-main);  
*     font-size: 1rem;  
*     font-weight: 600;  
*     text-align: center;  
*     cursor: pointer;  
*     border: 1px solid var(--color-text);  
*     background-color: var(--color-text);  
*     color: var(--color-background);  
*     border-radius: 0;  
*     transition: background-color 0.2s ease, color 0.2s ease;  
*     text-transform: uppercase;  
*     letter-spacing: 0.05em;  
* }  
*   
* .btn:hover {  
*     background-color: var(--color-background);  
*     color: var(--color-text);  
* }  
*   
* /\* Secondary button style (e.g., for "Draft") \*/  
* .btn-secondary {  
*     background-color: transparent;  
*     color: var(--color-text);  
*     border: 1px solid var(--color-border);  
* }  
* .btn-secondary:hover {  
*     background-color: var(--color-background-alt);  
*     border-color: var(--color-text);  
* }  
*   
*   
* /\* 5\. Layout & Containers  
* \------------------------------------------- \*/  
* .container {  
*     max-width: 1200px;  
*     margin: 0 auto;  
*     padding: 2rem;  
* }  
*   
* .main-content {  
*     background-color: var(--color-background-alt);  
*     padding: 2rem;  
*     margin-top: 2rem;  
* }  
*   
* /\* 6\. Table Styles  
* \------------------------------------------- \*/  
* .results-table {  
*     width: 100%;  
*     border-collapse: collapse;  
*     margin-top: 2rem;  
* }  
*   
* .results-table th,  
* .results-table td {  
*     padding: 1rem;  
*     text-align: left;  
*     border-bottom: 1px solid var(--color-border);  
*     vertical-align: top;  
* }  
*   
* .results-table th {  
*     font-weight: 700;  
*     text-transform: uppercase;  
*     font-size: 0.85rem;  
*     letter-spacing: 0.05em;  
* }  
*   
* .results-table tr:last-child td {  
*     border-bottom: none;  
* }  
*   
* .results-table tr:nth-child(even) {  
*     background-color: var(--color-background-alt);  
* }  
*   
* /\* 7\. Modal (for session ID input)  
* \------------------------------------------- \*/  
* .modal {  
*   display: none; /\* Hidden by default \*/  
*   position: fixed;   
*   z-index: 1000;  
*   left: 0;  
*   top: 0;  
*   width: 100%;  
*   height: 100%;  
*   overflow: auto;  
*   background-color: rgba(0,0,0,0.5); /\* Dim background \*/  
* }  
*   
* .modal-content {  
*   background-color: var(--color-background);  
*   margin: 15% auto;  
*   padding: 2rem;  
*   width: 90%;  
*   max-width: 500px;  
* }

