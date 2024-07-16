# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

env_config = []

if not os.environ.get("port") is None:
    env_config +=["--port", os.environ["port"]]
    
if not os.environ.get("AGENT_NAME") is None:
    env_config +=["--agent_name", os.environ["AGENT_NAME"]]

if not os.environ.get("strategy") is None:
    env_config += ["--strategy", os.environ["strategy"]]

if not os.environ.get("llm_endpoint_url") is None:
    env_config += ["--llm_endpoint_url", os.environ["llm_endpoint_url"]]

if not os.environ.get("llm_engine") is None:
    env_config += ["--llm_engine", os.environ["llm_engine"]]

if not os.environ.get("model") is None:
    env_config += ["--model", os.environ["model"]]

if not os.environ.get("recursion_limit") is None:
    env_config += ["--recursion_limit", os.environ["recursion_limit"]]

if not os.environ.get("require_human_feedback") is None:
    if os.environ["require_human_feedback"].lower() == "true":
        env_config += ["--require_human_feedback"]
        
if not os.environ.get("debug") is None:
    if os.environ["debug"].lower() == "true":
        env_config += ["--debug"]

if not os.environ.get("role_description") is None:
    env_config += ["--role_description", "'"+os.environ["role_description"]+"'"]

if not os.environ.get("tools") is None:
    env_config += ["--tools", os.environ["tools"]]