import re
import json
import os
from crewai import Agent, Crew, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from .tools.extract_text import extract_text_from_pdf_parallel

llm = LLM(
    model="gpt-4o",
    temperature=0.0,
)

BATCH_RESULT_FOLDER = "batch_results"
os.makedirs(BATCH_RESULT_FOLDER, exist_ok=True)

def extract_json_from_markdown(markdown: str):
    """
    Extract JSON object from markdown string.
    """
    try:
        json_pattern = re.compile(r'\{[\s\S]*\}')
        json_match = json_pattern.search(markdown)
        if json_match:
            json_text = json_match.group()
            return json.loads(json_text)
        else:
            print("❌ No JSON block found in markdown.")
            return {}
    except Exception as e:
        print(f"❌ Error parsing JSON from markdown: {e}")
        return {}


@CrewBase
class ResumeReaderCrew():

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def recruiter_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['recruiter_agent'],
            llm=llm
        )

    @task
    def report_task(self) -> Task:
        return Task(
            config=self.tasks_config['report_task'],
            llm=llm,
        )

    @crew
    def Crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=[
                self.report_task()
            ],
        )

    def kickoff_batch(self, resume_dir: str, jd_text: str, batch_id: int):
        print(f"🔄 Extracting resumes for Batch {batch_id}...")

        # ✅ Get both resume texts and warnings
        resume_texts, warnings_list = extract_text_from_pdf_parallel(resume_dir)

        print(f"🚀 Running Crew AI for Batch {batch_id}...")
        crew = self.Crew()

        result = crew.kickoff(inputs={
            "resume_text": resume_texts,
            "jd_text": jd_text
        })

        markdown = result.raw if hasattr(result, "raw") else ""

        #  Raw markdown for inspection
        with open(f"batch_{batch_id}_markdown.txt", "w", encoding="utf-8") as f:
            f.write(markdown)

        #  Extract JSON from markdown
        result_data = extract_json_from_markdown(markdown)

        if result_data:
            result_data["warnings"] = warnings_list  #  Include warnings in JSON

            with open(os.path.join(BATCH_RESULT_FOLDER, f"batch_{batch_id}.json"), "w", encoding="utf-8") as f:
                json.dump(result_data, f, indent=2)

            print(f"✅ Batch {batch_id} JSON saved with {len(result_data.get('candidates', []))} candidates.")
        else:
            print(f"⚠ Batch {batch_id} JSON extraction failed.")

        if warnings_list:
            print(f"⚠ Warnings for Batch {batch_id}: {warnings_list}")

        return result_data

    def parse_markdown_table(self, markdown: str):
        """
        Parse the markdown ranking table into a list of candidates.
        """
        lines = markdown.splitlines()

        table_started = False
        candidates = []

        for line in lines:
            if line.strip().startswith("| Rank") and not table_started:
                table_started = True
                continue

            if table_started:
                if line.strip().startswith("|----"):  # skip the header separator
                    continue

                if not line.strip().startswith("|") or line.strip() == "":
                    break  # End of table

                parts = [part.strip() for part in line.strip().split("|")[1:-1]]

                if len(parts) >= 8:
                    candidate = {
                        "rank": parts[0],
                        "name": parts[1],
                        "score": float(parts[2]) if parts[2] else 0.0,
                        "fit_indicator": parts[3],
                        "top_strength": parts[4],
                        "primary_gap": parts[5],
                        "email": parts[6],
                    }
                    candidates.append(candidate)

        return candidates
    # All batches result combined
    def load_all_batches(self):
        results = []
        for filename in sorted(os.listdir(BATCH_RESULT_FOLDER)):
            if filename.endswith(".json"):
                with open(os.path.join(BATCH_RESULT_FOLDER, filename), "r") as f:
                    results.append(json.load(f))
        return results
    
    # To clear data
    def clear_all_batches(self):
        for filename in os.listdir(BATCH_RESULT_FOLDER):
            file_path = os.path.join(BATCH_RESULT_FOLDER, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)