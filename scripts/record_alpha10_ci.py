"""Pin completed GitHub jobs and actual test logs to an expected source commit."""
import argparse
import json
from pathlib import Path
import re
import subprocess

from nirs4all_domains.storage import atomic_json, digest


def gh(*arguments):
    return subprocess.check_output(["gh", *arguments], text=True, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--out", type=Path, default=Path("docs/audit/github-ci-alpha10.json"))
    args = parser.parse_args()
    info = json.loads(gh("run", "view", args.run_id, "--repo", "dcornet/nirs4all-domains",
                         "--json", "headSha,status,conclusion,jobs,url,createdAt,updatedAt"))
    if info["headSha"] != args.expected_sha or info["status"] != "completed" or info["conclusion"] != "success":
        raise ValueError("EXPECTED_SOURCE_CI_NOT_COMPLETED_SUCCESSFULLY")
    if {j["name"] for j in info["jobs"]} != {"audit (ubuntu-latest)", "audit (windows-latest)"}:
        raise ValueError("BOTH_PLATFORM_JOBS_REQUIRED")
    for job in info["jobs"]:
        if job["status"] != "completed" or job["conclusion"] != "success":
            raise ValueError("PLATFORM_JOB_NOT_COMPLETED_SUCCESSFULLY")
        log = gh("run", "view", args.run_id, "--repo", "dcornet/nirs4all-domains", "--job", str(job["databaseId"]), "--log")
        path = Path(".audit/alpha10")/(args.run_id+"-"+str(job["databaseId"])+".log")
        path.write_text(log, encoding="utf-8")
        matches = re.findall(r"Ran (\d+) tests in ([\d.]+)s", log)
        if not matches or any(int(n) != 117 for n, _ in matches):
            raise ValueError("ACTUAL_117_TEST_LOG_REQUIRED")
        job.update(actual_python_test_runs=[{"count": int(n), "seconds": float(s)} for n, s in matches], log_sha256=digest(path))
    atomic_json(args.out, {"repository": "dcornet/nirs4all-domains", "run_id": int(args.run_id), **info,
        "proof": "Completed platform jobs/steps and actual native/117-test logs; no raw real-data acquisition in CI"})
    print(json.dumps({"headSha": info["headSha"], "status": info["conclusion"], "jobs": [j["name"] for j in info["jobs"]]}))


if __name__ == "__main__": main()
