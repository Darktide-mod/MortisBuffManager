"""Run this project's checks; never build another release."""
from pathlib import Path
import os, subprocess, sys
TESTS=Path(__file__).resolve().parent
PROJECT=TESTS.parent
CHECKS=PROJECT/'build/checks'
CHECKS.mkdir(parents=True,exist_ok=True)
environment=dict(os.environ, PYTHONIOENCODING='utf-8')
with (CHECKS/'tests.log').open('w',encoding='utf-8') as log:
    for case in ['syntax_tests.py', 'filesystem_ffi_tests.py', 'diy_minion_lifecycle_tests.py', 'workspace_tests.py', 'workspace_layering_tests.py', 'workspace_lifecycle_tests.py', 'workspace_native_tests.py', 'settings_tests.py', 'deployment_tests.py', 'ui_resource_tests.py', 'draft_tests.py', 'native_route_tests.py', 'diy_eligibility_tests.py', 'runtime_tests.py', 'performance_tests.py', 'competition_performance_tests.py', 'diy_capture_performance_tests.py', 'numeric_ui_tests.py', 'draft_input_tests.py', 'feature_ui_tests.py', 'diy_reward_controls_tests.py', 'realms_loading_tests.py', 'dual_controls_tests.py', 'host_policy_current_tests.py', 'preselection_model_tests.py', 'catalog_ui_tests.py', 'ranged_salvo_tests.py']:
        print(PROJECT.name + ': ' + case, flush=True)
        result=subprocess.run([sys.executable,str(TESTS/case)],cwd=PROJECT,
            text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=environment)
        log.write(case+'\n'+result.stdout+'\n'); log.flush()
        print(result.stdout, end='', flush=True)
        if result.returncode: sys.exit(result.returncode)
print(PROJECT.name + ': all project checks passed.')
