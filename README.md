# **Resume Screening Crew**  
## **AI-Powered Resume Evaluator, Automated Candidate Evaluation System**  

Resume Screening AI is an end-to-end intelligent system that evaluates resumes in bulk using CrewAI agents and OpenAI's GPT-4o. It automates candidate screening by assessing skill match, experience, education, and more — and generates structured reports with detailed analysis and recommendations.

⚠️ Note: This project was developed as part of my internship work. For confidentiality reasons, the complete source code is not posted here, and certain parts have been modified/removed to respect company policies.

##  **Features**  
✅ **Batch Resume Screening** – Processes up to 30 resumes in parallel, 10 per batch.  
✅ **CrewAI Agent based Evaluation** – Uses specialized agents to assess Skill Match, Experience, Education, Culture Fit & Keyword Alignment..  
✅ **Final Markdown Summary** – Compiles rankings, scores, and recommendations into a comprehensive markdown report.   
✅ **Interactive UI** – User-friendly Streamlit dashboard for seamless analysis.  

## **Installation**  
### **1️⃣ Clone the Repository**  
```bash
git clone https://github.com/yourusername/Resume-Screening-Crew.git
cd resume_checker
```
### **2️⃣ Install Dependencies**  
```bash
pip install -r requirements.txt
```
### **3️⃣ Set Up API Keys**  
Create a `.env` file and add your API credentials:  
```
OPENAI_API_KEY="your_api_key"
```
### **4️⃣ Run the Application**  
```bash
streamlit run streamlit_app.py
```

## **Screening Workflow**  
- **Home Page** – Upload folder containing resumes and paste the JD.
- **Parallel Text Extraction** – Extracts text from all resumes using PyMuPDF and multiprocessing.  
- **Agentic Evaluation** – Agents assess each resume for core parameters using LLM prompts.
- **Structured Report Generation** – Per batch, a JSON is generated with component scores and summaries.  

## **Tech Stack**  
- **Frontend**: Streamlit  
- **Backend**: Python, CrewAI , PyMuPDF
- **Data Sources**: Uploaded documents along with JD.  
- **Configuration**: YAML-based agent and task design.
