"""
This script iterates through the tasks in the WorkArena
benchmark and uses the cheat functions to solve them.

The purpose of this demo is:
1.) to showcase the type of tasks in the WorkArena benchmark
2.) to demostrate how an AI agent should interact with the software
    to be considered as having "solved" the task.
3.) to show how we could use this benchmark to evaluate our own AI agents
    for our own adaptive onboarding system.
"""

import random

from browsergym.core.env import BrowserEnv
from browsergym.workarena import ATOMIC_TASKS
from time import sleep


random.shuffle(ATOMIC_TASKS)
for task in ATOMIC_TASKS:
    print("Task:", task)

    # Instantiate a new environment
    env = BrowserEnv(task_entrypoint=task,
                    headless=False)
    env.reset()


    # Cheat functions use Playwright to automatically solve the task
    env.chat.add_message(role="assistant", msg="On it. Please wait...")
    """
    Here is where an AI agent would interact with the software to solve the task.
    Currently, we use the cheat function.
    However, in testing/benchmarking/comparing our own AI agent, we would replace this 
    with calls to our OWN agent or the model that the creators actually used.

    GPT-4o was the best performer at 43% success rate on WorkArena
    """
    cheat_messages = []
    env.task.cheat(env.page, cheat_messages)

    # Send cheat messages to chat
    for cheat_msg in cheat_messages:
        env.chat.add_message(role=cheat_msg["role"], msg=cheat_msg["message"])

    # Post solution to chat
    env.chat.add_message(role="assistant", msg="I'm done!")

    # Validate the solution
    reward, stop, message, info = env.task.validate(env.page, cheat_messages)
    if reward == 1:
        env.chat.add_message(role="user", msg="Yes, that works. Thanks!")
    else:
        env.chat.add_message(role="user", msg=f"No, that doesn't work. {info.get('message', '')}")

    sleep(3)
    env.close()