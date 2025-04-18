if __name__ == "__main__":
    from src.utilities.start_work_functions import print_ascii_logo
    print_ascii_logo()
from dotenv import find_dotenv
from src.utilities.set_up_dotenv import set_up_env_coder_pipeline

if not find_dotenv():
    set_up_env_coder_pipeline()

from concurrent.futures import ThreadPoolExecutor
import os
from src.agents.researcher_agent import Researcher
from src.agents.doc_harvester import Doc_harvester
from src.agents.planner_agent import planning
from src.agents.executor_agent import Executor
from src.agents.debugger_agent import Debugger
from src.agents.frontend_feedback import write_screenshot_codes
from src.utilities.user_input import user_input
from src.utilities.start_project_functions import set_up_dot_clean_coder_dir
from src.utilities.util_functions import create_frontend_feedback_story
from src.tools.rag.rag_utils import update_descriptions
from src.tools.rag.index_file_descriptions import prompt_index_project_files, upsert_file_list, write_file_descriptions, write_file_chunks_descriptions
from src.tools.rag.retrieval import vdb_available
from src.linters.static_analisys import python_static_analysis


use_frontend_feedback = bool(os.getenv("FRONTEND_URL"))


def run_clean_coder_pipeline(task: str, work_dir: str, doc_harvest: bool = False):
    researcher = Researcher(work_dir)
    files, image_paths = researcher.research_task(task)
    # documentation = None
    # if doc_harvest:
    #     harvester = Doc_harvester()
    #     documentation = harvester.find_documentation(task, work_dir)

    plan = planning(task, files, image_paths, work_dir) #, documentation=documentation)

    executor = Executor(files, work_dir)

    playwright_codes = None
    if use_frontend_feedback:
        create_frontend_feedback_story()
        with ThreadPoolExecutor() as executor_thread:
            future = executor_thread.submit(write_screenshot_codes, task, plan, work_dir)
            files = executor.do_task(task, plan)
            playwright_codes = future.result()
    else:
        files = executor.do_task(task, plan)

    # static analysis
    files_to_check = [file for file in files if file.filename.endswith(".py") and file.is_modified]
    analysis_result = python_static_analysis(files_to_check)
    if analysis_result:
        # Automatically proceed to debugger with static analysis results
        human_message = analysis_result
    else:
        # No static analysis issues - ask for user input
        human_message = user_input("Please test app and provide commentary if debugging/additional refinement is needed. ")
        if human_message in ["o", "ok"]:
            update_descriptions([file for file in files if file.is_modified])
            return

    debugger = Debugger(files, work_dir, human_message, image_paths, playwright_codes)
    files = debugger.do_task(task, plan)
    update_descriptions([file for file in files if file.is_modified])



if __name__ == "__main__":
    work_dir = os.getenv("WORK_DIR")
    if not work_dir:
        raise Exception("WORK_DIR variable is not provided. Please add WORK_DIR to .env file")
    set_up_dot_clean_coder_dir(work_dir)
    prompt_index_project_files()
    task = user_input("Provide task to be executed. ")
    run_clean_coder_pipeline(task, work_dir)
