#  Local Text Filtering Chatbot  
A local, privacy-preserving text moderation system powered by **Mistral-7B v0.2** and a custom **LoRA fine-tuned classifier**.  
The backend runs a FastAPI service that loads both the base model and the adapter locally, and the frontend provides a simple React-based chat interface.

This project allows you to classify user messages as **SAFE** or **UNSAFE** before processing them, making it suitable for parental control tools, community moderation systems, and content-filtering assistants.

---

##  Features

- Runs **fully offline** – no external API calls  
- Uses **Mistral-7B v0.2** as the base model  
- Custom **LoRA adapter** enables fast & lightweight filtering  
- Backend built with **FastAPI**  
- Frontend built with **React**  
- Simple `/api/chat` endpoint that:
  1. Extracts the latest user message  
  2. Classifies it as SAFE or UNSAFE  
  3. Returns a JSON response  

---

##  Project Structure

```

back/
  app/
    main.py
    config.py
    model.py
    routes/
      chat.py
    models/
      base/        <- Full Mistral-7B-v0.2 checkpoint (downloaded)
      adapter/     <- LoRA filtering adapter (downloaded)

front/
  src/
    App.jsx
    main.jsx
    App.css
    index.css

````

---

##  Requirements

### Backend
- Python 3.10+
- PyTorch (CPU or CUDA build)
- FastAPI
- Uvicorn
- Transformers
- PEFT
- pydantic-settings

Install everything:

```bash
pip install -r requirements.txt
````

*(If you don't have a requirements file, you may create one or install manually.)*

### Frontend

* Node.js 18+
* npm or yarn

---

##  Model Setup
This repository does NOT include the full Mistral-7B base weights.

Please download them with:

```bash
huggingface-cli download mistralai/Mistral-7B-v0.2 \
  --local-dir back/app/models/base

```bash
huggingface-cli download Devna08/filter_waifu \
  --local-dir back/app/models/adapter

Your folder must contain:

```
back/app/models/
  base/
    config.json
    generation_config.json
    tokenizer.json (or tokenizer.model)
    tokenizer_config.json
    special_tokens_map.json
    model-00001-of-00003.safetensors
    model-00002-of-00003.safetensors
    model-00003-of-00003.safetensors
    model.safetensors.index.json

  adapter/
    adapter_model.safetensors
    adapter_config.json
```

---

## ▶ Running the Backend

From `/back`:

```bash
python -m uvicorn app.main:app --reload
```

Server will start at:

```
http://127.0.0.1:8000
```

Test health endpoints:

```
GET /health
GET /config
```

---

## ▶ Running the Frontend

From `/front`:

```bash
npm install
npm run dev
```

Open browser:

```
http://localhost:5173
```

---

##  API Usage

### POST `/api/chat`

**Request:**

```json
{
  "messages": [
    { "role": "user", "content": "your message here" }
  ]
}
```

**Response:**

```json
{
  "role": "assistant",
  "content": "This message is considered safe.",
  "is_safe": true,
  "raw_decision": "SAFE",
  "normalized_decision": "SAFE"
}
```

---

##  How It Works

1. The backend loads:

   * The **Mistral base model**
   * The **LoRA adapter** (classification fine-tuning)
2. The latest user message is passed through a prompt:

   ```
   Determine whether this is SAFE or UNSAFE...
   ```
3. The model generates a one-word output:
   **“SAFE”** or **“UNSAFE”**
4. The backend converts this into structured JSON
5. The frontend displays the result in chat form

---

##  Development Notes

* The Mistral 7B model loads in ~20–30 seconds on first request
* Use `cpu` if no GPU is available (slower but works)
* You can adjust filtering sensitivity in `classify_text()`:

  * Change keywords
  * Modify the prompt
  * Add probability-based logic

---

##  License

This project contains machine-learning model weights that may be subject to the original Mistral AI license and the license associated with your fine-tuned adapter.
Code in this repository is free to modify and distribute.