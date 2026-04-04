#!/usr/bin/env python

from content_hub.interfaces.compat.legacy_runner import run_legacy_workflow


def run(inputs):
    return run_legacy_workflow(inputs)


def ai_write_x_run(config_data=None):
    return True, run(config_data or {"topic": "AIWriteX 内容中站任务"})


def ai_write_x_main(config_data=None):
    return ai_write_x_run(config_data=config_data)


if __name__ == "__main__":
    ai_write_x_main()
