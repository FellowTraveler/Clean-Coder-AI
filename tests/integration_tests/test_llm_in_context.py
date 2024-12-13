"""Integration tests for running single coder pipeline with no documentation context added."""

import logging
import os
import pathlib
import subprocess

import pytest

from single_task_coder import run_clean_coder_pipeline, set_up_dot_clean_coder_dir

logger = logging.getLogger()
logger.level = logging.INFO


@pytest.mark.integration
def test_llm_no_context(tmp_path: pathlib.Path) -> None:
    """Test that the LLM hallucinates and produces incorrect import statement without documentation context."""
    # Given the task for the LLM
    task = '''populate main_dummy.py with code to pull information with PubMedAPIWrapper from langchain,
        to load results to the query "cancer research". Use API key "123412367"'''
    # and given a test work directory as well as .py file
    work_dir = tmp_path / "trial"
    py_file = work_dir / "main_dummy.py"
    content = 'print("hello world")'
    py_file.write_text(content, encoding="utf-8")
    work_dir.mkdir()
    os.environ["WORK_DIR"] = str(work_dir)
    # When starting single coder pipeline and making the LLM call
    set_up_dot_clean_coder_dir(work_dir)
    run_clean_coder_pipeline(task, str(work_dir))
    # Then assert that main_dummy.py was modified by the agents
    assert py_file.read_text(encoding="utf-8") != content
    # Then assert that the response is not runnable
    command = ["python", py_file]
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.run(command, check=True)
    assert excinfo.value.returncode != 0


def test_llm_rag_context(tmp_path: pathlib.Path, doc_rag=None) -> None:
    """Test that an LLM with RAG documentation makes a correct implementation of what is requested."""
    # Given initial request for the LLM
    task = '''populate main_dummy.py with code to pull information with PubMedAPIWrapper from langchain,
        to load results to the query "cancer research". Use API key "123412367"'''
    # and given a test work directory as well as .py file
    work_dir = tmp_path / "trial"
    py_file = work_dir / "main_dummy.py"
    content = 'print("hello world")'
    py_file.write_text(content, encoding="utf-8")
    work_dir.mkdir()
    os.environ["WORK_DIR"] = str(work_dir)
    # When starting single coder pipeline and making the LLM call, with RAG
    set_up_dot_clean_coder_dir(work_dir)
    run_clean_coder_pipeline(task, str(work_dir), docrag="on")
    # Then assert that main_dummy.py was modified by the agents
    assert py_file.read_text(encoding="utf-8") != content
    # Then assert that the response is not runnable
    command = ["python", py_file]
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        subprocess.run(command, check=True)
    assert excinfo.value.returncode == 0
