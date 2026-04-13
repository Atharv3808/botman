# Botman: Project Architecture & Technical Description

**Botman** is a comprehensive, full-stack AI SaaS platform designed to let users easily create, configure, train, and deploy intelligent custom chatbots. It acts as a powerful orchestrator, connecting foundational AI models with custom user files through Retrieval-Augmented Generation (RAG). Bots can be deployed directly into standalone web applications via embeddable widgets, or synced to communication platforms like Telegram.

We built this platform with a clear separation of concerns, employing a robust async-capable backend architecture for AI pipelines, matched with a modern React SPA tailored for seamless UX.

---

## 1. Main Features 

- **Bot Studio**: A visual interface where users define the chatbot's core personalities, appearance (colors, text styling), and behavioral instructions for the AI context window.
- **Knowledge Base (RAG Pipeline)**: Users can upload domain-specific PDFs and TXT files. The system intelligently breaks down these files and maps them geometrically so the bot can "learn" and query the data to answer very specific domain questions, preventing AI hallucinations.
- **Deployable Embed / Widget JS**: Automatically generates robust standalone JS/HTML snippets integrating seamlessly into an end user's external website.
- **Telegram Integration**: Connect bots dynamically via standard Telegram HTTP bot tokens to serve as autonomous Telegram agents.
- **Live Interaction Previews**: An interactive chat terminal directly embedded in the dashboard for real-time fine-tuning and testing.
- **Analytics & Quota Systems**: Robust background-processed analytics giving users usage metrics, message insights, and token costs via interactive charts. This links directly to a tier-capable User Subscription system.
- **Authentication**: JWT-backed security with comprehensive Google SSO via Firebase.

---

## 2. Technical Stack & Tooling

### The Backend Application Layer
- **Framework**: Built on **Django** & **Django REST Framework (DRF)**. We chose Django for its strong ORM abstractions, built-in robust security rules, and easy administrative abstractions.
- **Persistent Storage (Database)**: Locally runs effortlessly on **SQLite**, but gracefully escalates to **PostgreSQL** in production to natively lean on the **`pgvector`** extension for lightning-fast AI vector mathematics.
- **Asynchronous Processing**: **Redis** and **Celery** handle all long-duration computations (e.g., chunking large PDFs, generating LLM vectors, talking to the Telegram API). This protects the Django Web Worker pool from stalling during API requests.
- **AI Integrations**: Leverages the **Google Generative AI (Gemini)** SDK heavily for text Embeddings, and **OpenAI** APIs for the core conversational logic.

### The Frontend Application Layer
- **Core Engine**: A blazing fast frontend pipeline run by **Vite** and built in **React.js**.
- **User Interface**: Heavily leverages **TailwindCSS** for rapid complex styling. The design language pushes extreme modern dark-mode aesthetic features: *glassmorphism (blur backdrops)*, ambient animated glowing halos, interactive states, and beautiful **`lucide-react`** iconography.
- **State & Data Protocol**: Uses localized dynamic states and **Axios** with complex HTTP Interceptor pipelines enforcing auto-renewal paths for expired `JWT` Authentication Tokens transparently.
- **Data Visualization**: Rich visual tracking dashboards driven dynamically by **`recharts`**.

---

## 3. Core Technical Implementations

Below is an overview of how we stitched these technologies into business logic.

### 📝 1. The RAG Engine (Smart Memory Mapping)
The hardest part of training AI is formatting the data. Here is how we implement file training (`ai_services/` module):
1. **Extraction**: `pypdf` opens user documents inside a Celery background worker. 
2. **Chunking Algorithm**: Data is sliced into sliding `1000` character string chunks overlapping by `200` characters to never sever conceptual context.
3. **Embedding Vectorization**: The Gemini model parses each textual chunk translating word contextual meanings into pure mathematical dimensional arrays (Embeddings).
4. **Hybrid Search Retrieval**: When a user queries a deployed bot, the Backend fires identical algorithms over the query, checks the Database vector (`CosineDistance` natively inside Postgres or via `numpy` locally) AND layers it simultaneously on exact-match word search (`SearchQuery/SearchRank` BM25). This technique (`Reciprocal Rank Fusion (RRF)`) guarantees the correct files are pulled for the OpenAI Chat completion prompt.

### 🔗 2. The Widget Embedding System
We implemented a robust CDN-like capability directly inside the `widgets/` App. 
The system hosts a completely standalone Vanilla JS wrapper (`widget.js`). This script injects shadow DOM components onto external sites isolating our widget CSS completely from their native website CSS rules. Every chat interaction seamlessly passes an HTTP request back into the Django DRF REST Chat APIs avoiding CORS complexities.

### 🚀 3. Task Queues and the Flow of Data
Botman relies critically on `Celery` workers. 
If a user hits `/api/bot/{X}/knowledge/` to upload a 50MB PDF document, doing that natively inside the API Request pipeline would stall the server for 30 seconds resulting in a `504 Gateway Timeout`. Instead, our UI pushes the raw file, DRF responds with a `202 Accepted` queue receipt instantly, and Celery offloads the computation in a parallel thread entirely.

### 📊 4. The Analytics Aggregation
To prevent locking the main database tables every time a user requests a Chart on their dashboard, we implemented a Cron-style Daily Aggregation. Celery spins up `analytics.tasks.aggregate_daily_analytics` sequentially scanning millions of standard interaction events and compiling extremely minimal Daily Statistic models mapping out Total Tokens and Conversations, which are then passed efficiently into the `recharts` logic on the UI.
