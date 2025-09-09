# PostPilot 🚀  
PostPilot is an *AI-powered platform* that helps users quickly generate professional LinkedIn posts. With intelligent content generation, personalization, and post management, PostPilot ensures your ideas turn into engaging posts—while keeping scalability and performance in mind.  

---

## 🌟 Features  

- ✍ *AI Post Generator* – Create LinkedIn posts tailored to your prompt, topic, tone, length, and audience.  
- 🧠 *Smart Personalization* – Adjust tone (casual, professional, persuasive, etc.) and length (short, medium, long).  
- 📑 *Content Templates* – Generate ready-to-post drafts for consistent branding.  
- 🔄 *Post History* – Save and revisit previously generated posts.  
- ⚡ *Fast & Reliable* – Optimized workflows for quick generation.  

---

## 🛠 Tech Stack  

- *Backend*: FastAPI (Python)  
- *Databases*:  
  - PostgreSQL → for authentication and user management  
  - MongoDB → for storing and managing generated posts  
  - Pinecone → Vector DB for embeddings of user posts  
- *Authentication*: JWT-based secure login system  
- *AI Integration*: OpenAI API / LangChain  
- *Scraping*: Playwright (lightweight, fast, and less detectable)  

---

## 📈 Key Contributions  

> **Team Project – 3 Members**  
> - Designed and implemented **Post Generator Engine** (AI-driven, parameterized).  
> - Developed **hybrid database design** with PostgreSQL + MongoDB.  
> - Integrated **Playwright scraping** for fast and stealthy web data extraction.  
> - Built **history & draft management** for easy retrieval.  
> - Ensured **backend scalability** for high-concurrency requests.  

---

## ⚙ How It Works  

1. *Enter Prompt*: Provide a topic or short idea for the LinkedIn post.  
2. *Choose Parameters*: Select tone, audience, and hashtags.  
3. *Generate Post*: AI instantly generates a high-quality draft.  
4. *Refine & Save*: Edit, save, or copy the post to LinkedIn.  

---

## 🏗 Project Setup  

### Prerequisites  
- Python 3.10+  
- FastAPI  
- PostgreSQL  
- MongoDB  
- Docker + Docker Compose  

### Steps to Run  

```bash
# Clone the repository
git clone https://github.com/Upadhyay-Yatendra/PostPilot
cd PostPilot

# Configure environment variables in .env files (see /services/*/.env examples)

# Build and run with Docker
docker-compose up --build
